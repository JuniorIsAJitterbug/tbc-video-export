from __future__ import annotations

import re
from contextlib import suppress
from typing import TYPE_CHECKING

from tbc_video_export.process.parser.export_state import ExportStateSnapshot
from tbc_video_export.process.parser.parser import Parser

if TYPE_CHECKING:
    from tbc_video_export.common.enums import ProcessName


class ParserLDChromaDecoder(Parser):
    """Parser for ld-chroma-decoder process."""

    def __init__(self, process_name: ProcessName) -> None:
        super().__init__(process_name)

        self.tracked_value_name = "frame"

    def parse_line(self, line: str) -> ExportStateSnapshot:  # noqa: D102
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
                    self.tracked_value = int(start_frame)
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

    @property
    def hide_tbc_type(self) -> bool:  # noqa: D102
        return False
