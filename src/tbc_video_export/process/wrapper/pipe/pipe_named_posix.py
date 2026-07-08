from __future__ import annotations

import logging
import os
import sys
from contextlib import suppress
from functools import cached_property
from pathlib import Path
from tempfile import mkdtemp
from typing import TYPE_CHECKING

from tbc_video_export.common import consts, exceptions
from tbc_video_export.common.enums import PipeType
from tbc_video_export.process.wrapper.pipe.pipe import Pipe

if TYPE_CHECKING:
    from types import TracebackType

    from tbc_video_export.common.enums import TBCType, ToolType

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


assert os.name == "posix"  # noqa: S101


class PipeNamedPosix(Pipe):
    """Named pipe helper for POSIX systems."""

    # use a class variable as we only want a single temp dir created
    tmp_dir: str = ""

    def __init__(self, tool_type: ToolType, tbc_type: TBCType) -> None:
        super().__init__(tool_type, tbc_type)

        if not PipeNamedPosix.tmp_dir:
            try:
                PipeNamedPosix.tmp_dir = mkdtemp(
                    prefix=f"{consts.APPLICATION_NAME}-", suffix=""
                )
            except PermissionError as e:
                raise exceptions.PipeError(
                    "Unable to create pipes due to permissions."
                ) from e

    @override
    async def __aenter__(self) -> Pipe:
        """Enter posix pipe context."""
        try:
            logging.getLogger("console").debug(f"Creating named pipe {self.in_path}")
            os.mkfifo(self.in_path)
        except FileNotFoundError as e:
            raise exceptions.PipeError(
                "Unable to create pipes due to permissions."
            ) from e
        except PermissionError as e:
            raise exceptions.PipeError(
                "Unable to create pipes due to permissions."
            ) from e
        else:
            return self

    @override
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None | bool:
        """Exit posix pipe context."""
        PipeNamedPosix.tmp_dir = ""
        self.close()

    @override
    @cached_property
    def pipe_type(self) -> PipeType:
        return PipeType.NAMED_POSIX

    @override
    @cached_property
    def in_path(self) -> Path | str:
        return Path(PipeNamedPosix.tmp_dir).joinpath(
            f"{self._tool_type}-{self._tbc_type}"
        )

    @override
    @cached_property
    def out_path(self) -> Path | str:
        """Get pipe stdout string.

        POSIX systems use the same path for in/out.
        """
        return self.in_path

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
        """Close pipe."""
        logging.getLogger("console").debug(f"Closing pipe {self.in_path}")
        # we suppress FileNotFoundError so other files can be cleaned up
        with suppress(FileNotFoundError, PermissionError):
            Path.unlink(Path(self.in_path))

            # other pipes may exist in the directory, only remove if empty
            if sum(1 for _ in Path(PipeNamedPosix.tmp_dir).iterdir()) == 0:
                Path.rmdir(Path(PipeNamedPosix.tmp_dir))
