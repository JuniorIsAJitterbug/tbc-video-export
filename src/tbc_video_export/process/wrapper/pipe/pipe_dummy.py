from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from tbc_video_export.common.enums import PipeType
from tbc_video_export.process.wrapper.pipe.pipe import Pipe

if TYPE_CHECKING:
    from pathlib import Path
    from types import TracebackType


class PipeDummy(Pipe):
    """Dummy pipe, does nothing. Used for dry-runs."""

    def __init__(self, stdin_str: str, stdout_str: str) -> None:
        self._stdin_str = stdin_str
        self._stdout_str = stdout_str

    async def __aenter__(self) -> Pipe:
        """Enter dummy pipe context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None | bool:
        """Exit dummy pipe context."""

    @cached_property
    def pipe_type(self) -> PipeType:  # noqa: D102
        return PipeType.NULL

    @cached_property
    def in_path(self) -> Path | str:  # noqa: D102
        return self._stdin_str

    @cached_property
    def out_path(self) -> Path | str:  # noqa: D102
        return self._stdout_str

    @property
    def in_handle(self) -> int | None:  # noqa: D102
        return None

    @property
    def out_handle(self) -> int | None:  # noqa: D102
        return None

    def close(self) -> None:
        """Does nothing."""
