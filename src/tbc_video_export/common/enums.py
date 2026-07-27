from __future__ import annotations

import sys
from enum import Enum, Flag, auto
from functools import cache
from typing import TypeVar

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

T = TypeVar("T", bound=Flag)


class FlagHelper:
    """Helper utils for enum.Flags.

    Most of these are not required in python >=3.11.
    """

    @staticmethod
    def get_flags(flag: T) -> list[T]:
        """Return a list of flags contained within a variable."""
        return [f for f in flag.__class__ if f & flag == f]

    @staticmethod
    @cache
    def get_flag_names(flag: Flag) -> list[str]:
        """Return a list of flag names contained within a variable."""
        return [
            f.name for f in flag.__class__ if f & flag == f and f.name and f.value != 1
        ]

    @staticmethod
    @cache
    def get_flags_str(flag: Flag, delimiter: str = "|") -> str:
        """Return a formatted flag string.

        This contains the flag names within a variable.
        """
        return f" {delimiter} ".join(FlagHelper.get_flag_names(flag))


class TBCType(Flag):
    """TBC type flags."""

    NONE = auto()
    COMBINED = auto()
    LUMA = auto()
    CHROMA = auto()

    @override
    def __str__(self) -> str:
        """Return enum name as string."""
        return f"{self.name!s}"


class ExportMode(Enum):
    """Export flags for the application."""

    LUMA = auto()
    LUMA_EXTRACTED = auto()
    LUMA_4FSC = auto()
    CHROMA_MERGE = auto()
    CHROMA_COMBINED = auto()
    CHROMA_COMBINED_LD = auto()


class VideoSystem(Enum):
    """Supported video systems."""

    PAL = "pal"
    PAL_M = "pal_m"
    NTSC = "ntsc"

    @override
    def __str__(self) -> str:
        """Return formatted enum value as string."""
        return self.value.replace("_", "-").lower()

    @override
    @classmethod
    def _missing_(cls, value: object) -> VideoSystem | None:
        """Check if formatted string is in enum."""
        if isinstance(value, str):
            for member in cls:
                if f"{member.value!s}" == value:
                    return member
        return None


class ChromaDecoder(Enum):
    """Available chroma decoders."""

    NONE = "none"
    PAL2D = "pal2d"
    TRANSFORM2D = "transform2d"
    TRANSFORM3D = "transform3d"
    MONO = "mono"
    NTSC1D = "ntsc1d"
    NTSC2D = "ntsc2d"
    NTSC3D = "ntsc3d"
    NTSC3DNOADAPT = "ntsc3dnoadapt"

    @override
    def __str__(self) -> str:
        """Return enum name as string."""
        return self.name


class FieldOrder(Enum):
    """Available field orders."""

    AUTO = "Auto"
    TFF = "Interlaced (Top Field First)"
    BFF = "Interlaced (Bottom Field First)"
    PROG = "Progressive"

    @override
    def __str__(self) -> str:
        """Return enum value as string."""
        return self.value


class ToolsetType(Enum):
    """Supported toolset types."""

    LEGACY_TOOLS = "legacy"
    LD_DECODE_TOOLS = "ld-decode-tools"
    TBC_TOOLS = "tbc-tools"

    @override
    def __str__(self) -> str:
        """Return enum value as string."""
        return self.value


class ToolType(Flag):
    """Tool types."""

    NONE = auto()
    DROPOUT_CORRECT = auto()
    CHROMA_DECODE = auto()
    FFMPEG = auto()
    METADATA_CONVERT = auto()
    METADATA_EXPORT = auto()
    VBI_PROCESS = auto()

    @override
    def __str__(self) -> str:
        """Return formatted enum name as string."""
        return f"{self.name!s}".replace("_", "-").lower()


class ToolName(Enum):
    """Tool names."""

    NONE = auto()
    FFMPEG = "ffmpeg"
    LD_CHROMA_DECODER = "ld-chroma-decoder"
    LD_DROPOUT_CORRECT = "ld-dropout-correct"
    LD_EXPORT_METADATA = "ld-export-metadata"
    LD_JSON_CONVERTER = "ld-json-converter"
    LD_PROCESS_VBI = "ld-process-vbi"
    TBC_EXPORT_METADATA = "tbc-export-metadata"
    TBC_METADATA_CONVERTER = "tbc-metadata-converter"

    @override
    def __str__(self) -> str:
        """Return formatted enum name as string."""
        return self.value


class ProcessStatus(Flag):
    """Process status flags."""

    NONE = auto()
    HAS_RUN = auto()
    RUNNING = auto()
    ENDED = auto()
    SUCCESS = auto()
    ERROR = auto()


class MetadataType(Enum):
    """Supported metadata types."""

    JSON = auto()
    SQLITE = auto()

    @override
    def __str__(self) -> str:
        """Return formatted enum name as string."""
        return self.name.lower()


class PipeType(Flag):
    """Pipe types for processes."""

    NONE = auto()
    NULL = auto()
    OS = auto()
    NAMED_POSIX = auto()
    NAMED_NT = auto()
    NAMED = NAMED_POSIX | NAMED_NT

    @override
    def __str__(self) -> str:
        """Return formatted enum name as string."""
        return f"{self.name!s}".upper()


class HardwareAccelType(Enum):
    """Hardware accel types for profiles."""

    VAAPI = "vaapi"
    NVENC = "nvenc"
    QUICKSYNC = "quicksync"
    AMF = "amf"
    VIDEOTOOLBOX = "videotoolbox"


class FFmpegPixelFormat(Enum):
    """FFmpeg pixel format types for profiles."""

    GRAY = auto()
    YUV420 = auto()
    YUV422 = auto()
    YUV444 = auto()

    @override
    def __str__(self) -> str:
        """Return formatted enum name as string."""
        return self.name.lower()


class FFmpegBitDepth(Enum):
    """FFmpeg bit depth types for profiles."""

    BIT_8 = 8
    BIT_10 = 10
    BIT_16 = 16

    @override
    def __str__(self) -> str:
        """Return formatted enum name as string."""
        return f"{self.value!s}"
