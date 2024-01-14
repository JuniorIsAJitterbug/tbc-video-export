from __future__ import annotations

import asyncio
import logging
import os
import queue
from dataclasses import dataclass
from enum import Flag, auto
from functools import cached_property
from typing import TYPE_CHECKING

from tbc_video_export.common import consts, exceptions
from tbc_video_export.common.enums import PipeType
from tbc_video_export.common.utils import strings
from tbc_video_export.process.wrapper.pipe.pipe import Pipe

if TYPE_CHECKING:
    from pathlib import Path
    from types import TracebackType


assert os.name == "nt"

import pywintypes  # noqa: E402
import win32event  # noqa: E402
import win32file  # noqa: E402
import win32pipe  # noqa: E402
import win32security  # noqa: E402
import winerror  # noqa: E402

from tbc_video_export.common.utils import win32  # noqa: E402


class PipeNamedNTAsync(Pipe):
    """Named pipe helper for NT systems.

    This uses asynchronous I/O compared to PipedNamedNT. We do not have
    to make a thread for every blocking win32 function.

    This is currently unused and is being tested for performance and
    stability.

    I hate Windows named pipes.
    """

    def __init__(self) -> None:
        self._id = strings.random_characters(7)
        self._pipe_name = rf"\\.\pipe\{consts.APPLICATION_NAME}-{self._id}"
        self.pipe_bridge = AsyncNamedPipeBridge(
            AsyncNamedPipeBridgeConfig(self._pipe_name)
        )
        self._bridge_thread: asyncio.Future[None] | None = None

    async def __aenter__(self) -> Pipe:
        """Enter async NT pipe context."""
        self._bridge_thread = asyncio.get_event_loop().run_in_executor(
            None, self.pipe_bridge.run
        )

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None | bool:
        """Exit async NT pipe context."""
        self.close()

    @cached_property
    def pipe_type(self) -> PipeType:  # noqa: D102
        return PipeType.NULL

    @cached_property
    def in_path(self) -> Path | str:  # noqa: D102
        return self._pipe_name

    @cached_property
    def out_path(self) -> Path | str:  # noqa: D102
        return self._pipe_name

    @property
    def in_handle(self) -> int | None:  # noqa: D102
        return None

    @property
    def out_handle(self) -> int | None:  # noqa: D102
        return None

    def close(self) -> None:  # noqa: D102
        self.pipe_bridge.disconnect_all()


class PipeState(Flag):
    """The current named pipe state."""

    NONE = auto()
    CONNECTING = auto()
    READING = auto()
    WRITING = auto()
    WRITE_TO_PEERS = auto()
    PENDING = auto()


class PipeInstance:
    """Represents a named pipe."""

    def __init__(
        self,
        pipe_id: int,
        handle: int,
        pipe_buffer_size: int = 4 * 1024 * 1024,  # 4MB
    ) -> None:
        self.pipe_id = pipe_id
        self.handle = handle
        self.buffer = win32file.AllocateReadBuffer(pipe_buffer_size)
        self.state = PipeState.NONE

        self.ol = win32file.OVERLAPPED()
        self.ol.hEvent = win32event.CreateEvent(
            win32security.SECURITY_ATTRIBUTES(), True, True, None
        )
        self.ol.Offset = 0
        self.ol.OffsetHigh = 0

        self.pending_write_size: int = -1

        self.current_read_size = 0
        self.read_data: memoryview | None = None
        self.write_queue: queue.Queue[memoryview] = queue.Queue()

    def log(self, message: str) -> None:
        """Log string with pipe details prefixed."""
        logging.getLogger("console").debug(f"[{self.pipe_id}][{self.state}] {message}")


@dataclass
class AsyncNamedPipeBridgeConfig:
    """Container for async pipe bridge config."""

    pipe_name: str
    peer_count: int = 2
    minimum_peers: int = 2
    pipe_timeout: int = 10000
    event_timeout: int = 100
    pipe_buffer_size: int = 65536  # advisory, doesn't really matter
    stop_on_disconnect: bool = True


