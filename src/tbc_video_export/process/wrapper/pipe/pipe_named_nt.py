from __future__ import annotations

import asyncio
import logging
import os
from contextlib import suppress
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING

from tbc_video_export.common import consts, exceptions
from tbc_video_export.common.enums import PipeType
from tbc_video_export.common.utils import strings
from tbc_video_export.process.wrapper.pipe.pipe import Pipe

if TYPE_CHECKING:
    from pathlib import Path
    from types import TracebackType

    from tbc_video_export.common.enums import ProcessName, TBCType

assert os.name == "nt"

import pywintypes  # noqa: E402
import win32file  # noqa: E402
import win32pipe  # noqa: E402
import win32security  # noqa: E402
import winerror  # noqa: E402

from tbc_video_export.common.utils import win32  # noqa: E402


class PipeNamedNT(Pipe):
    """Named pipe helper for NT systems.

    This uses synchronous I/O, because of this most win32 calls are
    blocking and must run in their own thread. Not much error checking
    is done here.

    I hate Windows named pipes.
    """

    @dataclass
    class PipeData:
        """Storage class for pipe data."""

        pipe_name: str | Path
        open_mode: int | Path
        pipe_mode = (
            win32pipe.PIPE_TYPE_BYTE
            | win32pipe.PIPE_READMODE_BYTE
            | win32pipe.PIPE_WAIT
        )
        max_instances = consts.NT_NAMED_PIPE_MAX_INSTANCES
        out_buffer_size = consts.NT_NAMED_PIPE_BUFFER_SIZE
        in_buffer_size = consts.NT_NAMED_PIPE_BUFFER_SIZE
        time_out = consts.NT_NAMED_PIPE_TIMEOUT
        security_attributes = win32security.SECURITY_ATTRIBUTES()

        thread: asyncio.Future[None] | None = None
        file_handle: int | None = None
        ready_event = asyncio.Event()

    def __init__(self, process_name: ProcessName, tbc_type: TBCType) -> None:
        super().__init__(process_name, tbc_type)
        self._bridge_thread: asyncio.Task[None] | None = None
        self._start_bridge_task: asyncio.Future[None] | None = None

        self._id = strings.random_characters(7)

        self._pipe_data_stdin: PipeNamedNT.PipeData = PipeNamedNT.PipeData(
            self.in_path, win32pipe.PIPE_ACCESS_OUTBOUND
        )
        self._pipe_data_stdout: PipeNamedNT.PipeData = PipeNamedNT.PipeData(
            self.out_path, win32pipe.PIPE_ACCESS_INBOUND
        )

    async def __aenter__(self) -> Pipe:
        """Enter named NT pipe context."""
        # starts the pipe bridge thread
        self._start_bridge_task = asyncio.create_task(self._start_pipe_bridge())

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None | bool:
        """Exit named NT pipe context."""
        self.close()

    @cached_property
    def pipe_type(self) -> PipeType:  # noqa: D102
        return PipeType.NAMED_NT

    @cached_property
    def in_path(self) -> Path | str:  # noqa: D102
        return (
            rf"\\.\pipe\{consts.APPLICATION_NAME}-{self._id}-"
            rf"{self._process_name}-{self._tbc_type}-in"
        )

    @cached_property
    def out_path(self) -> Path | str:  # noqa: D102
        return (
            rf"\\.\pipe\{consts.APPLICATION_NAME}-{self._id}-"
            rf"{self._process_name}-{self._tbc_type}-out"
        )

    @property
    def in_handle(self) -> int | None:  # noqa: D102
        return None

    @property
    def out_handle(self) -> int | None:  # noqa: D102
        return None

    def close(self) -> None:
        """Close named pipe."""
        self._close_pipe(str(self.in_path), win32file.GENERIC_READ)
        self._close_pipe(str(self.out_path), win32file.GENERIC_WRITE)

    async def _start_pipe_bridge(self) -> None:
        """Start the pipe bridge.

        This reads from one named pipe and writes into another.
        """
        loop = asyncio.get_event_loop()

        # create pipes
        self._create_pipe(self._pipe_data_stdin)
        self._create_pipe(self._pipe_data_stdout)

        # connect to pipes
        # we run these in a thread as CreateNamedPipe is blocking
        self._pipe_data_stdin.thread = loop.run_in_executor(
            None, self._connect_pipe, self._pipe_data_stdin
        )
        self._pipe_data_stdout.thread = loop.run_in_executor(
            None, self._connect_pipe, self._pipe_data_stdout
        )

        await asyncio.gather(
            *[self._pipe_data_stdin.thread, self._pipe_data_stdout.thread]
        )

        loop.run_in_executor(None, self._pipe_bridge)

    def _pipe_bridge(self) -> None:
        """Pipe bridge thread.

        This is started once the pipes have been created and connected, and the pipe
        handles exist.
        """
        logging.getLogger("console").debug(
            f"Pipe bridge for {self._pipe_data_stdout.pipe_name} -> "
            f"{self._pipe_data_stdin.pipe_name} started"
        )

        if (
            self._pipe_data_stdin.file_handle is None
            or self._pipe_data_stdout.file_handle is None
        ):
            raise exceptions.PipeError("Pipe handles do not exist.")

        try:
            while True:
                # read data from stdout pipe
                read_hr, read_buf = win32file.ReadFile(
                    self._pipe_data_stdout.file_handle,
                    consts.NT_NAMED_PIPE_BUFFER_SIZE,
                )

                if read_hr != winerror.ERROR_SUCCESS:
                    self._handle_winerror(read_hr)

                # write data to stdin pipe
                write_hr, written_count = win32file.WriteFile(
                    self._pipe_data_stdin.file_handle, read_buf
                )

                if write_hr != winerror.ERROR_SUCCESS:
                    self._handle_winerror(write_hr)

                if written_count != len(read_buf):
                    raise exceptions.PipeNTError("Failed to write all data.")
        except pywintypes.error:
            self._handle_winerror()
        finally:
            # we disconnect the pipes at the end of the loop instead of at __exit__,
            # else the stdin process will be stuck waiting for more data as the context
            # has not ended
            with suppress(pywintypes.error):
                self._disconnect_pipe(self._pipe_data_stdin)
                self._disconnect_pipe(self._pipe_data_stdout)

            logging.getLogger("console").debug(
                f"Pipe bridge for {self._pipe_data_stdout.pipe_name} to "
                f"{self._pipe_data_stdin.pipe_name} ended"
            )

    def _create_pipe(self, data: PipeNamedNT.PipeData) -> None:
        """Create named pipe."""
        try:
            pipe = win32pipe.CreateNamedPipe(  # pyright: ignore [reportUnknownMemberType]
                str(data.pipe_name),
                data.open_mode,
                data.pipe_mode,
                data.max_instances,
                data.out_buffer_size,
                data.in_buffer_size,
                data.time_out,
                data.security_attributes,
            )

            logging.getLogger("console").debug(f"Created pipe {data.pipe_name}")

            data.file_handle = pipe
        except pywintypes.error:
            self._handle_winerror()

    def _connect_pipe(self, data: PipeData) -> None:
        """Connect to named pipe.

        This is blocking and needs to run in it's own thread.
        """
        try:
            if data.file_handle is not None:
                logging.getLogger("console").debug(f"Connecting {data.pipe_name}")
                if win32pipe.ConnectNamedPipe(data.file_handle, None):  # pyright: ignore [reportUnknownMemberType]
                    self._handle_winerror()

                logging.getLogger("console").debug(f"Connected {data.pipe_name}")

        except pywintypes.error:
            self._handle_winerror()

    def _close_pipe(self, path: str, mode: int) -> None:
        """Close a pipe.

        Due to ConnectNamedPipe being blocking, we must force close the pipe by
        opening the pipe and closing it. This will cause a connection to the pipe
        and an instant disconnect.
        """
        logging.getLogger("console").debug(
            f"Closing pipe {self.in_path} -> {self.out_path}"
        )

        with suppress(pywintypes.error):
            file = win32file.CreateFile(
                path,
                mode,
                0,
                win32security.SECURITY_ATTRIBUTES(),
                win32file.OPEN_EXISTING,
                0,
                None,
            )

            win32file.CloseHandle(file.handle)

    @staticmethod
    def _disconnect_pipe(data: PipeData) -> None:
        """Disconnnect a pipe."""
        if data.file_handle is None:
            raise exceptions.PipeError("Pipe handle does not exist.")

        logging.getLogger("console").debug(f"Disconnecting {data.pipe_name}")
        win32pipe.DisconnectNamedPipe(data.file_handle)

    @staticmethod
    def _handle_winerror(ret: int | None = None) -> None:
        """Print windows related errors."""
        match ret or win32.GetLastError():
            case winerror.ERROR_BROKEN_PIPE:
                # The pipe has been ended.
                return

            case _ as e:
                raise exceptions.PipeNTError(
                    f"Windows Named Pipes failed with error {e}. "
                    "If this persists consider using --two-step as an alternative."
                )
