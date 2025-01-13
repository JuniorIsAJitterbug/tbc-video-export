from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from tbc_video_export.common import consts, exceptions
from tbc_video_export.common.utils import files
from tbc_video_export.config.default import DEFAULT_CONFIG
from tbc_video_export.config.profile import (
    Profile,
    ProfileAudio,
    ProfileFilter,
    ProfileVideo,
)

if TYPE_CHECKING:
    from tbc_video_export.common.enums import (
        HardwareAccelType,
        VideoSystem,
    )
    from tbc_video_export.config.json import JsonConfig


class Config:
    """Profile helper.

    Uses a default json if not given a valid json file.
    Currently only contains profiles but can be extended to contain other
    program configuration.
    """

    def __init__(self, config_file: str | None = None) -> None:
        self._data: JsonConfig
        self._additional_filters: list[str] = []

        # attempt loading user file if set, or exported file from default location
        file_name = (
            Path(config_file) if config_file is not None else self.get_config_file()
        )

        if file_name is not None:
            try:
                with Path.open(file_name, mode="r", encoding="utf-8") as file:
                    self._data = json.load(file)
            except (FileNotFoundError, PermissionError, json.JSONDecodeError) as e:
                raise exceptions.InvalidProfileError(str(e), file_name) from e

        # use default config
        # not going to check for decode errors on embedded json
        if not getattr(self, "_data", False):
            self._data = DEFAULT_CONFIG

        self.profiles: list[Profile] = []

        try:
            for json_profile in self._data["profiles"]:
                for profile in self._generate_profile(json_profile["name"]):
                    self.profiles.append(profile)
        except KeyError as e:
            raise exceptions.InvalidProfileError(
                "Configuration file missing required fields.", self.get_config_file()
            ) from e

    @cached_property
    def audio_profiles(self) -> list[ProfileAudio]:
        """Return list of available audio profiles."""
        try:
            return [ProfileAudio(p) for p in self._data["audio_profiles"]]
        except KeyError as e:
            raise exceptions.InvalidAudioProfileError(
                "Could not load audio profiles.", self.get_config_file()
            ) from e

    @cached_property
    def filter_profiles(self) -> list[ProfileFilter]:
        """Return list of available filter profiles."""
        try:
            return [ProfileFilter(p) for p in self._data["filter_profiles"]]
        except KeyError as e:
            raise exceptions.InvalidFilterProfileError(
                "Could not load filter profiles.", self.get_config_file()
            ) from e

    @property
    def additional_filters(self) -> list[str]:
        """Return list of additional filter profiles."""
        return self._additional_filters

    def add_additional_filter(self, filter_name: str) -> None:
        """Append a filter to use."""
        self._additional_filters.append(filter_name)

    def get_profile(self, profile_filter: GetProfileFilter) -> Profile:
        """Return a profile from a filter."""
        try:
            profile = next(
                (profile for profile in self.profiles if profile_filter.match(profile)),
                None,
            )

            if profile is None:
                err_msg = f"Could not find profile {profile_filter.name}."

                if profile_filter.hwaccel_type is not None:
                    err_msg += f" ({profile_filter.hwaccel_type.value})"

                raise exceptions.InvalidProfileError(err_msg)

            return profile
        except KeyError as e:
            raise exceptions.InvalidProfileError(
                "Could not load profiles.", self.get_config_file()
            ) from e
        except exceptions.InvalidProfileError as e:
            raise exceptions.InvalidProfileError(str(e), self.get_config_file()) from e

    def get_profile_names(self) -> list[str]:
        """Return a list of unique profile names for a given profile type."""
        return list(dict.fromkeys(profile.name for profile in self.profiles))

    def get_default_profile(self) -> Profile:
        """Return the first default profile."""
        profile = next(
            (profile for profile in self.profiles if profile.is_default), None
        )

        if profile is None:
            raise exceptions.InvalidProfileError(
                "Unable to find default profile.", self.get_config_file()
            )

        return profile

    def get_video_profiles_for_profile(self, profile_name: str) -> list[ProfileVideo]:
        """Return list of video profiles for a given profile."""
        video_profiles: list[ProfileVideo] = []

        for profile in self.profiles:
            if profile.name == profile_name:
                video_profiles.append(profile.video_profile)

        return video_profiles

    def get_audio_profile_names(self) -> list[str]:
        """Return all audio profile names.."""
        return [audio_profile.name for audio_profile in self.audio_profiles]

    def get_filter_profile(self, filter_name: str) -> ProfileFilter:
        """Return filter profile from filter name."""
        filter_profile = next(
            (
                filter_profile
                for filter_profile in self.filter_profiles
                if filter_profile.name == filter_name
            ),
            None,
        )

        if filter_profile is None:
            raise exceptions.InvalidProfileError(
                f"Unable to find filter profile {filter_name}.",
                self.get_config_file(),
            )

        return filter_profile

    @staticmethod
    def dump_default_config(file_name: Path) -> None:
        """Attempt to dump the default config to a json file."""
        try:
            if Path(file_name).is_file():
                raise exceptions.FileIOError(
                    f"Unable to create {file_name}, already exists"
                )

            with Path.open(file_name, "w", encoding="utf-8") as file:
                json.dump(DEFAULT_CONFIG, file, ensure_ascii=False, indent=4)
        except PermissionError as e:
            raise exceptions.FileIOError(
                f"Permission error writing {file_name}."
            ) from e

        logging.getLogger("console").info(f"default config dumped to {file_name}")

    @staticmethod
    def get_config_file() -> Path | None:
        """Return name of json file to load profiles from.

        Returns None if json file does not exist in PATH or script dir.
        """
        file_name_stock = consts.EXPORT_CONFIG_FILE_NAME

        # check current dir
        if (path := Path(file_name_stock)).is_file():
            return path.absolute()

        # check binary dir
        if (
            path := Path(files.get_runtime_directory().joinpath(file_name_stock))
        ).is_file():
            return path.absolute()

        return None

    def get_profile_filters(self, profile: Profile) -> tuple[list[str], list[str]]:
        """Adds profile filters to list opts."""
        video_filters: list[str] = []
        other_filters: list[str] = []

        filter_profiles = profile.filter_profiles

        # populate filters
        for vf in (profile.video_filter for profile in filter_profiles):
            if vf is not None:
                video_filters.append(vf)

        for of in (profile.other_filter for profile in filter_profiles):
            if of is not None:
                other_filters.append(of)

        # add additional video profile filters
        for name in profile.video_profile.filter_profiles_additions:
            self._add_filter(name, video_filters, other_filters)

        # add additional opt filters
        for name in self._additional_filters:
            self._add_filter(name, video_filters, other_filters)

        return video_filters, other_filters

    def _add_filter(
        self, filter_name: str, video_filters: list[str], other_filters: list[str]
    ) -> None:
        """Add ProfileFilter to lists from name."""
        filter_profile = self.get_filter_profile(filter_name)

        if (vf := filter_profile.video_filter) is not None:
            video_filters.append(vf)

        if (of := filter_profile.other_filter) is not None:
            other_filters.append(of)

    def _generate_profile(self, profile_name: str) -> list[Profile]:
        try:
            profile_data = next(
                profile
                for profile in self._data["profiles"]
                if profile["name"] == profile_name
            )

            # get video profile(s) for profile
            if isinstance(profile_data["video_profile"], list):
                video_profiles = [
                    ProfileVideo(profile_data, json_video_profile)
                    for json_video_profile in self._data["video_profiles"]
                    for video_profile_name in profile_data["video_profile"]
                    if json_video_profile["name"] == video_profile_name
                ]
            else:
                video_profiles = [
                    next(
                        ProfileVideo(profile_data, json_video_profile)
                        for json_video_profile in self._data["video_profiles"]
                        if json_video_profile["name"] == profile_data["video_profile"]
                    )
                ]

            # get audio profile for profile
            audio_profile = next(
                (
                    ProfileAudio(json_audio_profile)
                    for json_audio_profile in self._data["audio_profiles"]
                    if "audio_profile" in profile_data
                    and json_audio_profile["name"] == profile_data["audio_profile"]
                ),
                None,
            )

            # get filter profile(s) for profile
            filter_profiles = [
                ProfileFilter(json_filter_profile)
                for json_filter_profile in self._data["filter_profiles"]
                if "filter_profiles" in profile_data
                for filter_profile_name in profile_data["filter_profiles"]
                if json_filter_profile["name"] == filter_profile_name
            ]

            profiles: list[Profile] = []

            for video_profile in video_profiles:
                profile = Profile(
                    profile_data, video_profile, audio_profile, filter_profiles
                )

                # set profile overrides
                if override := video_profile.filter_profiles:
                    profile.filter_profiles = [
                        ProfileFilter(json_filter_profile)
                        for json_filter_profile in self._data["filter_profiles"]
                        for filter_profile_name in override
                        if json_filter_profile["name"] == filter_profile_name
                    ]

                profiles.append(profile)

            return profiles
        except KeyError as e:
            raise exceptions.InvalidProfileError(
                "Unable to generate profiles.", self.get_config_file()
            ) from e


@dataclass
class GetProfileFilter:
    """Container class for get profile filter params."""

    name: str
    hwaccel_type: HardwareAccelType | None = None
    video_system: VideoSystem | None = None

    def match(self, profile: Profile) -> bool:
        """Returns true if profile matches filter."""
        video_profile = profile.video_profile

        if profile.name != self.name:
            return False

        if (
            self.hwaccel_type is not None
            and video_profile.hardware_accel is not self.hwaccel_type
        ):
            return False

        return not (
            (self.video_system is not None and video_profile.video_system is not None)
            and video_profile.video_system is not self.video_system
        )
