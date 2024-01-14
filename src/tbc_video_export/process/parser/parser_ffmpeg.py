from __future__ import annotations

import re
from contextlib import suppress
from typing import TYPE_CHECKING

from tbc_video_export.process.parser.export_state import ExportStateSnapshot
from tbc_video_export.process.parser.parser import Parser

if TYPE_CHECKING:
    from tbc_video_export.common.enums import ProcessName


class ParserFFmpeg(Parser):
    """Parser for FFmpeg process."""

    def __init__(self, process_name: ProcessName) -> None:
        super().__init__(process_name)

        self.tracked_value_name = "frame"

    def parse_line(self, line: str) -> ExportStateSnapshot:  # noqa: D102
        state = ExportStateSnapshot()

        patterns = [
            r"frame=(.*?)$",
            r"fps=(.*?)$",
            r"bitrate=(.*?)$",
            r"total_size=(.*?)$",
            r"dup_frames=(.*?)$",
            r"drop_frames=(.*?)$",
            r"out_time=(.*?)$",
        ]

        with suppress(ValueError):
            if (reg := re.match("|".join(patterns), line)) is not None:
                # matches but no groups, an error
                # we should never see any other messages here, so exit
                if (frame := reg.group(1)) is not None:
                    self.tracked_value = int(frame)
                elif (fps := reg.group(2)) is not None:
                    self.current_fps = float(fps)
                elif (bitrate := reg.group(3)) is not None:
                    state.bitrate = bitrate
                elif (size := reg.group(4)) is not None:
                    state.size = int(size) / 1024 / 1024 / 1024
                elif None not in {reg.group(5), reg.group(6)}:
                    self.error_count += 1
                elif (duration := reg.group(7)) is not None:
                    state.duration = duration

        return state

    @property
    def hide_tbc_type(self) -> bool:  # noqa: D102
        return True
