from __future__ import annotations

from typing import TYPE_CHECKING

from tbc_video_export.common.enums import ProcessName
from tbc_video_export.process.parser.parser_ffmpeg import ParserFFmpeg
from tbc_video_export.process.parser.parser_ld_chroma_decoder import (
    ParserLDChromaDecoder,
)
from tbc_video_export.process.parser.parser_ld_dropout_correct import (
    ParserLDDropoutCorrect,
)
from tbc_video_export.process.parser.parser_ld_export_metadata import (
    ParserLDExportMetadata,
)
from tbc_video_export.process.parser.parser_ld_process_efm import ParserLDProcessEFM
from tbc_video_export.process.parser.parser_ld_process_vbi import ParserLDProcessVBI

if TYPE_CHECKING:
    from tbc_video_export.process.parser.parser import Parser


class ParserFactory:
    """Factory class for process parsing."""

    @classmethod
    def create(cls, process_name: ProcessName) -> Parser:
        """Create an output parser based on process name."""
        match process_name:
            case ProcessName.FFMPEG:
                return ParserFFmpeg(process_name)

            case ProcessName.LD_CHROMA_DECODER:
                return ParserLDChromaDecoder(process_name)

            case ProcessName.LD_DROPOUT_CORRECT:
                return ParserLDDropoutCorrect(process_name)

            case ProcessName.LD_PROCESS_VBI:
                return ParserLDProcessVBI(process_name)

            case ProcessName.LD_EXPORT_METADATA:
                return ParserLDExportMetadata(process_name)

            case ProcessName.LD_PROCESS_EFM:
                return ParserLDProcessEFM(process_name)

            case ProcessName.NONE:
                raise NotImplementedError(
                    f"Parser for process {process_name} not implemented."
                )
