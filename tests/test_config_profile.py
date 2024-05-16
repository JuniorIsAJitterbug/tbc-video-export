from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from tbc_video_export.common import exceptions
from tbc_video_export.config.config import Config

if TYPE_CHECKING:
    from pytest_mock import MockFixture
    from tbc_video_export.config.json import JsonConfig


class TestProfile:
    """Tests for config profile."""

    @pytest.fixture(autouse=True)
    def set_module(self) -> None:  # noqa: D102
        self.module = "tbc_video_export.config"

    def test_profile_counts(self) -> None:  # noqa: D102
        config = Config()
        assert len(config.profiles) >= 0
        assert len(config.audio_profiles) >= 0
        assert len(config.filter_profiles) >= 0

    def test_invalid_config_profiles(self, mocker: MockFixture) -> None:  # noqa: D102
        invalid_config: JsonConfig = {}  # type: ignore

        mocker.patch(f"{self.module}.config.DEFAULT_CONFIG", invalid_config)

        with pytest.raises(exceptions.InvalidProfileError):
            Config()

    def test_invalid_config_audio_profiles(  # noqa: D102
        self, mocker: MockFixture
    ) -> None:
        invalid_config: JsonConfig = {"profiles": []}  # type: ignore
        mocker.patch(f"{self.module}.config.DEFAULT_CONFIG", invalid_config)

        with pytest.raises(exceptions.InvalidAudioProfileError):
            config = Config()
            _ = config.audio_profiles

    def test_invalid_config_filter_profiles(  # noqa: D102
        self, mocker: MockFixture
    ) -> None:
        invalid_config: JsonConfig = {"profiles": []}  # type: ignore
        mocker.patch(f"{self.module}.config.DEFAULT_CONFIG", invalid_config)

        with pytest.raises(exceptions.InvalidFilterProfileError):
            config = Config()
            _ = config.filter_profiles

    def test_profile_names(self, mocker: MockFixture) -> None:  # noqa: D102
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

        mocker.patch(f"{self.module}.config.DEFAULT_CONFIG", json_config)
        config = Config()
        assert config.get_profile_names() == ["test1", "test2"]

    def test_default_profile(self, mocker: MockFixture) -> None:  # noqa: D102
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

        mocker.patch(f"{self.module}.config.DEFAULT_CONFIG", json_config)
        config = Config()
        assert config.get_default_profile().name == "test2"

    def test_single_video_profile(self, mocker: MockFixture) -> None:  # noqa: D102
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

        mocker.patch(f"{self.module}.config.DEFAULT_CONFIG", json_config)
        config = Config()

        video_profiles = config.get_video_profiles_for_profile("test1")
        assert len(video_profiles) == 1
        video_profile = video_profiles[0]
        assert video_profile.name == "video_profile_test"

    def test_multiple_video_profile(self, mocker: MockFixture) -> None:  # noqa: D102
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

        mocker.patch(f"{self.module}.config.DEFAULT_CONFIG", json_config)
        config = Config()

        video_profiles = config.get_video_profiles_for_profile("test1")
        assert len(video_profiles) == 3
        video_profile = video_profiles[2]
        assert video_profile.name == "video_profile_test3"
