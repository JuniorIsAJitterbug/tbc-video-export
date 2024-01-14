from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from tbc_video_export.common.enums import ProcessName


@dataclass
class ExportState:
    """Data from procs that represent the export state."""

    size: float = 0.0
    bitrate: str = "n/a"
    duration: str = "n/a   "
    messages: list[ExportStateMessage] = field(default_factory=list)
    concealments: int | None = None

    def merge_snapshot(self, snapshot: ExportStateSnapshot) -> None:
        """Merge a snapshot with the current export state."""
        if snapshot.size is not None:
            self.size = snapshot.size

        if snapshot.bitrate is not None:
            self.bitrate = snapshot.bitrate

        if snapshot.duration is not None:
            self.duration = snapshot.duration

        if snapshot.message is not None:
            self.messages.append(snapshot.message)

        if snapshot.concealments is not None:
            self.concealments = snapshot.concealments

    def append_message(self, message: str) -> None:
        """Append a message to the list.

        This is used when appending messages to the list from sources other than
        snapshots.
        """
        self.messages.append(
            ExportStateMessage(message, datetime.now(), ProcessName.NONE)
        )


@dataclass
class ExportStateSnapshot:
    """Snapshot data from procs, these values are merged with the export state."""

    size: float | None = None
    bitrate: str | None = None
    duration: str | None = None
    message: ExportStateMessage | None = None
    concealments: int | None = None


@dataclass
class ExportStateMessage:
    """Message data from process/wrappers."""

    message: str
    timestamp: datetime
    process: ProcessName
