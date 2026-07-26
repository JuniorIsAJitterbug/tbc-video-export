from __future__ import annotations

import asyncio
import os
import sys
from functools import cached_property
from typing import TYPE_CHECKING

from tbc_video_export.common.enums import PipeType, TBCType, ToolType
from tbc_video_export.common.utils import FlatList
from tbc_video_export.process.wrapper.pipe import Pipe
from tbc_video_export.process.wrapper.wrapper import Wrapper

if TYPE_CHECKING:
    from tbc_video_export.process.wrapper.wrapper_config import WrapperConfig
    from tbc_video_export.program_state import ProgramState

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class WrapperDropoutCorrect(Wrapper[None, Pipe]):
    """Wrapper for the dropout-correct process."""

    @override
    def __init__(self, state: ProgramState, config: WrapperConfig[None, Pipe]) -> None:
        super().__init__(state, config)
        self._config = config

    @override
    def post_fn(self) -> None:
        pass

    @override
    @property
    def command(self) -> FlatList:
        return FlatList(
            (
                self.binary,
                self._get_thread_opts(),
                self._state.file_helper.input_file.tbcs[self._config.tbc_type],
                None if self.dropout_interfield_correction else "-i",
                self.metadata_input_opt,
                self.metadata_input_file,
                self.metadata_output_opt,
                os.devnull,
                self._config.output_pipes.out_path,
            )
        )

    def _get_thread_opts(self) -> FlatList | None:
        thread_count = self._state.opts.threads

        if (t := self._state.opts.dropout_correct_threads) is not None:
            thread_count = t

        if thread_count != 0:
            return FlatList(("-t", thread_count))

        return None

    @override
    @cached_property
    def tool_type(self) -> ToolType:
        return ToolType.DROPOUT_CORRECT

    @override
    @cached_property
    def supported_pipe_types(self) -> PipeType:
        return PipeType.NULL | PipeType.OS

    @override
    @cached_property
    def stdin(self) -> int | None:
        return None

    @override
    @cached_property
    def stdout(self) -> int | None:
        return self._config.output_pipes.out_handle

    @override
    @cached_property
    def stderr(self) -> int | None:
        return asyncio.subprocess.PIPE

    @override
    @cached_property
    def log_output(self) -> bool:
        return True

    @override
    @cached_property
    def log_stdout(self) -> bool:
        return False

    @override
    @cached_property
    def env(self) -> dict[str, str] | None:
        return None

    @cached_property
    def dropout_interfield_correction(self) -> bool:  # noqa: D102
        if self._state.opts.dropout_interfield_correction == TBCType.NONE:
            return False

        return (
            self._state.opts.dropout_interfield_correction
            in (self.tbc_type, TBCType.COMBINED)
            or self.tbc_type == TBCType.COMBINED
        )

    @override
    @cached_property
    def ignore_error(self) -> bool:
        # ld-dropout-correct does not support -l or -s flags and will
        # be killed when other procs are finished.
        # This is unfortunate as we would have to use more
        # complicated logic to determine a real crash from success.
        # Currently we do not check any errors from ld-dropout-correct
        # and assume all returncodes are success.
        return True

    @override
    @cached_property
    def stop_on_last_alive(self) -> bool:
        # On NT systems closing an os.pipe() does not kill the procs using
        # the pipe. The result of this is ld-dropout-correct continuing
        # to run after other procs have finished when using -l or -s.
        # This will signal to the proc killer to kill the process if it
        # is the only remaining proc type running.
        # This is essentially a workaround until ld-dropout-correct
        # supports -s/-l or properly supports named pipes.
        return True
