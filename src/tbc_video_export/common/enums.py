from __future__ import annotations

from enum import Enum, Flag, auto
from functools import cache
from typing import TypeVar

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

    def __str__(self) -> str:
        """Return enum name as string."""
        return str(self.name)


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

    def __str__(self) -> str:
        """Return formatted enum value as string."""
        return self.value.replace("_", "-").lower()

    @classmethod
    def _missing_(cls, value: object) -> VideoSystem | None:
        """Check if formatted string is in enum."""
        if isinstance(value, str):
            for member in cls:
                if str(member.value) == str(value):
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

    def __str__(self) -> str:
        """Return enum name as string."""
        return self.name


class FieldOrder(Enum):
    """Available field orders."""

    AUTO = "Auto"
    TFF = "Interlaced (Top Field First)"
    BFF = "Interlaced (Bottom Field First)"
    PROG = "Progressive"

    def __str__(self) -> str:
        """Return enum value as string."""
        return self.value


class ProcessName(Flag):
    """Process names for parsing messages."""

    NONE = auto()
    LD_PROCESS_VBI = auto()
    LD_EXPORT_METADATA = auto()
    LD_PROCESS_EFM = auto()
    LD_DROPOUT_CORRECT = auto()
    LD_CHROMA_DECODER = auto()
    FFMPEG = auto()

    def __str__(self) -> str:
        """Return formatted enum name as string."""
        return str(self.name).replace("_", "-").lower()


class ProcessStatus(Flag):
    """Process status flags."""

    NONE = auto()
    HAS_RUN = auto()
    RUNNING = auto()
    STOPPED = auto()
    SUCCESS = auto()
    ERROR = auto()


class PipeType(Flag):
    """Pipe types for processes."""

    NONE = auto()
    NULL = auto()
    OS = auto()
    NAMED_POSIX = auto()
    NAMED_NT = auto()
    NAMED = NAMED_POSIX | NAMED_NT

    def __str__(self) -> str:
        """Return formatted enum name as string."""
        return str(self.name).upper()


class VideoBitDepthType(Enum):
    """Video bitdepth types for profiles."""

    BIT8 = "8bit"
    BIT10 = "10bit"
    BIT16 = "16bit"


class HardwareAccelType(Enum):
    """Hardware accel types for profiles."""

    VAAPI = "vaapi"
    NVENC = "nvenc"
    QUICKSYNC = "quicksync"
    AMF = "amf"
    VIDEOTOOLBOX = "videotoolbox"


class VideoFormatType(Enum):
    """Video format types for profiles."""

    GRAY = {
        8: "gray8",
        10: "gray16le",
        16: "gray16le",
    }
    YUV420 = {
        8: "yuv420p",
        10: "yuv420p10le",
        16: "yuv420p16le",
    }
    YUV422 = {
        8: "yuv422p",
        10: "yuv422p10le",
        16: "yuv422p16le",
    }
    YUV444 = {
        8: "yuv444p",
        10: "yuv444p10le",
        16: "yuv444p16le",
    }

    @classmethod
    def get_new_format(cls, current_format: str, new_bitdepth: int) -> str | None:
        """Return new format from current format and new bitdepth."""
        return next(
            (
                member.value.get(new_bitdepth)
                for member in cls
                for _, v in member.value.items()
                if current_format == v
            ),
            None,
        )

    @classmethod
    def get_bitdepth(cls, current_format: str) -> int | None:
        """Return bitdepth of current format."""
        return next(
            (
                k
                for member in cls
                for k, v in member.value.items()
                if current_format == v
            ),
            None,
        )
