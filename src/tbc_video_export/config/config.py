from __future__ import annotations

import json
import logging
from contextlib import suppress
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from tbc_video_export.common import consts, exceptions
from tbc_video_export.common.utils import FlatList, files
from tbc_video_export.config.default import DEFAULT_CONFIG
from tbc_video_export.config.profile import (
    Profile,
    ProfileAudio,
    ProfileFilter,
    ProfileVideo,
)

if TYPE_CHECKING:
    from tbc_video_export.common.enums import ProfileType
    from tbc_video_export.config.json import JsonConfig, JsonProfile


class Config:
    """Profile helper.

    Uses a default json if not given a valid json file.
    Currently only contains profiles but can be extended to contain other
    program configuration.
    """

    def __init__(self) -> None:
        self._data: JsonConfig
        self._additional_filters: list[ProfileFilter] = []

        with suppress(FileNotFoundError, PermissionError, json.JSONDecodeError):
            # attempt to load the file if it exists
            if (file_name := self.get_config_file()) is not None:
                with Path.open(file_name, mode="r", encoding="utf-8") as file:
                    self._data = json.load(file)

        # use default config
        # not going to check for decode errors on embedded json
        if not getattr(self, "_data", False):
            self._data = DEFAULT_CONFIG

        self._profiles: list[Profile] = self._generate_profiles()

    @property
    def profiles(self) -> list[Profile]:
        """Return list of available profiles."""
        return self._profiles

    @cached_property
    def video_profiles(self) -> list[ProfileVideo]:
        """Return list of available video profiles."""
        try:
            return [ProfileVideo(p) for p in self._data["video_profiles"]]
        except KeyError as e:
            raise exceptions.InvalidProfileError(
                "Could not read video profiles.", self.get_config_file()
            ) from e

    @cached_property
    def audio_profiles(self) -> list[ProfileAudio]:
        """Return list of available audio profiles."""
        try:
            return [ProfileAudio(p) for p in self._data["audio_profiles"]]
        except KeyError as e:
            raise exceptions.InvalidProfileError(
                "Could not load audio profiles.", self.get_config_file()
            ) from e

    @cached_property
    def filter_profiles(self) -> list[ProfileFilter]:
        """Return list of available filter profiles."""
        try:
            return [ProfileFilter(p) for p in self._data["filter_profiles"]]
        except KeyError as e:
            raise exceptions.InvalidProfileError(
                "Could not load filter profiles.", self.get_config_file()
            ) from e

    @property
    def additional_filters(self) -> list[ProfileFilter]:
        """Return list of additional filter profiles."""
        return self._additional_filters

    def get_profile(self, name: str) -> Profile:
        """Return a profile from a name."""
        return next(p for p in self.profiles if p.name == name)

    def get_profile_names(self, profile_type: ProfileType) -> list[str]:
        """Return a list of profile names for a given profile type."""
        return [p.name for p in self._get_profiles_from_type(profile_type)]

    def get_default_profile(self, profile_type: ProfileType) -> Profile:
        """Return the first default profile for a given profile type."""
        profiles = self._get_profiles_from_type(profile_type)

        if profile := next((p for p in profiles if p.is_default), False):
            profile = profiles[0]
        else:
            raise exceptions.InvalidProfileError(
                "Unable to find default profile.", self.get_config_file()
            )

        return self.get_profile(profile.name)

    def add_additional_filter_profile(self, profile: ProfileFilter) -> None:
        """Add an additional filter to be used when encoding."""
        self._additional_filters.append(profile)

        # regenerate profiles on filter add
        self._profiles = self._generate_profiles()

    @staticmethod
    def get_subprofile_descriptions(profile: Profile, show_format: bool) -> str:
        """Return a comma separated list of sub profile descriptions for a profile."""
        # whether to append the profile video format to the profile name
        sub_profiles = FlatList(
            f"{profile.video_profile.description} {profile.video_format}"
            if show_format
            else profile.video_profile.description
        )

        if profile.audio_profile is not None:
            sub_profiles.append(profile.audio_profile.description)

        if profile.filter_profiles is not None:
            sub_profiles.append(
                profile.description for profile in profile.filter_profiles
            )

        return ", ".join(sub_profiles.data)

    @staticmethod
    def dump_default_config(file_name: Path) -> None:
        """Attempt to dump the default config to a json file."""
        try:
            if Path(file_name).is_file():
                raise exceptions.FileIOError(
                    f"Unable to create {file_name}, already exists"
                )

            # remove

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

    def _generate_profiles(self) -> list[Profile]:
        try:
            return [
                Profile(
                    p,
                    self._get_video_profile(p["name"]),
                    self._get_audio_profile(p["name"]),
                    self._get_filter_profiles(p["name"]) + self._additional_filters,
                )
                for p in self._data["profiles"]
            ]
        except KeyError as e:
            raise exceptions.InvalidProfileError(
                "Could not load profiles.", self.get_config_file()
            ) from e
        except exceptions.InvalidProfileError as e:
            raise exceptions.InvalidProfileError(str(e), self.get_config_file()) from e

    def _get_profiles_from_type(self, profile_type: ProfileType) -> list[Profile]:
        """Return a list of profiles for a given type."""
        return [p for p in self.profiles if p.profile_type is profile_type]

    def _get_raw_profile_data(self, profile_name: str) -> JsonProfile:
        try:
            return next(
                profile
                for profile in self._data["profiles"]
                if profile["name"] == profile_name
            )
        except KeyError as e:
            raise exceptions.InvalidProfileError(
                "Could not load profiles.", self.get_config_file()
            ) from e

    def _get_video_profile(self, profile_name: str) -> ProfileVideo:
        """Return a video profile for a given profile name."""
        profile_data = self._get_raw_profile_data(profile_name)
        video_profile_name = profile_data["video_profile"]

        # return first video profile matching name
        if (
            video_profile := next(
                (
                    profile
                    for profile in self.video_profiles
                    if profile.name.lower() == video_profile_name.lower()
                ),
                None,
            )
        ) is None:
            raise exceptions.InvalidProfileError(
                f"Unable to find video profile {video_profile_name} "
                f"for profile {profile_name}.",
                self.get_config_file(),
            )

        return video_profile

    def _get_audio_profile(self, profile_name: str) -> ProfileAudio | None:
        """Return a audio profile for a given profile name."""
        profile_data = self._get_raw_profile_data(profile_name)

        # no profile given
        if (audio_profile_name := profile_data["audio_profile"]) is None:
            return None

        # return first audio profile matching name
        if (
            audio_profile := next(
                (
                    profile
                    for profile in self.audio_profiles
                    if profile.name.lower() == audio_profile_name.lower()
                ),
                None,
            )
        ) is None:
            raise exceptions.InvalidProfileError(
                f"Unable to find audio profile {audio_profile_name} "
                f"for profile {profile_name}.",
                self.get_config_file(),
            )

        return audio_profile

    def _get_filter_profiles(self, profile_name: str) -> list[ProfileFilter]:
        """Return all filter profiles for a given profile name."""
        profile_data = self._get_raw_profile_data(profile_name)
        filter_names = profile_data["filter_profiles"]

        # no filter profiles for profile
        if filter_names is None:
            return []

        filter_profiles = [
            profile
            for name in filter_names
            for profile in self.filter_profiles
            if profile.name.lower() == name.lower()
        ]

        # ensure we found all the profiles
        if len(filter_profiles) < len(filter_names):
            raise exceptions.InvalidProfileError(
                f"Unable to find filter profile(s) for profile {profile_name}.",
                self.get_config_file(),
            )

        return filter_profiles
