from __future__ import annotations

from typing import TYPE_CHECKING

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import ChromaDecoder, FieldOrder, VideoSystem

if TYPE_CHECKING:
    import argparse

    from tbc_video_export.config import Config
    from tbc_video_export.config.profile import ProfileFilter


class TypeVideoSystem:
    """Return ChromaDecoder value if it exists."""

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self._parser = parser

    def __call__(self, value: str) -> VideoSystem:  # noqa: D102
        try:
            return VideoSystem[value.replace("-", "_").upper()]
        except KeyError:
            self._parser.error(
                f"argument --video-system: invalid VideoSystem value: '{value}', "
                f"check --help for available options."
            )


class TypeFieldOrder:
    """Return FieldOrder value if it exists."""

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self._parser = parser

    def __call__(self, value: str) -> FieldOrder:  # noqa: D102
        try:
            return FieldOrder[value.upper()]
        except KeyError:
            self._parser.error(
                f"argument --field-order: invalid FieldOrder value: '{value}', "
                f"check --help for available options."
            )


class TypeAdditionalFilter:
    """Return ProfileFilter if it exists."""

    def __init__(self, config: Config) -> None:
        self._config = config

    def __call__(self, value: str) -> ProfileFilter:  # noqa: D102
        profile = next(
            (
                profile
                for profile in self._config.filter_profiles
                if profile.name == value
            ),
            None,
        )

        if profile is None:
            raise exceptions.InvalidFilterProfileError(
                f"Could not find filter profile '{value}'. See --list-profiles."
            )

        # add to config
        self._config.add_additional_filter_profile(profile)
        return profile


class TypeChromaDecoder:
    """Return ChromaDecoder value if it exists."""

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self._parser = parser

    def __call__(self, value: str) -> ChromaDecoder:  # noqa: D102
        try:
            return ChromaDecoder[value.upper()]
        except KeyError:
            self._parser.error(
                f"argument --chroma-decoder: invalid ChromaDecoder value: '{value}', "
                f"check --help for available options."
            )
