from __future__ import annotations

import json
from pathlib import Path

import pytest
from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import VideoSystem
from tbc_video_export.common.tbc_json_helper import TBCJsonHelper


class TestTBCJson:
    """Tests for tbc json helper."""

    def test_open_json(self) -> None:  # noqa: D102
        with pytest.raises(exceptions.TBCError) as e:
            TBCJsonHelper(Path("tests/files/non_existent_file"))

            assert e.value == "TBC json not found (tests/files/non_existent_file)."

        with pytest.raises(json.JSONDecodeError) as e:
            TBCJsonHelper(None, "blah")

            assert e.value == "Unable to parse TBC json (tests/files/invalid.json)."

        tbc_json = TBCJsonHelper(Path("tests/files/pal_svideo.tbc.json"))
        assert str(tbc_json.file_name) == "tests/files/pal_svideo.tbc.json"

    def test_video_system(self) -> None:  # noqa: D102
        json_data = '{"videoParameters":{"system":"PAL"}}'
        tbc_json = TBCJsonHelper(None, json_data)
        assert tbc_json.video_system == VideoSystem.PAL

        json_data = '{"videoParameters":{"system":"PAL-M"}}'
        tbc_json = TBCJsonHelper(None, json_data)
        assert tbc_json.video_system == VideoSystem.PAL_M

        json_data = '{"videoParameters":{"system":"NTSC"}}'
        tbc_json = TBCJsonHelper(None, json_data)
        assert tbc_json.video_system == VideoSystem.NTSC

        with pytest.raises(exceptions.TBCError) as e:
            json_data = '{"videoParameters":{"system":"INVALID"}}'
            tbc_json = TBCJsonHelper(None, json_data)
            _ = tbc_json.video_system
            assert e.value == "Unable to read video system from TBC json."

        with pytest.raises(exceptions.TBCError) as e:
            json_data = '{"videoParameters":{}}'
            tbc_json = TBCJsonHelper(None, json_data)
            _ = tbc_json.video_system
            assert e.value == "System unsupported (INVALID)."

    def test_field_count(self) -> None:  # noqa: D102
        tbc_json = TBCJsonHelper(Path("tests/files/pal_svideo.tbc.json"))
        assert tbc_json.field_count == 2
        assert tbc_json.frame_count == 1

    def test_check_widescreen(self) -> None:  # noqa: D102
        json_data = '{"videoParameters":{}}'
        tbc_json = TBCJsonHelper(None, json_data)
        assert not tbc_json.is_widescreen

        json_data = '{"videoParameters":{"isWidescreen":false}}'
        tbc_json = TBCJsonHelper(None, json_data)
        assert not tbc_json.is_widescreen

        json_data = '{"videoParameters":{"isWidescreen":true}}'
        tbc_json = TBCJsonHelper(None, json_data)
        assert tbc_json.is_widescreen

    vitc_data = [
        ("[1,8,7,8,1,0,1,0]", "NTSC", "01:01:07:01"),
        ("[0,0,0,0,0,0,0,0]", "PAL", "00:00:00:00"),
        ("[10,0,0,0,0,0,0,0]", "PAL", "00:00:00:00"),
        ("[1,2,3,4,6,5,3,2]", "PAL", "23:56:43:21"),
        ("[1,4,0,0,0,0,0,0]", "NTSC", "00:00:00;01"),
    ]

    @pytest.mark.parametrize("vitc_data,system,expected", vitc_data)
    def test_vitc(self, vitc_data: str, system: str, expected: str) -> None:  # noqa: D102
        json_data = (
            '{"videoParameters":{"system":"'
            + system
            + '"},"fields":[{"vitc":{"vitcData":'
            + vitc_data
            + "}}]}"
        )  # noqa: E501
        tbc_json = TBCJsonHelper(None, json_data)
        assert tbc_json.timecode == expected
