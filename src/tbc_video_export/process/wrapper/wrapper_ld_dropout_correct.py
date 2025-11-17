from __future__ import annotations

import asyncio
import os
from functools import cached_property
from typing import TYPE_CHECKING

from tbc_video_export.common.enums import PipeType, ProcessName
from tbc_video_export.common.utils import FlatList
from tbc_video_export.process.wrapper.wrapper import Wrapper

if TYPE_CHECKING:
    from tbc_video_export.process.wrapper.pipe import Pipe
    from tbc_video_export.process.wrapper.wrapper_config import WrapperConfig
    from tbc_video_export.program_state import ProgramState


class WrapperLDDropoutCorrect(Wrapper):
    """Wrapper for ld-dropout-correct."""

    def __init__(self, state: ProgramState, config: WrapperConfig[None, Pipe]) -> None:
        super().__init__(state, config)
        self._config = config

    def post_fn(self) -> None:  # noqa: D102
        pass

    @property
    def command(self) -> FlatList:  # noqa: D102
        l = FlatList(
            (
                self.binary,
                self._get_thread_opts(),
                self._state.file_helper.tbcs[self._config.tbc_type],
                "--input-json",
                self._state.file_helper.tbc_json.file_name,
                "--output-json",
                os.devnull,
                self._config.output_pipes.out_path,
            )
        )
        if self._state.opts.dropout_allow_interfield is False:
            l.append("-i")
        return l

    def _get_thread_opts(self) -> FlatList | None:
        thread_count = self._state.opts.threads

        if (t := self._state.opts.dropout_correct_threads) is not None:
            thread_count = t

        if thread_count != 0:
            return FlatList(("-t", thread_count))

        return None

    @cached_property
    def process_name(self) -> ProcessName:  # noqa: D102
        return ProcessName.LD_DROPOUT_CORRECT

    @cached_property
    def supported_pipe_types(self) -> PipeType:  # noqa: D102
        return PipeType.NULL | PipeType.OS

    @cached_property
    def stdin(self) -> int | None:  # noqa: D102
        return None

    @cached_property
    def stdout(self) -> int | None:  # noqa: D102
        return self._config.output_pipes.out_handle

    @cached_property
    def stderr(self) -> int | None:  # noqa: D102
        return asyncio.subprocess.PIPE

    @cached_property
    def log_output(self) -> bool:  # noqa: D102
        return True

    @cached_property
    def log_stdout(self) -> bool:  # noqa: D102
        return False

    @cached_property
    def env(self) -> dict[str, str] | None:  # noqa: D102
        return None

    @cached_property
    def ignore_error(self) -> bool:  # noqa: D102
        # ld-dropout-correct does not support -l or -s flags and will
        # be killed when other procs are finished.
        # This is unfortunate as we would have to use more
        # complicated logic to determine a real crash from success.
        # Currently we do not check any errors from ld-dropout-correct
        # and assume all returncodes are success.
        return True

    @cached_property
    def stop_on_last_alive(self) -> bool:  # noqa: D102
        # On NT systems closing an os.pipe() does not kill the procs using
        # the pipe. The result of this is ld-dropout-correct continuing
        # to run after other procs have finished when using -l or -s.
        # This will signal to the proc killer to kill the process if it
        # is the only remaining proc type running.
        # This is essentially a workaround until ld-dropout-correct
        # supports -s/-l or properly supports named pipes.
        return True
