from __future__ import annotations

import asyncio
from functools import cached_property
from typing import TYPE_CHECKING

from tbc_video_export.common.enums import PipeType, ProcessName
from tbc_video_export.common.utils import FlatList
from tbc_video_export.process.wrapper.wrapper import Wrapper

if TYPE_CHECKING:
    from tbc_video_export.process.wrapper.wrapper_config import WrapperConfig
    from tbc_video_export.program_state import ProgramState


class WrapperLDExportMetadata(Wrapper):
    """Wrapper for ld-export-metadata."""

    def __init__(self, state: ProgramState, config: WrapperConfig[None, None]) -> None:
        super().__init__(state, config)
        self._config = config

    def post_fn(self) -> None:  # noqa: D102
        pass

    @property
    def command(self) -> FlatList:  # noqa: D102
        return FlatList(
            (
                self.binary,
                "--ffmetadata",
                self._state.file_helper.ffmetadata_file,
                "--closed-captions",
                self._state.file_helper.cc_file,
                self._state.file_helper.tbc_json.file_name,
            ),
        )

    @cached_property
    def process_name(self) -> ProcessName:  # noqa: D102
        return ProcessName.LD_EXPORT_METADATA

    @cached_property
    def supported_pipe_types(self) -> PipeType:  # noqa: D102
        return PipeType.NONE

    @cached_property
    def stdin(self) -> int | None:  # noqa: D102
        return None

    @cached_property
    def stdout(self) -> int | None:  # noqa: D102
        return asyncio.subprocess.DEVNULL

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
        return False

    @cached_property
    def stop_on_last_alive(self) -> bool:  # noqa: D102
        return False