class AsyncNamedPipeBridge:
    """Handle bridging between named pipes.

    Allows N pipes to connect to a pipe and acts as an echo server between them.
    While this is only used to go from A->B, A<->N is also possible.
    """

    def __init__(self, config: AsyncNamedPipeBridgeConfig) -> None:
        self.pipes: list[PipeInstance] = []
        self._pipe_name = config.pipe_name
        self._peer_count = config.peer_count
        self._minimum_peers = config.minimum_peers
        self._pipe_timeout = config.pipe_timeout
        self._event_timeout = config.event_timeout
        self._pipe_buffer_size = config.pipe_buffer_size
        self._stop_on_disconnect = config.stop_on_disconnect

        self._stop_queued = False

        for pipe_id in range(self._peer_count):
            self.pipes.append(self._create(pipe_id))

    def _create(self, pipe_id: int) -> PipeInstance:
        """Create the pipe instance."""
        try:
            handle = win32pipe.CreateNamedPipe(  # pyright: ignore [reportUnknownMemberType]
                self._pipe_name,
                win32pipe.PIPE_ACCESS_DUPLEX | win32file.FILE_FLAG_OVERLAPPED,
                win32pipe.PIPE_READMODE_BYTE
                | win32pipe.PIPE_TYPE_BYTE
                | win32pipe.PIPE_WAIT,
                self._peer_count,
                self._pipe_buffer_size,
                self._pipe_buffer_size,
                self._pipe_timeout,
                win32security.SECURITY_ATTRIBUTES(),
            )
        except pywintypes.error:
            match win32.GetLastError():
                case winerror.ERROR_BAD_NETPATH:
                    raise exceptions.PipeNTError(
                        f"Invalid pipe path {self._pipe_name}"
                    ) from None
                case _ as e:
                    raise exceptions.PipeNTError(
                        f"Create pipe failed with: {e}"
                    ) from None
        else:
            if handle == win32file.INVALID_HANDLE_VALUE:
                raise exceptions.PipeNTError(
                    f"Create pipe failed with {win32.GetLastError()}"
                )

            # create the pipe instance
            pipe = PipeInstance(pipe_id, handle)
            self._connect(pipe)

            return pipe

    def _connect(self, pipe: PipeInstance) -> None:
        """Connect a pipe instance."""
        result = win32pipe.ConnectNamedPipe(pipe.handle, pipe.ol)  # pyright: ignore [reportUnknownMemberType, reportUnknownVariableType]
        if isinstance(result, int):
            self._handle_connect_ret(pipe, result)
        else:
            # this should never reach, we're only checking for type checker
            raise exceptions.PipeNTError(f"ConnectNamedPipe returned {result}")

    def _disconnect(self, pipe: PipeInstance, close_handle: bool = False) -> None:
        """Disconnect a pipe instance."""
        try:
            pipe.log("Disconnecting")
            win32pipe.DisconnectNamedPipe(pipe.handle)
        except pywintypes.error:
            self._handle_disconnect_ret(pipe)

        if close_handle:
            try:
                win32file.CloseHandle(pipe.handle)
            except pywintypes.error:
                self._handle_disconnect_ret(pipe)

    def disconnect_all(self) -> None:
        """Disconnect all pipe instances."""
        for pipe in (pipe for pipe in self.pipes):
            self._disconnect(pipe, True)

    def _handle_connection(self, pipe: PipeInstance):
        """Handle new/re-connection."""
        try:
            # get connect result
            ol_result = win32file.GetOverlappedResult(pipe.handle, pipe.ol, False)

            return self._handle_connect_ret(pipe, ol_result)
        except pywintypes.error:
            return self._handle_connect_ret(pipe, win32.GetLastError())

    @staticmethod
    def _handle_connect_ret(pipe: PipeInstance, ret: int) -> bool:
        """Handle connection return."""
        match ret:
            case winerror.ERROR_SUCCESS:
                pipe.log("Connection successful")

                # set the pipe state based on whether the queue already contains data
                pipe.state = (
                    PipeState.WRITING
                    if not pipe.write_queue.empty()
                    else PipeState.READING  # pyright: ignore [reportUnknownMemberType, reportUnknownArgumentType]
                )

                return True

            # The overlapped connection in progress.
            case winerror.ERROR_IO_PENDING:
                pipe.log("Connection pending")
                pipe.state = PipeState.CONNECTING

            # Client is already connected, so signal an event.
            # There is a process on other end of the pipe.
            case winerror.ERROR_PIPE_CONNECTED:
                pipe.log("Pipe already connected")
                pipe.state = PipeState.CONNECTING
                win32event.SetEvent(pipe.ol.hEvent)

            # Overlapped I/O event is not in a signaled state.
            case winerror.ERROR_IO_INCOMPLETE:
                pipe.log("Overlapped I/O event is not in a signaled state.")

            case _ as e:
                raise exceptions.PipeNTError(f"Connect failed with: {e}")

        return False

    def _handle_disconnect(self, pipe: PipeInstance) -> None:
        """Handle disconnects."""
        try:
            if self._stop_on_disconnect:
                pipe.log("Stop on disconnect set")
                self._stop_queued = True

            self._disconnect(pipe, self._stop_queued)

            if not self._stop_queued:
                self._connect(pipe)
        except pywintypes.error as e:
            pipe.log(f"Failed to disconnect {e}")

    @staticmethod
    def _handle_disconnect_ret(pipe: PipeInstance) -> None:
        """Handle disconnect return."""
        match win32.GetLastError():
            case winerror.ERROR_PIPE_NOT_CONNECTED:
                pipe.log("Attempted to disconnect disconnected pipe")

            case winerror.ERROR_INVALID_HANDLE:
                pipe.log("Attempted to close invalid handle")

            case _ as e:
                pipe.log(f"Disconnect error: {e}")
                raise SystemExit

    def _handle_read(self, pipe: PipeInstance) -> None:
        """Handle reads."""
        try:
            result, _ = win32file.ReadFile(pipe.handle, pipe.buffer, pipe.ol)
            self._handle_read_ret(pipe, result)
        except pywintypes.error:
            self._handle_read_ret(pipe, win32.GetLastError())

    def _handle_read_pending(self, pipe: PipeInstance) -> None:
        """Handle pending reads.."""
        try:
            self._handle_read_ol_ret(pipe)

            # remove pending flag
            pipe.state &= ~PipeState.PENDING
        except pywintypes.error:
            self._handle_read_ret(pipe, win32.GetLastError())

    def _handle_read_ol_ret(self, pipe: PipeInstance) -> None:
        """Handle read result.."""
        try:
            # get result
            ol_result = win32file.GetOverlappedResult(pipe.handle, pipe.ol, False)

            # this shouldn't happen
            if ol_result == 0:
                pipe.log("Read {ol_result} bytes, expected > 0")
                self._handle_disconnect(pipe)

            # keep track of current read size for memoryview splicing
            pipe.current_read_size += ol_result

            if pipe.read_data is None:
                pipe.read_data = pipe.buffer[:ol_result]  # pyright: ignore [reportGeneralTypeIssues]
            else:
                pipe.read_data[pipe.current_read_size :] = pipe.buffer[:ol_result]  # pyright: ignore [reportGeneralTypeIssues, reportUnknownArgumentType]

            # copy data to all connected peers
            for peer in (
                peer
                for peer in self.pipes
                if peer.state is not PipeState.CONNECTING
                and peer.pipe_id != pipe.pipe_id
            ):
                # add read data to other pipe instance write queue
                if isinstance(pipe.read_data, memoryview):  # pyright: ignore [reportUnknownMemberType]
                    peer.write_queue.put_nowait(pipe.read_data)
                    peer.pending_write_size = ol_result
                    peer.state = PipeState.WRITING

            # prep pipe for writing to peers
            pipe.current_read_size = 0
            pipe.read_data = None
            pipe.state = PipeState.WRITE_TO_PEERS
        except pywintypes.error:
            self._handle_read_ret(pipe, win32.GetLastError())
        except queue.Full as e:
            # queue should never be full as we prioritise writes
            # something is broke if we reach here
            raise exceptions.PipeNTError("Write queue full.") from e

    def _handle_read_ret(self, pipe: PipeInstance, ret: int) -> None:
        """Handle read returns."""
        match ret:
            case winerror.ERROR_SUCCESS:
                self._handle_read_ol_ret(pipe)

            # More data is available.
            case winerror.ERROR_MORE_DATA:
                bytes_read = len(pipe.buffer)  # pyright: ignore [reportGeneralTypeIssues]

                # keep track of current read size for memoryview splicing
                pipe.current_read_size += bytes_read

                if pipe.read_data is None:
                    pipe.read_data = pipe.buffer[:bytes_read]  # pyright: ignore [reportGeneralTypeIssues]
                else:
                    pipe.read_data[pipe.current_read_size :] = pipe.buffer[:bytes_read]  # pyright: ignore [reportGeneralTypeIssues, reportUnknownArgumentType]

                # set pending and read more
                pipe.state |= PipeState.PENDING
                win32file.ReadFile(pipe.handle, pipe.buffer, pipe.ol)

            case winerror.ERROR_IO_PENDING:
                pipe.state |= PipeState.PENDING

            case _:
                self._handle_ret(pipe, ret)

    def _handle_write(self, pipe: PipeInstance) -> None:
        """Handle writes."""
        try:
            data = pipe.write_queue.get()

            result, bytes_written = win32file.WriteFile(
                pipe.handle,
                data,  # pyright: ignore [reportGeneralTypeIssues]
                pipe.ol,
            )

            # confirm we wrote the correct amount of data
            self._handle_write_ret(
                pipe, result, bytes_written == pipe.pending_write_size
            )
        except pywintypes.error:
            self._handle_write_ret(pipe, win32.GetLastError(), False)

    def _handle_write_pending(self, pipe: PipeInstance) -> None:
        """Handle pending writes.."""
        try:
            self._handle_write_ol_ret(pipe)
        except pywintypes.error:
            self._handle_write_ret(pipe, win32.GetLastError(), False)

    @staticmethod
    def _handle_write_ol_ret(pipe: PipeInstance) -> None:
        """Handle write result."""
        # get result
        ol_result = win32file.GetOverlappedResult(pipe.handle, pipe.ol, False)

        # we wrote the correct amount of data, set pipe state to reading
        if ol_result == pipe.pending_write_size:
            pipe.state = PipeState.READING
            return

    def _handle_write_ret(
        self,
        pipe: PipeInstance,
        ret: int,
        success_condition: bool,
    ) -> None:
        """Handle write return."""
        match ret:
            case winerror.ERROR_SUCCESS:
                if success_condition:
                    pipe.state = PipeState.READING

            case winerror.ERROR_IO_PENDING:
                pipe.state |= PipeState.PENDING

            case _:
                self._handle_ret(pipe, ret)

    def _handle_writepeer(self, pipe: PipeInstance) -> None:
        """Handle writing to peers."""
        try:
            # write to all connected pipes excluding sender
            for peer in (
                peer
                for peer in self.pipes
                if peer.state is not PipeState.CONNECTING
                and peer.pipe_id != pipe.pipe_id
            ):
                self._handle_write(peer)

            pipe.state = PipeState.READING

        except pywintypes.error:
            self._handle_write_ret(pipe, win32.GetLastError(), False)

    def _handle_ret(self, pipe: PipeInstance, ret: int) -> None:
        """Handle general returns."""
        match ret:
            case (
                # The pipe has been ended.
                winerror.ERROR_BROKEN_PIPE
                # The pipe is being closed.
                | winerror.ERROR_NO_DATA
                # No process is on the other end of the pipe.
                | winerror.ERROR_PIPE_NOT_CONNECTED
            ):
                self._handle_disconnect(pipe)

            # Waiting for a process to open the other end of the pipe.
            case winerror.ERROR_PIPE_LISTENING:
                pass

            case (
                # The pipe state is invalid
                winerror.ERROR_BAD_PIPE
                # All pipe instances are busy.
                | winerror.ERROR_PIPE_BUSY
                # Overlapped I/O event is not in a signaled state.
                | winerror.ERROR_IO_INCOMPLETE
            ):
                raise exceptions.PipeNTError(f"[{pipe.pipe_id}] Pipe in invalid state.")

            case _ as e:
                raise exceptions.PipeNTError(
                    f"[{pipe.pipe_id}] An unknown error occured: {e}"
                )

    def _process(self, pipe: PipeInstance) -> None:
        """Process data based on pipe state."""
        match pipe.state:
            case PipeState.CONNECTING:
                if not self._handle_connection(pipe):
                    return

            # Pending read handler
            case _ as state if PipeState.READING | PipeState.PENDING in state:
                self._handle_read_pending(pipe)

            case _ as state if PipeState.WRITING | PipeState.PENDING in state:
                self._handle_write_pending(pipe)

            case PipeState.READING:
                self._handle_read(pipe)

            case PipeState.WRITING:
                self._handle_write(pipe)

            case PipeState.WRITE_TO_PEERS:
                self._handle_writepeer(pipe)
            case _:
                pipe.log("Shouldn't be here")
                raise exceptions.PipeNTError(
                    f"[{pipe.pipe_id}] An unknown error occured."
                )

    def run(self):
        """Run the pipe bridge."""
        while True:
            connected_peer_count = sum(
                1 for pipe in self.pipes if pipe.state is not PipeState.CONNECTING
            )

            pending_writers = [
                pipe
                for pipe in self.pipes
                if pipe.state is PipeState.WRITING | PipeState.PENDING
            ]

            # if only 1 peer, only listen for events from unconnected peers
            if connected_peer_count < self._minimum_peers:
                pipe_events = [
                    pipe for pipe in self.pipes if pipe.state is PipeState.CONNECTING
                ]
            elif count := len(pending_writers):
                # If there are pipes with pending writes, only process them
                pipe_events = [
                    pipe
                    for pipe in self.pipes
                    if pipe.state is PipeState.WRITING | PipeState.PENDING
                ]
            else:
                # Multiple peers
                pipe_events = self.pipes

            wait_idx = -1

            try:
                wait_idx = win32event.WaitForMultipleObjects(  # pyright: ignore [reportUnknownMemberType, reportUnknownVariableType]
                    [pipe.ol.hEvent for pipe in pipe_events], False, self._event_timeout
                )
            except pywintypes.error:
                match win32.GetLastError():
                    case winerror.ERROR_INVALID_PARAMETER:
                        continue

                    case _ as e:
                        logging.getLogger("console").debug(f"Unknown events error {e}")
                        return

            assert isinstance(wait_idx, int)

            if wait_idx == winerror.WAIT_TIMEOUT:
                continue

            wait_idx -= win32event.WAIT_OBJECT_0
            pipe = pipe_events[wait_idx]

            if self._stop_queued:
                logging.getLogger("console").debug(
                    "Stop queued, checking remaining pipes"
                )
                if (
                    count := sum(1 for p in self.pipes if not p.write_queue.empty())
                ) == 0:
                    logging.getLogger("console").debug(
                        "Remaining pipes are all empty, disconnecting"
                    )
                    self.disconnect_all()
                    return

                logging.getLogger("console").debug(
                    f"Waiting for {count} pipes to finish writing"
                )

            self._process(pipe)
