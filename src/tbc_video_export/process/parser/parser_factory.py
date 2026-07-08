from __future__ import annotations

from typing import TYPE_CHECKING

from tbc_video_export.common.enums import ToolType
from tbc_video_export.process.parser.parser_chroma_decode import (
    ParserChromaDecode,
)
from tbc_video_export.process.parser.parser_dropout_correct import (
    ParserDropoutCorrect,
)
from tbc_video_export.process.parser.parser_ffmpeg import ParserFFmpeg
from tbc_video_export.process.parser.parser_metadata_export import (
    ParserMetadataExport,
)
from tbc_video_export.process.parser.parser_vbi_process import ParserVBIProcess

if TYPE_CHECKING:
    from tbc_video_export.process.parser.parser import Parser


class ParserFactory:
    """Factory class for process parsing."""

    @classmethod
    def create(cls, process_type: ToolType) -> Parser:
        """Create an output parser based on process type."""
        match process_type:
            case ToolType.CHROMA_DECODE:
                return ParserChromaDecode(process_type)

            case ToolType.DROPOUT_CORRECT:
                return ParserDropoutCorrect(process_type)

            case ToolType.FFMPEG:
                return ParserFFmpeg(process_type)

            case ToolType.METADATA_EXPORT:
                return ParserMetadataExport(process_type)

            case ToolType.VBI_PROCESS:
                return ParserVBIProcess(process_type)

            case _:
                raise NotImplementedError(
                    f"Parser for process {process_type} not implemented."
                )
