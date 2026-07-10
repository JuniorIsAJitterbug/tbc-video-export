from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from tbc_video_export.common.enums import (
    ChromaDecoder,
    FieldOrder,
    MetadataType,
    TBCType,
    ToolsetType,
    VideoSystem,
)

if TYPE_CHECKING:
    import argparse

    from tbc_video_export.config import Config

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class TypeVideoSystem:
    """Return ChromaDecoder value if it exists."""

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self._parser = parser

    @override
    def __call__(self, value: str) -> VideoSystem:
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

    @override
    def __call__(self, value: str) -> FieldOrder:
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

    @override
    def __call__(self, value: str) -> str:
        # add to config
        self._config.add_additional_filter(value)
        return value


class TypeDropoutInterfieldCorrection:
    """Return TBCType value if it exists."""

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self._parser = parser

    @override
    def __call__(self, value: str) -> TBCType:
        try:
            return TBCType[value.upper()]
        except KeyError:
            self._parser.error(
                f"argument --dropout-interfield-correction: invalid value: '{value}', "
                f"check --help for available options."
            )


class TypeChromaDecoder:
    """Return ChromaDecoder value if it exists."""

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self._parser = parser

    @override
    def __call__(self, value: str) -> ChromaDecoder:
        try:
            return ChromaDecoder[value.upper()]
        except KeyError:
            self._parser.error(
                f"argument --chroma-decoder: invalid ChromaDecoder value: '{value}', "
                f"check --help for available options."
            )


class TypeToolset:
    """Return Toolset value if it exists."""

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self._parser = parser

    @override
    def __call__(self, value: str) -> ToolsetType:
        toolset_type = next(
            (
                toolset_type
                for toolset_type in ToolsetType
                if f"{toolset_type!s}" == value.lower()
            ),
            None,
        )

        if toolset_type is None:
            self._parser.error(
                f"argument --toolset: invalid Toolset value: '{value}', "
                f"check --help for available options."
            )

        return toolset_type


class TypeMetadataType:
    """Return MetadataType value if it exists."""

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self._parser = parser

    @override
    def __call__(self, value: str) -> MetadataType:
        try:
            return MetadataType[value.upper()]
        except KeyError:
            self._parser.error(
                f"argument --metadata-type: invalid MetadataType value: '{value}', "
                f"check --help for available options."
            )
