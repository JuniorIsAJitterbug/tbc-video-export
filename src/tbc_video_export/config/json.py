from __future__ import annotations

from typing import TypedDict


class JsonConfig(TypedDict):
    """Raw mapping of config from JSON."""

    profiles: list[JsonProfile]
    video_profiles: list[JsonSubProfileVideo]
    audio_profiles: list[JsonSubProfileAudio]
    filter_profiles: list[JsonPSubrofileFilter]


class JsonProfile(TypedDict):
    """Raw mapping of profile from JSON."""

    name: str
    type: str | None
    default: bool | None
    include_vbi: bool | None
    video_profile: str
    video_format: str
    audio_profile: str | None
    filter_profiles: list[str] | None


class JsonSubProfile(TypedDict):
    """Raw mapping of subprofile from JSON."""

    name: str
    description: str


class JsonSubProfileVideo(JsonSubProfile):
    """Raw mapping of video subprofile from JSON."""

    container: str
    output_format: str | None
    codec: str
    opts: list[str | int] | None


class JsonSubProfileAudio(JsonSubProfile):
    """Raw mapping of audio subprofile from JSON."""

    codec: str
    opts: list[str | int] | None


class JsonPSubrofileFilter(JsonSubProfile):
    """Raw mapping of filter subprofile from JSON."""

    video_filter: str | None
    other_filter: str | None
