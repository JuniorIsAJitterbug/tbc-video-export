from __future__ import annotations

from typing import TYPE_CHECKING

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import ProfileType
from tbc_video_export.common.utils import FlatList

if TYPE_CHECKING:
    from tbc_video_export.config.json import (
        JsonProfile,
        JsonPSubrofileFilter,
        JsonSubProfile,
        JsonSubProfileAudio,
        JsonSubProfileVideo,
    )


class Profile:
    """Holds profile data."""

    def __init__(
        self,
        profile: JsonProfile,
        video_profile: ProfileVideo,
        audio_profile: ProfileAudio | None,
        filter_profiles: list[ProfileFilter] | None,
    ) -> None:
        self._profile = profile
        self.video_profile = video_profile
        self.audio_profile = audio_profile
        self.filter_profiles = filter_profiles

        if not all(
            key in self._profile for key in ("name", "video_profile", "video_format")
        ):
            raise exceptions.InvalidProfileError(
                "profile requires at least a name, video_profile and video_format"
            )

    @property
    def name(self) -> str:
        """Return profile name."""
        return self._profile["name"]

    @property
    def profile_type(self) -> ProfileType:
        """Returns profile type."""
        return (
            ProfileType[self._profile["type"].upper()]
            if "type" in self._profile and self._profile["type"] is not None
            else ProfileType.DEFAULT
        )

    @property
    def is_default(self) -> bool:
        """Returns True if the profile is flagged as default."""
        return (
            self._profile["default"]
            if "default" in self._profile and self._profile["default"] is not None
            else False
        )

    @property
    def video_format(self) -> str:
        """Return profile name."""
        return self._profile["video_format"]


class SubProfile:
    """Abstract class for subprofiles."""

    def __init__(self, profile: JsonSubProfile):
        self._profile = profile

    @property
    def name(self) -> str:
        """Return profile name."""
        return self._profile["name"]

    @property
    def description(self) -> str:
        """Return the profile description."""
        return self._profile["description"]


class ProfileVideo(SubProfile):
    """Holds FFmpeg video profile."""

    def __init__(self, profile: JsonSubProfileVideo) -> None:
        self._profile = profile

        # ensure required fields are set
        if not all(key in self._profile for key in ("name", "container", "codec")):
            raise exceptions.InvalidProfileError(
                "Video profile requires at least a name, container and codec."
            )

    @property
    def container(self) -> str:
        """Return the output file container."""
        return self._profile["container"]

    @property
    def output_format(self) -> str | None:
        """Return the output format."""
        return self._profile["output_format"]

    @property
    def codec(self) -> str:
        """Return the video codec."""
        return self._profile["codec"]

    @property
    def opts(self) -> FlatList | None:
        """Return the video opts if they exist."""
        return FlatList(self._profile["opts"])


class ProfileAudio(SubProfile):
    """Holds FFmpeg audio profile."""

    def __init__(self, profile: JsonSubProfileAudio) -> None:
        self._profile = profile

        # ensure required fields are set
        if not all(key in self._profile for key in ("name", "codec")):
            raise exceptions.InvalidProfileError(
                "Audio profile requires at least a name and codec."
            )

    @property
    def codec(self) -> str:
        """Return the audio codec."""
        return self._profile["codec"]

    @property
    def opts(self) -> FlatList | None:
        """Return the audio opts if they exist."""
        return FlatList(self._profile["opts"])


class ProfileFilter(SubProfile):
    """Holds FFmpeg filter profile."""

    def __init__(self, profile: JsonPSubrofileFilter) -> None:
        self._profile = profile

        # ensure required fields are set
        if all(key in self._profile for key in ("name")) and any(
            key in self._profile for key in ("video_filter", "audio_filter")
        ):
            raise exceptions.InvalidProfileError(
                "Filter profile requires at least a name and a filter."
            )

    @property
    def video_filter(self) -> str | None:
        """Return the video filter."""
        return self._profile.get("video_filter", None)

    @property
    def other_filter(self) -> str | None:
        """Return the other filters.

        These go after the main video filter and can contain any other type of filter.
        """
        return self._profile.get("other_filter", None)
