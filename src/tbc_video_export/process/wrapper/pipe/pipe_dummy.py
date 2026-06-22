from __future__ import annotations

import sys
from functools import cached_property
from typing import TYPE_CHECKING

from tbc_video_export.common.enums import PipeType
from tbc_video_export.process.wrapper.pipe.pipe import Pipe

if TYPE_CHECKING:
    from pathlib import Path
    from types import TracebackType

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class PipeDummy(Pipe):
    """Dummy pipe, does nothing. Used for dry-runs."""

    def __init__(self, stdin_str: Path | str, stdout_str: Path | str) -> None:
        self._stdin_str = stdin_str
        self._stdout_str = stdout_str

    @override
    async def __aenter__(self) -> Pipe:
        """Enter dummy pipe context."""
        return self

    @override
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None | bool:
        """Exit dummy pipe context."""

    @override
    @cached_property
    def pipe_type(self) -> PipeType:
        return PipeType.NULL

    @override
    @cached_property
    def in_path(self) -> Path | str:
        return self._stdin_str

    @override
    @cached_property
    def out_path(self) -> Path | str:
        return self._stdout_str

    @override
    @property
    def in_handle(self) -> int | None:
        return None

    @override
    @property
    def out_handle(self) -> int | None:
        return None

    @override
    def close(self) -> None:
        """Does nothing."""
