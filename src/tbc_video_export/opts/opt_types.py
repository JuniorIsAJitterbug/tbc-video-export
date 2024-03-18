from __future__ import annotations

from typing import TYPE_CHECKING

from tbc_video_export.common.enums import (
    ChromaDecoder,
    FieldOrder,
    ProfileVideoType,
    VideoSystem,
)

if TYPE_CHECKING:
    import argparse

    from tbc_video_export.config import Config


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

    def __call__(self, value: str) -> str:  # noqa: D102
        # add to config
        self._config.add_additional_filter(value)
        return value


class TypeOverrideAudioProfile:
    """Return ProfileFilter if it exists."""

    def __init__(self, config: Config) -> None:
        self._config = config

    def __call__(self, value: str) -> str:  # noqa: D102
        # add to config
        self._config.add_additional_filter(value)
        return value


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


class TypeVideoProfile:
    """Return ProfileVideoType value if it exists."""

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self._parser = parser

    def __call__(self, value: str) -> ProfileVideoType:  # noqa: D102
        try:
            return ProfileVideoType[value.upper()]
        except KeyError:
            self._parser.error(
                f"argument --video-profile: invalid ProfileVideoType value: "
                f"'{value}', check --help for available options."
            )
