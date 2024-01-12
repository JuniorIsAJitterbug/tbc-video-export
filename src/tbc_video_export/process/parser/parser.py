from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

from tbc_video_export.process.parser.export_state import (
    ExportStateMessage,
    ExportStateSnapshot,
)

if TYPE_CHECKING:
    from tbc_video_export.common.enums import ProcessName


class Parser(ABC):
    """Abstract class for process parsing."""

    def __init__(self, process_name: ProcessName) -> None:
        self._process_name = process_name
        self._tracked_value_total = 0
        self._tracked_value_name = ""
        self._tracked_value = 0
        self._current_fps = 0.0
        self._error_count = 0

    @abstractmethod
    def parse_line(self, line: str) -> ExportStateSnapshot:
        """Parse process output line.

        This will set the process state in this object while returning an export state
        snapshot. This snapshot is a global state and is handled by the caller.
        """

    @property
    @abstractmethod
    def hide_tbc_type(self) -> bool:
        """Return True if we should hide the TBC type for the process.

        For some this is a pointless piece of information and should be hidden.
        """

    @property
    def tracked_value_total(self) -> int:
        """Returns total count for whatever the handler is tracking."""
        return self._tracked_value_total

    @tracked_value_total.setter
    def tracked_value_total(self, value: int) -> None:
        """Set the total count for whatever the handler is tracking."""
        self._tracked_value_total = value

    @property
    def error_count(self) -> int:
        """Return the current error count read from the process."""
        return self._error_count

    @error_count.setter
    def error_count(self, value: int) -> None:
        """Set the current error count read from the process."""
        self._error_count = value

    @property
    def tracked_value_name(self) -> str:
        """Returns the name of whatever the handler is tracking."""
        return self._tracked_value_name

    @tracked_value_name.setter
    def tracked_value_name(self, value: str) -> None:
        """Set the name of whatever the handler is tracking."""
        self._tracked_value_name = value

    @property
    def current_fps(self) -> float:
        """Returns the current FPS read from the process."""
        return self._current_fps

    @current_fps.setter
    def current_fps(self, value: float) -> None:
        """Set the current FPS read from the process."""
        self._current_fps = value

    @property
    def tracked_value(self) -> int:
        """Returns the current count for whatever the handle is tracking."""
        return self._tracked_value

    @tracked_value.setter
    def tracked_value(self, value: int) -> None:
        """Set the current count for whatever the handle is tracking."""
        self._tracked_value = value

    @property
    def process_name(self) -> ProcessName:
        """Returns the process name."""
        return self._process_name

    def _create_log_line(self, line: str) -> ExportStateMessage:
        """Return a log line object."""
        return ExportStateMessage(line, datetime.now(), self.process_name)
