from __future__ import annotations

import re
from contextlib import suppress
from typing import TYPE_CHECKING

from tbc_video_export.process.parser.export_state import ExportStateSnapshot
from tbc_video_export.process.parser.parser import Parser

if TYPE_CHECKING:
    from tbc_video_export.common.enums import ProcessName


class ParserLDExportMetadata(Parser):
    """Parser for ld-export-metadata process.

    This tool is silent unless there is a problem.
    """

    def __init__(self, process_name: ProcessName) -> None:
        super().__init__(process_name)

    def parse_line(self, line: str) -> ExportStateSnapshot:  # noqa: D102
        state = ExportStateSnapshot()

        patterns = [
            r".*",
        ]

        with suppress(ValueError):
            # matches but no groups, error
            if (reg := re.match("|".join(patterns), line)) is not None and all(
                v is None for v in reg.groups()
            ):
                self.error_count += 1

        return state

    @property
    def hide_tbc_type(self) -> bool:  # noqa: D102
        return True
