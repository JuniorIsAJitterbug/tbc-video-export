from __future__ import annotations

from typing import TYPE_CHECKING

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import ProfileVideoType, VideoSystem
from tbc_video_export.common.utils import FlatList, ansi

if TYPE_CHECKING:
    from tbc_video_export.config.json import (
        JsonProfile,
        JsonSubProfile,
        JsonSubProfileAudio,
        JsonSubProfileFilter,
        JsonSubProfileVideo,
    )


class Profile:
    """Holds profile data."""

    def __init__(
        self,
        profile: JsonProfile,
        video_profile: ProfileVideo,
        audio_profile: ProfileAudio | None,
        filter_profiles: list[ProfileFilter],
    ) -> None:
        self._profile = profile
        self.video_profile = video_profile
        self.audio_profile = audio_profile
        self._filter_profiles = filter_profiles

    @property
    def name(self) -> str:
        """Return profile name."""
        return self._profile["name"]

    @property
    def include_vbi(self) -> bool:
        """Returns True if the profile contains include_vbi as True."""
        return self._profile["include_vbi"] if "include_vbi" in self._profile else False

    @property
    def is_default(self) -> bool:
        """Returns True if the profile is flagged as default."""
        return self._profile["default"] if "default" in self._profile else False

    @property
    def filter_profiles(self) -> list[ProfileFilter]:
        """Return filter profiles."""
        return self._filter_profiles

    @filter_profiles.setter
    def filter_profiles(self, filter_profiles: list[ProfileFilter]) -> None:
        """Set filter profiles."""
        self._filter_profiles = filter_profiles

    def __str__(self) -> str:  # noqa: D105
        data = f"--{self.name} {'(default)' if self.is_default else ''}\n"

        data += str(self.video_profile)

        if self.audio_profile is not None:
            data += str(self.audio_profile)

        if self.include_vbi:
            data += f"  {ansi.dim('Include VBI')}\t{self.include_vbi}\n"

        return data


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
        super().__init__(profile)
        self._profile = profile
        self._video_format = self._profile["video_format"]

    @property
    def container(self) -> str:
        """Return the output file container."""
        return self._profile["container"]

    @property
    def output_format(self) -> str | None:
        """Return the output format."""
        return (
            self._profile["output_format"] if "output_format" in self._profile else None
        )

    @property
    def codec(self) -> str:
        """Return the video codec."""
        return self._profile["codec"]

    @property
    def opts(self) -> FlatList | None:
        """Return the video opts if they exist."""
        return FlatList(self._profile["opts"]) if "opts" in self._profile else None

    @property
    def video_format(self) -> str:
        """Return the video format."""
        return self._video_format

    @video_format.setter
    def video_format(self, video_format: str) -> None:
        """Set video format."""
        self._video_format = video_format

    @property
    def filter_profiles_additions(self) -> list[str]:
        """Return the additional filters if they exists."""
        return (
            self._profile["filter_profiles_additions"]
            if "filter_profiles_additions" in self._profile
            else []
        )

    @property
    def filter_profiles_override(self) -> list[str] | None:
        """Return the filters to override parent filters if they exists."""
        return (
            self._profile["filter_profiles_override"]
            if "filter_profiles_override" in self._profile
            else None
        )

    @property
    def profile_type(self) -> ProfileVideoType | None:
        """Return the video profile type."""
        try:
            return ProfileVideoType(self._profile["type"])
        except (KeyError, ValueError):
            return None

    @property
    def video_system(self) -> VideoSystem | None:
        """Return the video system filter."""
        if "video_system" in self._profile:
            try:
                return VideoSystem(self._profile["video_system"])
            except (KeyError, ValueError) as e:
                raise exceptions.InvalidProfileError(
                    f"Video profile {self._profile['name']} contains unknown "
                    f"video_system."
                ) from e

        return None

    def __str__(self) -> str:  # noqa: D105
        data = "  "
        data += (
            f"--{ansi.bold(self.profile_type.value)} "
            if self.profile_type is not None
            else ""
        )

        if data == "  ":
            data += "default"

        data += "\n"
        data += f"    {ansi.dim('Description')}\t{self.description} [{self.name}]\n"
        data += f"    {ansi.dim('Video Codec')}\t{self.codec}\n"

        if self.opts is not None:
            data += f"    {ansi.dim('Video Opts')}\t{self.opts}\n"

        data += f"    {ansi.dim('Format')}\t{self.video_format}\n"
        data += f"    {ansi.dim('Container')}\t{self.container}"

        if self.output_format is not None:
            data += f" ({self.output_format})"

        data += "\n"

        if self.filter_profiles_additions or self.filter_profiles_override is not None:
            data += f"    {ansi.dim('Filters')}\n"
            if self.filter_profiles_additions:
                data += (
                    f"      {ansi.dim('Additions')}\t"
                    f"{', '.join(self.filter_profiles_additions)}\n"
                )

            if self.filter_profiles_override is not None:
                data += (
                    f"      {ansi.dim('Override')}\t"
                    f"{', '.join(self.filter_profiles_override)}\n"
                )

        if self.video_system is not None:
            data += f"    {ansi.dim('System')}\t{self.video_system}\n"

        # data += "\n"

        return data


class ProfileAudio(SubProfile):
    """Holds FFmpeg audio profile."""

    def __init__(self, profile: JsonSubProfileAudio) -> None:
        super().__init__(profile)
        self._profile = profile

    @property
    def codec(self) -> str:
        """Return the audio codec."""
        return self._profile["codec"]

    @property
    def opts(self) -> FlatList:
        """Return the audio opts if they exist."""
        return (
            FlatList(self._profile["opts"]) if "opts" in self._profile else FlatList()
        )

    def __str__(self) -> str:  # noqa: D105
        data = f"  {ansi.dim('Audio Codec:')}\t{self.codec}\n"
        if self.opts:
            data += f"  {ansi.dim('Audio Opts')}\t{self.opts}\n"

        return data


class ProfileFilter(SubProfile):
    """Holds FFmpeg filter profile."""

    def __init__(self, profile: JsonSubProfileFilter) -> None:
        super().__init__(profile)
        self._profile = profile

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
