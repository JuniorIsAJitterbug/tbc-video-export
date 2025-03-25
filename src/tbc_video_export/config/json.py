from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from typing_extensions import NotRequired


class JsonConfig(TypedDict):
    """Raw mapping of config from JSON."""

    profiles: list[JsonProfile]
    video_profiles: list[JsonSubProfileVideo]
    audio_profiles: list[JsonSubProfileAudio]
    filter_profiles: list[JsonSubProfileFilter]


class JsonProfile(TypedDict):
    """Raw mapping of profile from JSON."""

    name: str
    default: NotRequired[bool]
    include_vbi: NotRequired[bool]
    video_profile: str | list[str]
    audio_profile: NotRequired[str]
    filter_profiles: NotRequired[list[str]]
    deprecated: NotRequired[bool]


class JsonSubProfile(TypedDict):
    """Raw mapping of subprofile from JSON."""

    name: str
    description: str


class JsonSupportedFormats(TypedDict):
    """Raw mapping of supported formats from JSON."""

    bitdepth: int
    format: str


class JsonSubProfileVideo(JsonSubProfile):
    """Raw mapping of video subprofile from JSON."""

    container: str
    output_format: NotRequired[str]
    codec: str
    opts: NotRequired[list[str | int]]
    video_system: NotRequired[str]
    video_format: str
    filter_profiles_additions: NotRequired[list[str]]
    filter_profiles_override: NotRequired[list[str]]
    hardware_accel: NotRequired[str]


class JsonSubProfileAudio(JsonSubProfile):
    """Raw mapping of audio subprofile from JSON."""

    codec: str
    opts: NotRequired[list[str | int]]


class JsonSubProfileFilter(JsonSubProfile):
    """Raw mapping of filter subprofile from JSON."""

    video_filter: NotRequired[str]
    other_filter: NotRequired[str]
