from __future__ import annotations

import asyncio
import sys
from functools import cached_property
from typing import TYPE_CHECKING

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import PipeType, ProcessName
from tbc_video_export.common.utils import FlatList
from tbc_video_export.process.wrapper.wrapper import Wrapper

if TYPE_CHECKING:
    from pathlib import Path

    from tbc_video_export.process.wrapper.wrapper_config import WrapperConfig
    from tbc_video_export.program_state import ProgramState

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class WrapperLDProcessEFM(Wrapper[None, None]):
    """Wrapper for ld-process-efm."""

    def __init__(self, state: ProgramState, config: WrapperConfig[None, None]) -> None:
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
                self._state.opts.convert_opt("process_efm_dts", "--dts"),
                self._get_efm_file(),
                self._get_output_file(),
            ),
        )

    def _get_efm_file(self) -> Path:
        if self._state.file_helper.efm_file is None:
            raise exceptions.FileIOError(
                "Could not find EFM file. Try without --process-efm."
            )

        return self._state.file_helper.efm_file

    def _get_output_file(self) -> Path:
        return (
            self._state.file_helper.get_output_file_from_ext("digital.pcm")
            if not self._state.opts.process_efm_dts
            else self._state.file_helper.get_output_file_from_ext("dts")
        )

    @override
    @cached_property
    def process_name(self) -> ProcessName:
        return ProcessName.LD_PROCESS_EFM

    @override
    @cached_property
    def supported_pipe_types(self) -> PipeType:
        return PipeType.NONE

    @override
    @cached_property
    def stdin(self) -> int | None:
        return None

    @override
    @cached_property
    def stdout(self) -> int | None:
        return asyncio.subprocess.DEVNULL

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

    @override
    @cached_property
    def ignore_error(self) -> bool:
        return False

    @override
    @cached_property
    def stop_on_last_alive(self) -> bool:
        return False
