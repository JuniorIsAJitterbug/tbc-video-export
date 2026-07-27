from __future__ import annotations

from dataclasses import dataclass

from tbc_video_export.common.enums import FFmpegBitDepth, FFmpegPixelFormat


@dataclass(frozen=True, slots=True)
class PixelFormat:
    """Helper class for ffmpeg pixel formats."""

    @staticmethod
    def get_pix_format(pix_fmt: FFmpegPixelFormat, bit_depth: FFmpegBitDepth) -> str:
        """Return pixel format string from video format and bit depth."""
        return _pixel_formats[pix_fmt][bit_depth]


_pixel_formats: dict[FFmpegPixelFormat, dict[FFmpegBitDepth, str]] = {
    FFmpegPixelFormat.GRAY: {
        FFmpegBitDepth.BIT_8: "gray8",
        FFmpegBitDepth.BIT_10: "gray16le",
        FFmpegBitDepth.BIT_16: "gray16le",
    },
    FFmpegPixelFormat.YUV420: {
        FFmpegBitDepth.BIT_8: "yuv420p",
        FFmpegBitDepth.BIT_10: "yuv420p10le",
        FFmpegBitDepth.BIT_16: "yuv420p16le",
    },
    FFmpegPixelFormat.YUV422: {
        FFmpegBitDepth.BIT_8: "yuv422p",
        FFmpegBitDepth.BIT_10: "yuv422p10le",
        FFmpegBitDepth.BIT_16: "yuv422p16le",
    },
    FFmpegPixelFormat.YUV444: {
        FFmpegBitDepth.BIT_8: "yuv444p",
        FFmpegBitDepth.BIT_10: "yuv444p10le",
        FFmpegBitDepth.BIT_16: "yuv444p16le",
    },
}
