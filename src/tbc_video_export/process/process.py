from __future__ import annotations

import asyncio
import logging
import os
from contextlib import suppress
from typing import TYPE_CHECKING

from tbc_video_export.common import consts
from tbc_video_export.common.enums import FlagHelper, ProcessStatus
from tbc_video_export.common.utils import log
from tbc_video_export.process.parser import Parser, ParserFactory
from tbc_video_export.process.process_state import ProcessState
from tbc_video_export.process.wrapper.pipe.pipe_os import PipeOS

if TYPE_CHECKING:
    from typing import Any

    from tbc_video_export.process.wrapper import Wrapper
    from tbc_video_export.program_state import ProgramState as ProgramState


class Process:
    """Contains the subprocess, handler and state of a running process."""

    def __init__(
        self, state: ProgramState, stop_event: asyncio.Event, wrapper: Wrapper
    ) -> None:
        self._state = state
        self._stop_event = stop_event
        self.wrapper = wrapper

        self._process_state = ProcessState()
        self._process: asyncio.subprocess.Process | None = None
        self._tasks: set[asyncio.Task[Any]] = set()

        self._output_parser = ParserFactory.create(wrapper.process_name)

        self._logger_name = (
            f"{self.wrapper.process_name}_"
            f"{FlagHelper.get_flags_str(self.wrapper.tbc_type, '_')}"
        )

    async def run(self) -> ProcessState:
        """Run the process."""
        self.state.set_has_run()

        if self._state.opts.show_process_output or self._state.opts.log_process_output:
            # setup file logger
            log.setup_logger(
                self._logger_name,
                enable_console=self._state.opts.show_process_output,
                filename=str(
                    self._state.file_helper.get_log_file(
                        self.wrapper.process_name, self.wrapper.tbc_type
                    )
                )
                if self._state.opts.log_process_output and self.wrapper.log_output
                else None,
            )

        # create subprocess
        command = self.wrapper.command.data
        logging.getLogger("console").debug(f"Running: {command}")

        self._process = await asyncio.create_subprocess_exec(
            *command,
            limit=consts.PIPE_BUFFER_SIZE,
            stdin=self.wrapper.stdin,
            stdout=self.wrapper.stdout,
            stderr=self.wrapper.stderr,
            env=dict(os.environ) | self.wrapper.env
            if self.wrapper.env is not None
            else None,
        )

        # set the process output start event
        self._process_state.set_running()

        # create parse task
        self._tasks.add(asyncio.create_task(self._parse_process_output()))

        # wait for subprocess to finish
        await self._process.wait()

        if self._process.returncode is not None:
            self._process_state.returncode = self._process.returncode

        await asyncio.wait(self._tasks)

        # even though these will be handled by the ExitStack, we should
        # close os pipes now to prevent hanging procs (POSIX only?)
        for pipe in self.wrapper.pipes:
            if isinstance(pipe, PipeOS):
                pipe.close()

        self._process_state.set_stopped()
        self._set_proc_status()

        return self._process_state

    async def stop(self) -> None:
        """Kill the subprocess and set the process state."""
        logging.getLogger("console").debug(
            f"{self.wrapper.process_name} "
            f"({FlagHelper.get_flags_str(self.wrapper.tbc_type)}) Killing process"
        )

        if self._process is not None and not self._process_state.is_stopped:
            with suppress(ProcessLookupError):
                self._process.kill()
                await self._process.wait()

        await asyncio.wait(self._tasks)

        logging.getLogger("console").debug(
            f"{self.wrapper.process_name} "
            f"({FlagHelper.get_flags_str(self.wrapper.tbc_type)}) Killing tasks"
        )

    def _set_proc_status(self) -> None:
        """Parse the returncode from a process and set the state."""
        if self._process is not None:
            if self._process.returncode == 0 or self.wrapper.ignore_error:
                self._process_state.set_success()
            else:
                self._process_state.set_error()

        logging.getLogger("console").debug(
            f"{self.wrapper.process_name} "
            f"({FlagHelper.get_flags_str(self.wrapper.tbc_type)}) "
            f"stopped with status: {self._process_state.status}"
        )

    async def _parse_process_output(self) -> None:
        """Parse a line from a process. This data is read by the progress handler."""
        while (
            not self._stop_event.is_set()
            and self.log_pipe is not None
            and ProcessStatus.RUNNING in self._process_state.status
        ):
            read_task = asyncio.Task(self.log_pipe.readline())
            await asyncio.wait([read_task], timeout=0.1)

            raw_line = await read_task

            if not raw_line:
                # done
                break

            try:
                line = raw_line.decode("utf-8").strip()

                current_state = self._output_parser.parse_line(line)

                # update export state
                self._state.export.merge_snapshot(current_state)

                # send to process logger
                logging.getLogger(self._logger_name).info(f"{line}")
            except UnicodeDecodeError:
                # skip line
                continue

    @property
    def output_parser(self) -> Parser:
        """Return output parser created for process."""
        return self._output_parser

    @property
    def log_pipe(self) -> asyncio.StreamReader | None:
        """Get the pipe to parse output from.

        Some procs use STDOUT and some use STDERR. This will be determined by the
        Wrapper.
        """
        return (
            None
            if self._process is None
            else self._process.stdout
            if self.wrapper.log_stdout
            else self._process.stderr
        )

    @property
    def state(self) -> ProcessState:
        """Return the process state."""
        return self._process_state
