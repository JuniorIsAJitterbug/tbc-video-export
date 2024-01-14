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
        return self.name


class ExportMode(Enum):
    """Export flags for the application."""

    LUMA = "Luma"
    LUMA_EXTRACTED = "Luma (extracted)"
    LUMA_4FSC = "Luma (4FSC)"
    CHROMA_MERGE = "Luma + Chroma (merged)"
    CHROMA_COMBINED = "Luma + Chroma (combined)"

    def __str__(self) -> str:
        """Return enum value as string."""
        return self.value


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
        return self.name.replace("_", "-").lower()


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
        return self.name.upper()


class ProfileType(Enum):
    """Profile types for FFmpeg."""

    DEFAULT = TBCType.CHROMA | TBCType.COMBINED
    LUMA = TBCType.LUMA

    def __str__(self) -> str:
        """Return formatted enum name as string."""
        return self.name.upper()
