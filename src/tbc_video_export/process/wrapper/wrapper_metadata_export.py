from __future__ import annotations

import asyncio
import sys
from functools import cached_property
from typing import TYPE_CHECKING

from tbc_video_export.common.enums import PipeType, ToolType
from tbc_video_export.common.utils import FlatList
from tbc_video_export.process.wrapper.wrapper import Wrapper

if TYPE_CHECKING:
    from tbc_video_export.process.wrapper.wrapper_config import WrapperConfig
    from tbc_video_export.program_state import ProgramState

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class WrapperMetadataExport(Wrapper[None, None]):
    """Wrapper for the metadata-export process."""

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
                "--ffmetadata",
                self._state.file_helper.ffmetadata_file,
                "--closed-captions",
                self._state.file_helper.cc_file,
                self._state.file_helper.tbc_json.file_name,
            ),
        )

    @override
    @cached_property
    def tool_type(self) -> ToolType:
        return ToolType.METADATA_EXPORT

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
