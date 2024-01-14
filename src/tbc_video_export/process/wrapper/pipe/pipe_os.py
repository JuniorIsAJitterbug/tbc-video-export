from __future__ import annotations

import logging
import os
from contextlib import suppress
from functools import cached_property
from typing import TYPE_CHECKING

from tbc_video_export.common.enums import PipeType
from tbc_video_export.process.wrapper.pipe.pipe import Pipe

if TYPE_CHECKING:
    from pathlib import Path
    from types import TracebackType


class PipeOS(Pipe):
    """OS pipe for stdin/stdout helper."""

    _stdin: int | None = None
    _stdout: int | None = None

    async def __aenter__(self) -> Pipe:
        """Enter OS pipe context."""
        logging.getLogger("console").debug("Creating os.pipe")
        self._stdin, self._stdout = os.pipe()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None | bool:
        """Exit OS pipe context."""
        self.close()

    @cached_property
    def pipe_type(self) -> PipeType:  # noqa: D102
        return PipeType.OS

    @cached_property
    def in_path(self) -> Path | str:  # noqa: D102
        return "-"

    @cached_property
    def out_path(self) -> Path | str:  # noqa: D102
        return "-"

    @property
    def in_handle(self) -> int | None:  # noqa: D102
        return self._stdin

    @property
    def out_handle(self) -> int | None:  # noqa: D102
        return self._stdout

    def close(self) -> None:
        """Close the OS pipe."""
        logging.getLogger("console").debug("Closing pipe os.pipe")

        with suppress(OSError):
            if self.in_handle is not None and self.in_handle > -1:
                os.close(self.in_handle)
                logging.getLogger("console").debug("Closed in handle")

            if self.out_handle is not None and self.out_handle > -1:
                os.close(self.out_handle)
                logging.getLogger("console").debug("Closed out handle")
