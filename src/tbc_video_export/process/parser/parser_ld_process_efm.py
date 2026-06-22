from __future__ import annotations

import re
import sys
from contextlib import suppress
from typing import TYPE_CHECKING

from tbc_video_export.process.parser.export_state import ExportStateSnapshot
from tbc_video_export.process.parser.parser import Parser

if TYPE_CHECKING:
    from tbc_video_export.common.enums import ProcessName

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class ParserLDProcessEFM(Parser):
    """Parser for ld-process-efm process."""

    tracked_value: int
    tracked_value_name: str
    tracked_value_total: int

    def __init__(self, process_name: ProcessName) -> None:
        super().__init__(process_name)

        self.tracked_value_name = "%"
        self.tracked_value_total = 100

    @override
    def parse_line(self, line: str) -> ExportStateSnapshot:
        state = ExportStateSnapshot()

        patterns = [
            r"Info: Processed (.*?)%$",
            r"Info:      Corrupt samples: (.*?)$",
            r"Info:      Missing samples: (.*?)$",
        ]

        with suppress(ValueError):
            if (reg := re.match("|".join(patterns), line)) is not None:
                if (percentage := reg.group(1)) is not None:
                    self.tracked_value = int(percentage)
                elif (samples := reg.group(2)) is not None or (
                    samples := reg.group(3)
                ) is not None:
                    self.error_count += int(samples)

        return state

    @override
    @property
    def hide_tbc_type(self) -> bool:
        return True
