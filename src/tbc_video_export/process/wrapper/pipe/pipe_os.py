from __future__ import annotations

import logging
import os
import sys
from contextlib import suppress
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from tbc_video_export.common.enums import PipeType
from tbc_video_export.process.wrapper.pipe.pipe import Pipe

if TYPE_CHECKING:
    from types import TracebackType

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class PipeOS(Pipe):
    """OS pipe for stdin/stdout helper."""

    _stdin: int | None = None
    _stdout: int | None = None

    @override
    async def __aenter__(self) -> Pipe:
        """Enter OS pipe context."""
        logging.getLogger("console").debug("Creating os.pipe")
        self._stdin, self._stdout = os.pipe()
        return self

    @override
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None | bool:
        """Exit OS pipe context."""
        self.close()

    @override
    @cached_property
    def pipe_type(self) -> PipeType:
        return PipeType.OS

    @override
    @cached_property
    def in_path(self) -> Path:
        return Path("-")

    @override
    @cached_property
    def out_path(self) -> Path:
        return Path("-")

    @override
    @property
    def in_handle(self) -> int | None:
        return self._stdin

    @override
    @property
    def out_handle(self) -> int | None:
        return self._stdout

    @override
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
