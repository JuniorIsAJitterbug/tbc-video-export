from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import (
    MetadataType,
    ToolName,
    ToolsetType,
    ToolType,
)


@dataclass(frozen=True, slots=True)
class ToolData:
    """Container for tools."""

    name: ToolName
    appimage_support: bool


@dataclass(frozen=True, slots=True)
class ToolsetData:
    """Container for toolsets.

    This stores toolsets and their supported tool and metadata types.
    """

    default: bool
    default_metadata_type: MetadataType
    tools: dict[ToolType, ToolData]
    metadata_types: list[MetadataType]

    @staticmethod
    def get(toolset_type: ToolsetType) -> ToolsetData:
        """Returns ToolsetData for the specified toolset type."""
        return _toolsets[toolset_type]

    def get_tool_data(self, tool_type: ToolType) -> ToolData:  # noqa: D102
        try:
            return self.tools[tool_type]
        except KeyError as e:
            raise exceptions.ToolUnsupportedError from e

    def get_tool_name(self, tool_type: ToolType) -> ToolName:  # noqa: D102
        return self.get_tool_data(tool_type).name

    def supports_appimage(self, tool_type: ToolType) -> bool:  # noqa: D102
        return self.get_tool_data(tool_type).appimage_support


_toolsets: Final[dict[ToolsetType, ToolsetData]] = {
    ToolsetType.LEGACY_TOOLS: ToolsetData(
        default=True,
        default_metadata_type=MetadataType.JSON,
        tools={
            ToolType.CHROMA_DECODE: ToolData(
                name=ToolName.LD_CHROMA_DECODER,
                appimage_support=True,
            ),
            ToolType.DROPOUT_CORRECT: ToolData(
                name=ToolName.LD_DROPOUT_CORRECT,
                appimage_support=True,
            ),
            ToolType.FFMPEG: ToolData(
                name=ToolName.FFMPEG,
                appimage_support=False,
            ),
            ToolType.METADATA_EXPORT: ToolData(
                name=ToolName.LD_EXPORT_METADATA,
                appimage_support=True,
            ),
            ToolType.VBI_PROCESS: ToolData(
                name=ToolName.LD_PROCESS_VBI,
                appimage_support=True,
            ),
        },
        metadata_types=[
            MetadataType.JSON,
        ],
    ),
    ToolsetType.LD_DECODE_TOOLS: ToolsetData(
        default=False,
        default_metadata_type=MetadataType.SQLITE,
        tools={
            ToolType.CHROMA_DECODE: ToolData(
                name=ToolName.LD_CHROMA_DECODER,
                appimage_support=True,
            ),
            ToolType.DROPOUT_CORRECT: ToolData(
                name=ToolName.LD_DROPOUT_CORRECT,
                appimage_support=True,
            ),
            ToolType.FFMPEG: ToolData(
                name=ToolName.FFMPEG,
                appimage_support=False,
            ),
            ToolType.METADATA_CONVERT: ToolData(
                name=ToolName.LD_JSON_CONVERTER,
                appimage_support=True,
            ),
            ToolType.METADATA_EXPORT: ToolData(
                name=ToolName.LD_EXPORT_METADATA,
                appimage_support=True,
            ),
            ToolType.VBI_PROCESS: ToolData(
                name=ToolName.LD_PROCESS_VBI,
                appimage_support=True,
            ),
        },
        metadata_types=[
            MetadataType.SQLITE,
        ],
    ),
    ToolsetType.TBC_TOOLS: ToolsetData(
        default=False,
        default_metadata_type=MetadataType.JSON,
        tools={
            ToolType.CHROMA_DECODE: ToolData(
                name=ToolName.LD_CHROMA_DECODER,
                appimage_support=True,
            ),
            ToolType.DROPOUT_CORRECT: ToolData(
                name=ToolName.LD_DROPOUT_CORRECT,
                appimage_support=True,
            ),
            ToolType.FFMPEG: ToolData(
                name=ToolName.FFMPEG,
                appimage_support=False,
            ),
            ToolType.METADATA_CONVERT: ToolData(
                name=ToolName.TBC_METADATA_CONVERTER,
                appimage_support=True,
            ),
            ToolType.METADATA_EXPORT: ToolData(
                name=ToolName.TBC_EXPORT_METADATA, appimage_support=True
            ),
            ToolType.VBI_PROCESS: ToolData(
                name=ToolName.LD_PROCESS_VBI,
                appimage_support=True,
            ),
        },
        metadata_types=[
            MetadataType.JSON,
            MetadataType.SQLITE,
        ],
    ),
}
