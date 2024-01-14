from __future__ import annotations

import re
from contextlib import suppress
from typing import TYPE_CHECKING

from tbc_video_export.process.parser.export_state import ExportStateSnapshot
from tbc_video_export.process.parser.parser import Parser

if TYPE_CHECKING:
    from tbc_video_export.common.enums import ProcessName


class ParserLDProcessVBI(Parser):
    """Parser for ld-process-vbi process."""

    def __init__(self, process_name: ProcessName) -> None:
        super().__init__(process_name)

        self.tracked_value_name = "field"

    def parse_line(self, line: str) -> ExportStateSnapshot:  # noqa: D102
        state = ExportStateSnapshot()

        patterns = [
            r"Info: Using .* threads to process (.*?) fields",
            r"Info: Processing field (.*?)$",
            (
                r"Info: VBI Processing complete - (.*?) "
                r"fields in .* seconds \( (.*?) FPS \)"
            ),
            r"Warning: .*",
            r"Critical: .*",
        ]

        with suppress(ValueError):
            if (reg := re.match("|".join(patterns), line)) is not None:
                # matches but no groups, error
                if all(v is None for v in reg.groups()):
                    self.error_count += 1
                    state.message = self._create_log_line(line)
                elif (total_fields := reg.group(1)) is not None:
                    self.tracked_value_total = int(total_fields)
                elif (current_field := reg.group(2)) is not None:
                    self.tracked_value = int(current_field)
                elif (total_fields := reg.group(3)) is not None and (
                    end_fps := reg.group(4)
                ) is not None:
                    self.tracked_value = int(total_fields)
                    self.fps = float(end_fps)

        return state

    @property
    def hide_tbc_type(self) -> bool:  # noqa: D102
        return True
