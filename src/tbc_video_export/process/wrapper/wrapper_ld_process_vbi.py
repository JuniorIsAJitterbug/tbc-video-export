from __future__ import annotations

import asyncio
import sys
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from tbc_video_export.common.enums import PipeType, ProcessName, TBCType
from tbc_video_export.common.utils import FlatList
from tbc_video_export.process.wrapper.wrapper import Wrapper

if TYPE_CHECKING:
    from tbc_video_export.process.wrapper.wrapper_config import WrapperConfig
    from tbc_video_export.program_state import ProgramState

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class WrapperLDProcessVBI(Wrapper[None, None]):
    """Wrapper for ld-process-vbi."""

    def __init__(self, state: ProgramState, config: WrapperConfig[None, None]) -> None:
        self._tbc_json_vbi = Path(f"{state.file_helper.input_name}.vbi.json")

        super().__init__(state, config)
        self._config = config

    @override
    def post_fn(self) -> None:
        # if dry run, just update the file name
        if self._state.dry_run:
            self._state.file_helper.tbc_json.file_name = self._tbc_json_vbi
        elif Path(self._tbc_json_vbi).is_file():
            # load the new tbc json
            self._state.file_helper.tbc_json = self._tbc_json_vbi

    @override
    @property
    def command(self) -> FlatList:
        return FlatList(
            (
                self.binary,
                self._get_thread_opts(),
                "--input-json",
                self._state.file_helper.tbc_json.file_name,
                "--output-json",
                self._tbc_json_vbi,
                self._get_tbc(),
            ),
        )

    def _get_tbc(self) -> Path:
        return (
            self._state.file_helper.tbcs[TBCType.LUMA]
            if TBCType.LUMA in self._state.file_helper.tbcs
            else self._state.file_helper.tbcs[TBCType.COMBINED]
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
    def process_name(self) -> ProcessName:
        return ProcessName.LD_PROCESS_VBI

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
