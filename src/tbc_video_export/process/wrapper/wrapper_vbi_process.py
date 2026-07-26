from __future__ import annotations

import asyncio
import sys
from functools import cached_property
from typing import TYPE_CHECKING

from tbc_video_export.common.enums import MetadataType, PipeType, TBCType, ToolType
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


class WrapperVBIProcess(Wrapper[None, None]):
    """Wrapper for the vbi-process process."""

    @override
    def __init__(self, state: ProgramState, config: WrapperConfig[None, None]) -> None:
        super().__init__(state, config)
        self._tbc_metadata = state.file_helper.tbc_metadata
        self._metadata_vbi_file = self.metadata_input_file.with_suffix(
            f".vbi{self.metadata_input_file.suffix}"
        )

    @override
    def post_fn(self) -> None:
        match self._state.opts.metadata_type:
            case MetadataType.JSON:
                if self._state.dry_run:
                    # if dry run, just update the file name
                    self._state.file_helper.tbc_metadata.json_file_name = (
                        self._metadata_vbi_file
                    )
                else:
                    # reload json metadata
                    self._state.file_helper.tbc_metadata = self._metadata_vbi_file

            case MetadataType.SQLITE:
                # assign to new sqlite metadata file
                self._state.file_helper.tbc_metadata.sqlite_file_name = (
                    self._metadata_vbi_file
                )

    @override
    @property
    def command(self) -> FlatList:
        return FlatList(
            (
                self.binary,
                self._get_thread_opts(),
                self.metadata_input_opt,
                self.metadata_input_file,
                self.metadata_output_opt,
                self._metadata_vbi_file,
                self._get_tbc(),
            ),
        )

    def _get_tbc(self) -> Path:
        return (
            self._state.file_helper.input_file.tbcs[TBCType.LUMA]
            if TBCType.LUMA in self._state.file_helper.input_file.tbcs
            else self._state.file_helper.input_file.tbcs[TBCType.COMBINED]
        )

    def _get_thread_opts(self) -> FlatList | None:
        thread_count = self._state.opts.threads

        if (t := self._state.opts.process_vbi_threads) is not None:
            thread_count = t

        if thread_count != 0:
            return FlatList(("-t", thread_count))

        return None

    @override
    @cached_property
    def tool_type(self) -> ToolType:
        return ToolType.VBI_PROCESS

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
        # process-vbi logs to stdout
        return asyncio.subprocess.PIPE

    @override
    @cached_property
    def stderr(self) -> int | None:
        # forward any errors to stdout
        return asyncio.subprocess.STDOUT

    @override
    @cached_property
    def log_output(self) -> bool:
        return True

    @override
    @cached_property
    def log_stdout(self) -> bool:
        return True

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
