from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from pathlib import Path
    from types import TracebackType

    from tbc_video_export.common.enums import PipeType, ProcessName, TBCType


class Pipe(ABC):
    """Abstract class for pipes."""

    def __init__(self, process_name: ProcessName, tbc_type: TBCType) -> None:
        self._process_name = process_name
        self._tbc_type = tbc_type

        logging.getLogger("console").debug(
            f"Pipe ({self.pipe_type}) created for {process_name} ({tbc_type})"
        )

    @abstractmethod
    async def __aenter__(self) -> Pipe:
        """Create named pipes."""

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None | bool:
        """Cleanup pipes and any temp dirs."""

    def __str__(self) -> str:
        """Return formatted string containing pipe paths."""
        return (
            f"{self.pipe_type}:\n"
            f"  in_path:\t{self.in_path}\n"
            f"  out_path:\t{self.out_path}\n"
            f"  in_handle:\t{self.in_handle}\n"
            f"  out_handle:\t{self.out_handle}\n"
        )

    @cached_property
    @abstractmethod
    def pipe_type(self) -> PipeType:
        """Get pipe type."""

    @cached_property
    @abstractmethod
    def in_path(self) -> Path | str:
        """Get pipe stdin string."""

    @cached_property
    @abstractmethod
    def out_path(self) -> Path | str:
        """Get pipe stdout string."""

    @property
    @abstractmethod
    def in_handle(self) -> int | None:
        """Get stdin pipe."""

    @property
    @abstractmethod
    def out_handle(self) -> int | None:
        """Get stdout pipe."""

    @abstractmethod
    def close(self) -> None:
        """Close pipe."""


@dataclass
class ConsumablePipe:
    """Class for grouping pipes together for processes."""

    tbc_type: TBCType
    consumer: ProcessName
    pipe: Pipe


# generics for wrappers
PipeInputGeneric = TypeVar("PipeInputGeneric", None, Pipe, tuple[Pipe, ...])
PipeOutputGeneric = TypeVar("PipeOutputGeneric", None, Pipe, tuple[Pipe, ...])
