from __future__ import annotations

import json
from pathlib import Path
from re import escape
from tempfile import NamedTemporaryFile
from typing import ClassVar

import pytest

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import VideoSystem
from tbc_video_export.files import MetadataFile


class TestMetadataHelper:
    """Tests for metadata helper."""

    def test_open_json(self) -> None:
        with pytest.raises(
            exceptions.TBCError,
            match=escape("TBC json not found (tests/files/non_existent_file)."),
        ):
            _ = MetadataFile(Path("tests/files/non_existent_file"))

        with pytest.raises(
            json.JSONDecodeError,
        ):
            _ = MetadataFile(None, "blah")

        with (
            NamedTemporaryFile(suffix="_chroma.tbc") as file,
            pytest.raises(
                exceptions.TBCError,
                match=escape(f"Unable to parse TBC json ({file.name})."),
            ),
        ):
            _ = MetadataFile(Path(file.name))

        json_path = Path("tests/files/pal_svideo.tbc.json")
        metadata_helper = MetadataFile(json_path)
        assert metadata_helper.json_file_name == json_path

    def test_video_system(self) -> None:
        json_data = '{"videoParameters":{"system":"PAL"}}'
        metadata_helper = MetadataFile(None, json_data)
        assert metadata_helper.video_system == VideoSystem.PAL

        json_data = '{"videoParameters":{"system":"PAL-M"}}'
        metadata_helper = MetadataFile(None, json_data)
        assert metadata_helper.video_system == VideoSystem.PAL_M

        json_data = '{"videoParameters":{"system":"NTSC"}}'
        metadata_helper = MetadataFile(None, json_data)
        assert metadata_helper.video_system == VideoSystem.NTSC

        json_data = '{"videoParameters":{}}'
        metadata_helper = MetadataFile(None, json_data)

        with pytest.raises(
            exceptions.TBCError,
            match=escape("Unable to read video system from TBC json."),
        ):
            _ = metadata_helper.video_system

        json_data = '{"videoParameters":{"system":"INVALID"}}'
        metadata_helper = MetadataFile(None, json_data)

        with pytest.raises(
            exceptions.TBCError, match=escape("System unsupported (INVALID).")
        ):
            _ = metadata_helper.video_system

    def test_field_count(self) -> None:
        metadata_helper = MetadataFile(Path("tests/files/pal_svideo.tbc.json"))
        assert metadata_helper.field_count == 2
        assert metadata_helper.frame_count == 1

    def test_check_widescreen(self) -> None:
        json_data = '{"videoParameters":{}}'
        metadata_helper = MetadataFile(None, json_data)
        assert not metadata_helper.is_widescreen

        json_data = '{"videoParameters":{"isWidescreen":false}}'
        metadata_helper = MetadataFile(None, json_data)
        assert not metadata_helper.is_widescreen

        json_data = '{"videoParameters":{"isWidescreen":true}}'
        metadata_helper = MetadataFile(None, json_data)
        assert metadata_helper.is_widescreen

    vitc_data: ClassVar[list[tuple[str, str, str]]] = [
        ("[1,8,7,8,1,0,1,0]", "NTSC", "01:01:07:01"),
        ("[0,0,0,0,0,0,0,0]", "PAL", "00:00:00:00"),
        ("[10,0,0,0,0,0,0,0]", "PAL", "00:00:00:00"),
        ("[1,2,3,4,6,5,3,2]", "PAL", "23:56:43:21"),
        ("[1,4,0,0,0,0,0,0]", "NTSC", "00:00:00;01"),
    ]

    @pytest.mark.parametrize(("vitc_data", "system", "expected"), tuple(vitc_data))
    def test_vitc(self, vitc_data: str, system: str, expected: str) -> None:
        json_data = (
            '{"videoParameters":{"system":"'
            + system
            + '"},"fields":[{"vitc":{"vitcData":'
            + vitc_data
            + "}}]}"
        )
        metadata_helper = MetadataFile(None, json_data)
        assert metadata_helper.timecode == expected
