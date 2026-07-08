from __future__ import annotations

import re
import sys
from contextlib import suppress
from typing import TYPE_CHECKING

from tbc_video_export.process.parser.export_state import ExportStateSnapshot
from tbc_video_export.process.parser.parser import Parser

if TYPE_CHECKING:
    from tbc_video_export.common.enums import ToolType

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class ParserChromaDecode(Parser):
    """Parser for the chroma-decode process."""

    tracked_value: int
    tracked_value_name: str
    tracked_value_total: int
    current_fps: float

    @override
    def __init__(self, process_type: ToolType) -> None:
        super().__init__(process_type)

        self.tracked_value_name = "frame"
        self.tracked_value_start = 0

    @override
    def parse_line(self, line: str) -> ExportStateSnapshot:
        state = ExportStateSnapshot()
        patterns = [
            r"Info: Processing from start frame # (.*?) with a length of (.*?) frames",
            r"Info: (.*?) frames processed - (.*?) FPS",
            r"Info: Processing complete - (.*?) frames in .* seconds \( (.*?) FPS \)",
            r"Warning: .*",
            r"Critical: .*",
        ]

        with suppress(ValueError):
            if reg := re.match("|".join(patterns), line):
                # matches but no groups, an error
                if all(v is None for v in reg.groups()):
                    self.error_count += 1
                    state.message = self._create_log_line(line)
                elif (start_frame := reg.group(1)) is not None and (
                    frame_count := reg.group(2)
                ) is not None:
                    self.tracked_value_start = int(start_frame)
                    self.tracked_value_total = int(frame_count)
                elif (current_frame := reg.group(3)) is not None and (
                    current_fps := reg.group(4)
                ) is not None:
                    self.tracked_value = int(current_frame)
                    self.current_fps = float(current_fps)
                elif (total_frames := reg.group(5)) is not None and (
                    end_fps := reg.group(6)
                ) is not None:
                    self.tracked_value = int(total_frames)
                    self.current_fps = float(end_fps)

        return state

    @override
    @property
    def hide_tbc_type(self) -> bool:
        return False
