from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import ClassVar, Literal, TypeAlias

from tbc_video_export.common.enums import ChromaDecoder, ExportMode, VideoSystem


@dataclass(frozen=True, slots=True)
class VideoSystemData:
    """Base VideoSystem data class.

    Holds static values for the video system.

    Active line values from (default):
    vhs_decode/tools/library/tbc/lddecodemetadata.cpp

    Aspect ratio values from (default/widescreen):
    vhs_decode/tools/ld-chroma-decoder/outputwriter.cpp
    """

    size: dict[VideoSizeType, Size]
    active_lines: dict[VideoActiveLinesType, ActiveLines]
    aspect_ratio: dict[VideoAspectRatioType, AspectRatio]
    chroma_decoder: dict[ExportMode, ChromaDecoder]
    ffmpeg_config: FFmpegConfig

    @staticmethod
    def get(system: VideoSystem) -> VideoSystemData:
        """Returns VideoSystemData for the specified video format."""
        match system:
            case VideoSystem.PAL:
                return video_system_pal

            case VideoSystem.NTSC:
                return video_system_ntsc

            case VideoSystem.PAL_M:
                return video_system_palm

    @dataclass(frozen=True, slots=True)
    class Size:
        """Width/height data container."""

        width: int
        height: int

    @dataclass(frozen=True, slots=True)
    class AspectRatio:
        """Aspect ratio container."""

        horizontal: int
        vertical: int

    @dataclass(frozen=True, slots=True)
    class ActiveLines:
        """Active lines data container."""

        first_field: int
        last_field: int
        first_frame: int
        last_frame: int
        padding: int | None

    @dataclass(frozen=True, slots=True)
    class FFmpegConfig:
        """FFmpeg config data container."""

        color_range: str
        color_space: str
        color_primaries: str
        color_trc: str
        fps: str

        _FPS_RATES: ClassVar[dict[str, Fraction]] = {
            "pal": Fraction(25),
            "ntsc": Fraction(30000, 1001),
        }

        @property
        def fps_fraction(self) -> Fraction:
            """Return fps as a Fraction for precise frame-to-time arithmetic."""
            return self._FPS_RATES[self.fps]


video_system_pal = VideoSystemData(
    size={
        "default": VideoSystemData.Size(928, 576),  # unused
        "4fsc": VideoSystemData.Size(1135, 626),
    },
    active_lines={
        "default": VideoSystemData.ActiveLines(22, 308, 44, 620, None),  # unused
        "full_vertical": VideoSystemData.ActiveLines(2, 308, 2, 620, None),
        "letterbox": VideoSystemData.ActiveLines(2, 308, 118, 548, None),
        "vbi": VideoSystemData.ActiveLines(12, 308, 12, 620, None),
    },
    aspect_ratio={
        "default": VideoSystemData.AspectRatio(259, 311),  # unused
        "widescreen": VideoSystemData.AspectRatio(865, 779),
        "letterbox": VideoSystemData.AspectRatio(16, 9),
    },
    chroma_decoder={
        ExportMode.LUMA_EXTRACTED: ChromaDecoder.MONO,
        ExportMode.CHROMA_MERGE: ChromaDecoder.PAL2D,
        ExportMode.CHROMA_COMBINED: ChromaDecoder.TRANSFORM3D,
        ExportMode.CHROMA_COMBINED_LD: ChromaDecoder.TRANSFORM3D,
    },
    ffmpeg_config=VideoSystemData.FFmpegConfig(
        "tv",
        "bt470bg",
        "bt470bg",
        "bt709",
        "pal",
    ),
)

video_system_ntsc = VideoSystemData(
    size={
        "default": VideoSystemData.Size(760, 488),  # unused
        "4fsc": VideoSystemData.Size(910, 526),
    },
    active_lines={
        "default": VideoSystemData.ActiveLines(20, 259, 40, 525, None),  # unused
        "full_vertical": VideoSystemData.ActiveLines(1, 259, 2, 525, None),
        "letterbox": VideoSystemData.ActiveLines(61, 224, 122, 448, 1),  # unsure!
        "vbi": VideoSystemData.ActiveLines(15, 259, 16, 525, 1),
    },
    aspect_ratio={
        "default": VideoSystemData.AspectRatio(352, 413),  # unused
        "widescreen": VideoSystemData.AspectRatio(25, 22),
        "letterbox": VideoSystemData.AspectRatio(16, 9),
    },
    chroma_decoder={
        ExportMode.LUMA_EXTRACTED: ChromaDecoder.MONO,
        ExportMode.CHROMA_MERGE: ChromaDecoder.NTSC2D,
        ExportMode.CHROMA_COMBINED: ChromaDecoder.NTSC3D,
        ExportMode.CHROMA_COMBINED_LD: ChromaDecoder.NTSC2D,
    },
    ffmpeg_config=VideoSystemData.FFmpegConfig(
        "tv",
        "smpte170m",
        "smpte170m",
        "bt709",
        "ntsc",
    ),
)

video_system_palm = VideoSystemData(
    size={
        "default": VideoSystemData.Size(760, 488),  # unused
        "4fsc": VideoSystemData.Size(909, 526),
    },
    active_lines={
        "default": VideoSystemData.ActiveLines(20, 259, 40, 525, None),  # unused
        "full_vertical": VideoSystemData.ActiveLines(1, 259, 2, 525, None),
        "letterbox": VideoSystemData.ActiveLines(0, 0, 0, 0, 0),  # Sample required!
        "vbi": VideoSystemData.ActiveLines(16, 259, 17, 525, 1),
    },
    aspect_ratio={
        "default": VideoSystemData.AspectRatio(352, 413),  # unused
        "widescreen": VideoSystemData.AspectRatio(25, 22),
        "letterbox": VideoSystemData.AspectRatio(16, 9),
    },
    chroma_decoder={
        ExportMode.LUMA_EXTRACTED: ChromaDecoder.MONO,
        ExportMode.CHROMA_MERGE: ChromaDecoder.PAL2D,
        ExportMode.CHROMA_COMBINED: ChromaDecoder.TRANSFORM3D,
        ExportMode.CHROMA_COMBINED_LD: ChromaDecoder.TRANSFORM3D,
    },
    ffmpeg_config=VideoSystemData.FFmpegConfig(
        "tv",
        "bt470bg",
        "bt470bg",
        "bt709",
        "ntsc",
    ),
)

VideoSizeType: TypeAlias = Literal["default", "4fsc"]
VideoActiveLinesType: TypeAlias = Literal[
    "default", "full_vertical", "letterbox", "vbi"
]
VideoAspectRatioType: TypeAlias = Literal["default", "widescreen", "letterbox"]
