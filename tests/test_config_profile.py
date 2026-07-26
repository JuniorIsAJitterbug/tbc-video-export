from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tbc_video_export.common import exceptions
from tbc_video_export.files import ConfigFile
from tbc_video_export.opts import opts_parser

if TYPE_CHECKING:
    from pytest_mock import MockFixture

    from tbc_video_export.config.json import JsonConfig


class TestProfile:
    """Tests for config profile."""

    @pytest.fixture(autouse=True)
    def set_module(self) -> None:
        self.module = "tbc_video_export.files.config_file.DEFAULT_CONFIG"

    def test_profile_counts(self) -> None:
        config = ConfigFile()
        assert len(config.profiles) >= 0
        assert len(config.audio_profiles) >= 0
        assert len(config.filter_profiles) >= 0

    def test_invalid_config_profiles(self, mocker: MockFixture) -> None:
        invalid_config: JsonConfig = {}  # pyrefly: ignore [bad-typed-dict-key]

        mocker.patch(self.module, invalid_config)

        with pytest.raises(exceptions.InvalidProfileError):
            ConfigFile()

    def test_invalid_config_audio_profiles(self, mocker: MockFixture) -> None:
        invalid_config: JsonConfig = {"profiles": []}  # pyrefly: ignore [bad-typed-dict-key]
        mocker.patch(self.module, invalid_config)

        config = ConfigFile()

        with pytest.raises(exceptions.InvalidAudioProfileError):
            _ = config.audio_profiles

    def test_invalid_config_filter_profiles(self, mocker: MockFixture) -> None:
        invalid_config: JsonConfig = {"profiles": []}  # pyrefly: ignore [bad-typed-dict-key]
        mocker.patch(self.module, invalid_config)

        config = ConfigFile()

        with pytest.raises(exceptions.InvalidFilterProfileError):
            _ = config.filter_profiles

    def test_profile_names(self, mocker: MockFixture) -> None:
        json_config: JsonConfig = {
            "profiles": [
                {
                    "name": "test1",
                    "video_profile": "video_profile_test",
                },
                {
                    "name": "test2",
                    "video_profile": "video_profile_test",
                },
            ],
            "video_profiles": [
                {
                    "name": "video_profile_test",
                    "description": "Video Profile Test",
                    "codec": "ffv1",
                    "video_format": "yuv444p16le",
                    "container": "mkv",
                }
            ],
            "audio_profiles": [],
            "filter_profiles": [],
        }

        mocker.patch(self.module, json_config)
        config = ConfigFile()
        assert config.get_profile_names() == ["test1", "test2"]

    def test_default_profile(self, mocker: MockFixture) -> None:
        json_config: JsonConfig = {
            "profiles": [
                {
                    "name": "test1",
                    "video_profile": "video_profile_test",
                },
                {
                    "name": "test2",
                    "default": True,
                    "video_profile": "video_profile_test",
                },
            ],
            "video_profiles": [
                {
                    "name": "video_profile_test",
                    "description": "Video Profile Test",
                    "codec": "ffv1",
                    "video_format": "yuv444p16le",
                    "container": "mkv",
                }
            ],
            "audio_profiles": [],
            "filter_profiles": [],
        }

        mocker.patch(self.module, json_config)
        config = ConfigFile()
        assert config.get_default_profile().name == "test2"

    def test_single_video_profile(self, mocker: MockFixture) -> None:
        json_config: JsonConfig = {
            "profiles": [
                {
                    "name": "test1",
                    "video_profile": "video_profile_test",
                },
            ],
            "video_profiles": [
                {
                    "name": "video_profile_test",
                    "description": "Video Profile Test",
                    "codec": "ffv1",
                    "video_format": "yuv444p16le",
                    "container": "mkv",
                }
            ],
            "audio_profiles": [],
            "filter_profiles": [],
        }

        mocker.patch(self.module, json_config)
        config = ConfigFile()

        video_profiles = config.get_video_profiles_for_profile("test1")
        assert len(video_profiles) == 1
        video_profile = video_profiles[0]
        assert video_profile.name == "video_profile_test"

    def test_multiple_video_profile(self, mocker: MockFixture) -> None:
        json_config: JsonConfig = {
            "profiles": [
                {
                    "name": "test1",
                    "video_profile": [
                        "video_profile_test1",
                        "video_profile_test2",
                        "video_profile_test3",
                    ],
                },
            ],
            "video_profiles": [
                {
                    "name": "video_profile_test1",
                    "description": "Video Profile Test 1",
                    "codec": "ffv1",
                    "video_format": "yuv444p16le",
                    "container": "mkv",
                },
                {
                    "name": "video_profile_test2",
                    "description": "Video Profile Test 2",
                    "codec": "ffv1",
                    "video_format": "yuv444p16le",
                    "container": "mkv",
                },
                {
                    "name": "video_profile_test3",
                    "description": "Video Profile Test 3",
                    "codec": "ffv1",
                    "video_format": "yuv444p16le",
                    "container": "mkv",
                },
            ],
            "audio_profiles": [],
            "filter_profiles": [],
        }

        mocker.patch(self.module, json_config)
        config = ConfigFile()

        video_profiles = config.get_video_profiles_for_profile("test1")
        assert len(video_profiles) == 3
        video_profile = video_profiles[2]
        assert video_profile.name == "video_profile_test3"

    def test_config_file_opt(self) -> None:
        pre_opts, _ = opts_parser.parse_pre_opts(
            [
                "--config-file",
                "tests/files/test_profile.json",
            ]
        )

        config = ConfigFile(pre_opts.config_file)
        assert config.get_default_profile().name == "ffv1_test"

        pre_opts, _ = opts_parser.parse_pre_opts(
            [
                "--config-file",
                "tests/files/invalid.json",
            ]
        )

        with pytest.raises(exceptions.InvalidProfileError):
            config = ConfigFile(pre_opts.config_file)
