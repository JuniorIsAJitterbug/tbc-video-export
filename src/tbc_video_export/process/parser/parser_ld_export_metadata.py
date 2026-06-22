from __future__ import annotations

import re
import sys
from contextlib import suppress
from typing import TYPE_CHECKING

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

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

    @override
    def parse_line(self, line: str) -> ExportStateSnapshot:
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

    @override
    @property
    def hide_tbc_type(self) -> bool:
        return True
