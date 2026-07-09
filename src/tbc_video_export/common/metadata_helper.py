from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path
from typing import Any

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import VideoSystem


class MetadataHelper:
    """Handles parsing the TBC metadata.

    This only supports reading JSON metadata.
    """

    def __init__(self, json_file_name: Path | None, json_data: Any = None) -> None:
        if json_file_name is not None:
            self.json_file_name = json_file_name
            self.sqlite_file_name = json_file_name.with_suffix(".db")

            try:
                with Path.open(json_file_name, mode="r", encoding="utf-8") as json_file:
                    self._json_data = json.load(json_file)
            except FileNotFoundError as e:
                raise exceptions.TBCError(
                    f"TBC json not found ({json_file_name})."
                ) from e
            except PermissionError as e:
                raise exceptions.TBCError(
                    f"Permission denied opening TBC json ({json_file_name})."
                ) from e
            except json.JSONDecodeError as e:
                raise exceptions.TBCError(
                    f"Unable to parse TBC json ({json_file_name})."
                ) from e
        else:
            self._json_data = json.loads(json_data)

    @property
    def json_file_name(self) -> Path:
        """Return json metadata file name."""
        return self._json_file_name

    @json_file_name.setter
    def json_file_name(self, file_name: Path) -> None:
        self._json_file_name = file_name

    @property
    def sqlite_file_name(self) -> Path:
        """Return sqlite file name."""
        return self._sqlite_file_name

    @sqlite_file_name.setter
    def sqlite_file_name(self, file_name: Path) -> None:
        self._sqlite_file_name = file_name

    @cached_property
    def is_widescreen(self) -> bool:
        """Returns whether the json TBC flags widescreen."""
        return (
            "isWidescreen" in self._json_data["videoParameters"]
            and self._json_data["videoParameters"]["isWidescreen"]
        )

    @cached_property
    def video_system(self) -> VideoSystem:
        """Return VideoSystem from TBC json."""
        if "system" in self._json_data["videoParameters"]:
            system = self._json_data["videoParameters"]["system"]

            # search for PAL* or NTSC* in videoParameters.system
            # isSourcePal and isSourceNtsc sometimes used, but not
            # sure if it's worth checking for
            match system.replace("-", "_").lower():
                case VideoSystem.PAL.value:
                    return VideoSystem.PAL

                case VideoSystem.PAL_M.value:
                    return VideoSystem.PAL_M

                case VideoSystem.NTSC.value:
                    return VideoSystem.NTSC

                case _:
                    raise exceptions.TBCError(f"System unsupported ({system}).")

        raise exceptions.TBCError("Unable to read video system from TBC json.")

    @cached_property
    def field_count(self) -> int:
        """Get total # of fields in TBC."""
        return len(self._json_data["fields"])

    @cached_property
    def frame_count(self) -> int:
        """Get total # of frames in TBC."""
        return int(self.field_count / 2)

    @cached_property
    def timecode(self) -> str:
        """Attempt to read a VITC timecode for the first frame.

        Return starting timecode if no VITC data found.
        """
        # ruff: disable[PLR2004]
        if (
            not self._json_data["fields"]
            or "vitc" not in self._json_data["fields"][0]
            or "vitcData" not in self._json_data["fields"][0]["vitc"]
        ):
            return "00:00:00:00"

        is_valid = True
        is_30_frame = self.video_system is not VideoSystem.PAL
        vitc_data = self._json_data["fields"][0]["vitc"]["vitcData"]

        def decode_bcd(tens: int, units: int) -> int:
            nonlocal is_valid

            if tens > 9:
                is_valid = False
                tens = 9

            if units > 9:
                is_valid = False
                units = 9

            return (tens * 10) + units

        hour = decode_bcd(vitc_data[7] & 0x03, vitc_data[6] & 0x0F)
        minute = decode_bcd(vitc_data[5] & 0x07, vitc_data[4] & 0x0F)
        second = decode_bcd(vitc_data[3] & 0x07, vitc_data[2] & 0x0F)
        frame = decode_bcd(vitc_data[1] & 0x03, vitc_data[0] & 0x0F)

        invalid_time = hour > 23 or minute > 59 or second > 59

        if (
            invalid_time
            or (is_30_frame and frame > 29)
            or (not is_30_frame and frame > 24)
        ):
            is_valid = False

        is_drop_frame = (vitc_data[1] & 0x04) != 0 if is_30_frame else False

        if not is_valid:
            return "00:00:00:00"

        sep = ";" if is_drop_frame else ":"

        return f"{hour:02d}:{minute:02d}:{second:02d}{sep}{frame:02d}"
        # ruff: enable[PLR2004]
