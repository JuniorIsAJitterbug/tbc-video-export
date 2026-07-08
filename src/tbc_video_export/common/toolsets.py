from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from typing import Final

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import (
    MetadataType,
    ToolName,
    ToolsetType,
    ToolType,
)


@cache
def get_tool_name(toolset: ToolsetType, tool_type: ToolType) -> ToolName:
    """Return process name from tool version and process type."""
    if (
        tool_type not in toolsets[toolset].tools
        or toolsets[toolset].tools is ToolName.NONE
    ):
        raise exceptions.ToolUnsupportedError

    return toolsets[toolset].tools[tool_type]


@cache
def is_metadata_type_supported(
    toolset: ToolsetType, metadata_type: MetadataType
) -> bool:
    """Return True if metadata type is supported by toolset."""
    return metadata_type in toolsets[toolset].metadata_types


@dataclass(frozen=True, slots=True)
class ToolsetData:
    """Container for toolsets.

    This stores toolsets and their supported tool and metadata types.
    """

    default: bool
    default_metadata_type: MetadataType
    tools: dict[ToolType, ToolName]
    metadata_types: list[MetadataType]


toolsets: Final[dict[ToolsetType, ToolsetData]] = {
    ToolsetType.LEGACY_TOOLS: ToolsetData(
        default=True,
        default_metadata_type=MetadataType.JSON,
        tools={
            ToolType.CHROMA_DECODE: ToolName.LD_CHROMA_DECODER,
            ToolType.DROPOUT_CORRECT: ToolName.LD_DROPOUT_CORRECT,
            ToolType.FFMPEG: ToolName.FFMPEG,
            ToolType.METADATA_EXPORT: ToolName.LD_EXPORT_METADATA,
            ToolType.VBI_PROCESS: ToolName.LD_PROCESS_VBI,
        },
        metadata_types=[
            MetadataType.JSON,
        ],
    ),
}
