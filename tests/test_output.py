from __future__ import annotations

from contextlib import suppress
from dataclasses import fields
from pathlib import Path
from typing import Any

import pytest
from pymediainfo import MediaInfo  # pyright: ignore[reportMissingTypeStubs]
from tbc_video_export import main

from tests.conftest import (
    AudioBase,
    OutputTestCase,
    VideoBaseNTSC,
    VideoBasePAL,
    VideoBasePALM,
    VideoColorNTSC,
    VideoColorPAL,
    VideoColorPALM,
)


class TestOutput:
    """Tests for output video files.

    This will generate multiple video files using tbc-tools and ffmpeg,
    and validate the output using mediainfo.
    """

    codec_ffv1: dict[str, Any] = {
        "format": "FFV1",
        "format_settings__gop": "N=1",
        "coder_type": "Range Coder",
        "maxslicescount": "24",
        "errordetectiontype": "Per slice",
    }

    pal_svideo_test_cases = [
        OutputTestCase(
            id="default",
            input_opts=["--quiet", "--overwrite"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="luma",
            input_opts=["--quiet", "--overwrite", "--luma-only"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="Y",
                bit_depth=16,
                chroma_subsampling=None,
            ),
        ),
        OutputTestCase(
            id="4fsc",
            input_opts=["--quiet", "--overwrite", "--luma-4fsc"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(
                width=1135,
                height=626,
                pixel_aspect_ratio="1.000",
                display_aspect_ratio="1.813",
            ),
            output_video_color=VideoColorPAL(
                color_space="Y",
                bit_depth=16,
                chroma_subsampling=None,
            ),
        ),
        OutputTestCase(
            id="vbi",
            input_opts=["--quiet", "--overwrite", "--vbi"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(
                width=928,
                height=612,
                pixel_aspect_ratio="0.833",
                display_aspect_ratio="1.263",
            ),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="letterbox",
            input_opts=["--quiet", "--overwrite", "--letterbox"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(
                width=928,
                height=432,
                pixel_aspect_ratio="1.110",
                display_aspect_ratio="2.385",
            ),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="full vertical",
            input_opts=["--quiet", "--overwrite", "--full-vertical"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(
                width=928,
                height=624,
                pixel_aspect_ratio="0.833",
                display_aspect_ratio="1.239",
            ),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
    ]

    pal_composite_test_cases = [
        OutputTestCase(
            id="default",
            input_opts=["--quiet", "--overwrite"],
            input_tbc="pal_composite",
            output_file="pal_composite.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="luma",
            input_opts=["--quiet", "--overwrite", "--luma-only"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="Y",
                bit_depth=16,
                chroma_subsampling=None,
            ),
        ),
        OutputTestCase(
            id="4fsc",
            input_opts=["--quiet", "--overwrite", "--luma-4fsc"],
            input_tbc="pal_composite",
            output_file="pal_composite.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(
                width=1135,
                height=626,
                pixel_aspect_ratio="1.000",
                display_aspect_ratio="1.813",
            ),
            output_video_color=VideoColorPAL(
                color_space="Y",
                bit_depth=16,
                chroma_subsampling=None,
            ),
        ),
        OutputTestCase(
            id="vbi",
            input_opts=["--quiet", "--overwrite", "--vbi"],
            input_tbc="pal_composite",
            output_file="pal_composite.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(
                width=928,
                height=612,
                display_aspect_ratio="1.263",
            ),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="letterbox",
            input_opts=["--quiet", "--overwrite", "--letterbox"],
            input_tbc="pal_composite",
            output_file="pal_composite.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(
                width=928,
                height=432,
                pixel_aspect_ratio="1.110",
                display_aspect_ratio="2.385",
            ),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="full vertical",
            input_opts=["--quiet", "--overwrite", "--full-vertical"],
            input_tbc="pal_composite",
            output_file="pal_composite.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(
                width=928,
                height=624,
                display_aspect_ratio="1.239",
            ),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
    ]

    pal_composite_ld_test_cases = [
        OutputTestCase(
            id="default",
            input_opts=["--quiet", "--overwrite"],
            input_tbc="pal_composite_ld",
            output_file="pal_composite_ld.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="luma",
            input_opts=["--quiet", "--overwrite", "--luma-only"],
            input_tbc="pal_composite_ld",
            output_file="pal_composite_ld.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="Y",
                bit_depth=16,
                chroma_subsampling=None,
            ),
        ),
        OutputTestCase(
            id="4fsc",
            input_opts=["--quiet", "--overwrite", "--luma-4fsc"],
            input_tbc="pal_composite_ld",
            output_file="pal_composite_ld.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(
                width=1135,
                height=626,
                pixel_aspect_ratio="1.000",
                display_aspect_ratio="1.813",
            ),
            output_video_color=VideoColorPAL(
                color_space="Y",
                bit_depth=16,
                chroma_subsampling=None,
            ),
        ),
        OutputTestCase(
            id="vbi",
            input_opts=["--quiet", "--overwrite", "--vbi"],
            input_tbc="pal_composite_ld",
            output_file="pal_composite_ld.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(
                width=928,
                height=612,
                display_aspect_ratio="1.263",
            ),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="letterbox",
            input_opts=["--quiet", "--overwrite", "--letterbox"],
            input_tbc="pal_composite_ld",
            output_file="pal_composite_ld.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(
                width=928,
                height=432,
                pixel_aspect_ratio="1.110",
                display_aspect_ratio="2.385",
            ),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="full vertical",
            input_opts=["--quiet", "--overwrite", "--full-vertical"],
            input_tbc="pal_composite_ld",
            output_file="pal_composite_ld.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(
                width=928,
                height=624,
                display_aspect_ratio="1.239",
            ),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
    ]

    ntsc_svideo_test_cases = [
        OutputTestCase(
            id="default",
            input_opts=["--quiet", "--overwrite"],
            input_tbc="ntsc_svideo",
            output_file="ntsc_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(),
            output_video_color=VideoColorNTSC(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="luma",
            input_opts=["--quiet", "--overwrite", "--luma-only"],
            input_tbc="ntsc_svideo",
            output_file="ntsc_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(),
            output_video_color=VideoColorNTSC(
                color_space="Y",
                bit_depth=16,
                chroma_subsampling=None,
            ),
        ),
        OutputTestCase(
            id="4fsc",
            input_opts=["--quiet", "--overwrite", "--luma-4fsc"],
            input_tbc="ntsc_svideo",
            output_file="ntsc_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(
                width=910,
                height=526,
                pixel_aspect_ratio="1.000",
                display_aspect_ratio="1.730",
            ),
            output_video_color=VideoColorNTSC(
                color_space="Y",
                bit_depth=16,
                chroma_subsampling=None,
            ),
        ),
        OutputTestCase(
            id="vbi",
            input_opts=["--quiet", "--overwrite", "--vbi"],
            input_tbc="ntsc_svideo",
            output_file="ntsc_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(
                width=760,
                height=509,
                display_aspect_ratio="1.273",
            ),
            output_video_color=VideoColorNTSC(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="letterbox",
            input_opts=["--quiet", "--overwrite", "--letterbox"],
            input_tbc="ntsc_svideo",
            output_file="ntsc_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(
                width=760,
                height=336,
                pixel_aspect_ratio="1.136",
                display_aspect_ratio="2.570",
            ),
            output_video_color=VideoColorNTSC(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="full vertical",
            input_opts=["--quiet", "--overwrite", "--full-vertical"],
            input_tbc="ntsc_svideo",
            output_file="ntsc_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(
                width=760,
                height=528,
                display_aspect_ratio="1.227",
            ),
            output_video_color=VideoColorNTSC(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
    ]

    ntsc_composite_test_cases = [
        OutputTestCase(
            id="default",
            input_opts=["--quiet", "--overwrite"],
            input_tbc="ntsc_composite",
            output_file="ntsc_composite.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(),
            output_video_color=VideoColorNTSC(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="luma",
            input_opts=["--quiet", "--overwrite", "--luma-only"],
            input_tbc="ntsc_composite",
            output_file="ntsc_composite.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(),
            output_video_color=VideoColorNTSC(
                color_space="Y",
                bit_depth=16,
                chroma_subsampling=None,
            ),
        ),
        OutputTestCase(
            id="4fsc",
            input_opts=["--quiet", "--overwrite", "--luma-4fsc"],
            input_tbc="ntsc_composite",
            output_file="ntsc_composite.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(
                width=910,
                height=526,
                pixel_aspect_ratio="1.000",
                display_aspect_ratio="1.730",
            ),
            output_video_color=VideoColorNTSC(
                color_space="Y",
                bit_depth=16,
                chroma_subsampling=None,
            ),
        ),
        OutputTestCase(
            id="vbi",
            input_opts=["--quiet", "--overwrite", "--vbi"],
            input_tbc="ntsc_composite",
            output_file="ntsc_composite.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(
                width=760,
                height=509,
                display_aspect_ratio="1.273",
            ),
            output_video_color=VideoColorNTSC(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="letterbox",
            input_opts=["--quiet", "--overwrite", "--letterbox"],
            input_tbc="ntsc_composite",
            output_file="ntsc_composite.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(
                width=760,
                height=336,
                pixel_aspect_ratio="1.136",
                display_aspect_ratio="2.570",
            ),
            output_video_color=VideoColorNTSC(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="full vertical",
            input_opts=["--quiet", "--overwrite", "--full-vertical"],
            input_tbc="ntsc_composite",
            output_file="ntsc_composite.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(
                width=760,
                height=528,
                display_aspect_ratio="1.227",
            ),
            output_video_color=VideoColorNTSC(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
    ]

    ntsc_composite_ld_test_cases = [
        OutputTestCase(
            id="default",
            input_opts=["--quiet", "--overwrite"],
            input_tbc="ntsc_composite_ld",
            output_file="ntsc_composite_ld.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(),
            output_video_color=VideoColorNTSC(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="luma",
            input_opts=["--quiet", "--overwrite", "--luma-only"],
            input_tbc="ntsc_composite_ld",
            output_file="ntsc_composite_ld.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(),
            output_video_color=VideoColorNTSC(
                color_space="Y",
                bit_depth=16,
                chroma_subsampling=None,
            ),
        ),
        OutputTestCase(
            id="4fsc",
            input_opts=["--quiet", "--overwrite", "--luma-4fsc"],
            input_tbc="ntsc_composite_ld",
            output_file="ntsc_composite_ld.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(
                width=910,
                height=526,
                pixel_aspect_ratio="1.000",
                display_aspect_ratio="1.730",
            ),
            output_video_color=VideoColorNTSC(
                color_space="Y",
                bit_depth=16,
                chroma_subsampling=None,
            ),
        ),
        OutputTestCase(
            id="vbi",
            input_opts=["--quiet", "--overwrite", "--vbi"],
            input_tbc="ntsc_composite_ld",
            output_file="ntsc_composite_ld.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(
                width=760,
                height=509,
                display_aspect_ratio="1.273",
            ),
            output_video_color=VideoColorNTSC(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="letterbox",
            input_opts=["--quiet", "--overwrite", "--letterbox"],
            input_tbc="ntsc_composite_ld",
            output_file="ntsc_composite_ld.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(
                width=760,
                height=336,
                pixel_aspect_ratio="1.136",
                display_aspect_ratio="2.570",
            ),
            output_video_color=VideoColorNTSC(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="full vertical",
            input_opts=["--quiet", "--overwrite", "--full-vertical"],
            input_tbc="ntsc_composite_ld",
            output_file="ntsc_composite_ld.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBaseNTSC(
                width=760,
                height=528,
                display_aspect_ratio="1.227",
            ),
            output_video_color=VideoColorNTSC(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
    ]

    palm_svideo_test_cases = [
        OutputTestCase(
            id="default pal-m svideo",
            input_opts=["--quiet", "--overwrite"],
            input_tbc="palm_svideo",
            output_file="palm_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePALM(),
            output_video_color=VideoColorPALM(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="default pal-m svideo luma",
            input_opts=["--quiet", "--overwrite", "--luma-only"],
            input_tbc="palm_svideo",
            output_file="palm_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePALM(),
            output_video_color=VideoColorPALM(
                color_space="Y",
                bit_depth=16,
                chroma_subsampling=None,
            ),
        ),
        OutputTestCase(
            id="default pal-m svideo luma 4fsc",
            input_opts=["--quiet", "--overwrite", "--luma-4fsc"],
            input_tbc="palm_svideo",
            output_file="palm_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePALM(
                width=909,
                height=526,
                pixel_aspect_ratio="1.000",
                display_aspect_ratio="1.728",
            ),
            output_video_color=VideoColorPALM(
                color_space="Y",
                bit_depth=16,
                chroma_subsampling=None,
            ),
        ),
        OutputTestCase(
            id="vbi",
            input_opts=["--quiet", "--overwrite", "--vbi"],
            input_tbc="palm_svideo",
            output_file="palm_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePALM(
                width=909,
                height=509,
                pixel_aspect_ratio="1.000",
                display_aspect_ratio="1.728",
            ),
            output_video_color=VideoColorPALM(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
            expected_exc=pytest.raises(AssertionError),
        ),
        OutputTestCase(
            id="letterbox",
            input_opts=["--quiet", "--overwrite", "--letterbox"],
            input_tbc="palm_svideo",
            output_file="palm_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePALM(),
            output_video_color=VideoColorPALM(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
            expected_exc=pytest.raises(AssertionError),
        ),
        OutputTestCase(
            id="full vertical",
            input_opts=["--quiet", "--overwrite", "--full-vertical"],
            input_tbc="palm_svideo",
            output_file="palm_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePALM(
                width=760,
                height=528,
                pixel_aspect_ratio="0.852",
                display_aspect_ratio="1.227",
            ),
            output_video_color=VideoColorPALM(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling=None,
            ),
        ),
    ]

    video_format_test_cases = [
        OutputTestCase(
            id="yuv420p",
            input_opts=["--quiet", "--overwrite", "--yuv420", "--8bit"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=8,
                chroma_subsampling="4:2:0",
            ),
        ),
        OutputTestCase(
            id="yuv420p10le",
            input_opts=["--quiet", "--overwrite", "--yuv420", "--10bit"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:0",
            ),
        ),
        OutputTestCase(
            id="yuv420p16le",
            input_opts=["--quiet", "--overwrite", "--yuv420", "--16bit"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=16,
                chroma_subsampling="4:2:0",
            ),
        ),
        OutputTestCase(
            id="yuv422p",
            input_opts=["--quiet", "--overwrite", "--yuv422", "--8bit"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=8,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="yuv422p10le",
            input_opts=["--quiet", "--overwrite", "--yuv422", "--10bit"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="yuv420p16le",
            input_opts=["--quiet", "--overwrite", "--yuv422", "--16bit"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=16,
                chroma_subsampling="4:2:2",
            ),
        ),
        OutputTestCase(
            id="yuv444p",
            input_opts=["--quiet", "--overwrite", "--yuv444", "--8bit"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=8,
                chroma_subsampling="4:4:4",
            ),
        ),
        OutputTestCase(
            id="yuv444p10le",
            input_opts=["--quiet", "--overwrite", "--yuv444", "--10bit"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:4:4",
            ),
        ),
        OutputTestCase(
            id="yuv444p16le",
            input_opts=["--quiet", "--overwrite", "--yuv444", "--16bit"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=16,
                chroma_subsampling="4:4:4",
            ),
        ),
        OutputTestCase(
            id="gray8",
            input_opts=["--quiet", "--overwrite", "--luma-only", "--gray", "--8bit"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="Y",
                bit_depth=8,
                chroma_subsampling=None,
            ),
        ),
        OutputTestCase(
            id="gray16le (10)",
            input_opts=["--quiet", "--overwrite", "--luma-only", "--gray", "--10bit"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="Y",
                bit_depth=16,
                chroma_subsampling=None,
            ),
        ),
        OutputTestCase(
            id="gray16le",
            input_opts=["--quiet", "--overwrite", "--luma-only", "--gray", "--16bit"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="Y",
                bit_depth=16,
                chroma_subsampling=None,
            ),
        ),
    ]

    audio_test_cases = [
        OutputTestCase(
            id="mux 1 audio track",
            input_opts=[
                "--quiet",
                "--overwrite",
                "--audio-track",
                "tests/files/audio.flac",
            ],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
            output_audio_base=[
                AudioBase(
                    format="FLAC",
                    bit_depth=16,
                    sampling_rate=44100,
                ),
            ],
        ),
        OutputTestCase(
            id="mux 2 audio tracks",
            input_opts=[
                "--quiet",
                "--overwrite",
                "--audio-track",
                "tests/files/audio.flac",
                "--audio-track",
                "tests/files/audio.flac",
            ],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
            output_audio_base=[
                AudioBase(
                    format="FLAC",
                    bit_depth=16,
                    sampling_rate=44100,
                ),
                AudioBase(
                    format="FLAC",
                    bit_depth=16,
                    sampling_rate=44100,
                ),
            ],
        ),
        OutputTestCase(
            id="mux audio tracks with advanced settings",
            input_opts=[
                "--quiet",
                "--overwrite",
                "--audio-track",
                "tests/files/audio.flac",
                "--audio-track-advanced",
                '["tests/files/audio_192_24.wav", "test 1", "eng", 192000, "s24le", 2]',  # noqa: E501
                "--audio-track-advanced",
                '["tests/files/audio_48_16.wav", "test 2", "eng", 48000, "s16le", 6, "5.1"]',  # noqa: E501
            ],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
            output_audio_base=[
                AudioBase(
                    format="FLAC",
                    bit_depth=16,
                    sampling_rate=44100,
                ),
                AudioBase(
                    title="test 1",
                    format="FLAC",
                    bit_depth=24,
                    sampling_rate=192000,
                    language="en",
                ),
                AudioBase(
                    title="test 2",
                    format="FLAC",
                    bit_depth=16,
                    sampling_rate=48000,
                    channel_s=6,
                    channel_layout="L R C LFE Lb Rb",
                    language="en",
                ),
            ],
        ),
    ]

    metadata_test_cases = [
        OutputTestCase(
            id="single metadata",
            input_opts=["--quiet", "--overwrite", "--metadata", "FOO", "BAR"],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
            output_metadata={"foo": "BAR"},
        ),
        OutputTestCase(
            id="multiple metadata",
            input_opts=[
                "--quiet",
                "--overwrite",
                "--metadata",
                "FOO",
                "BAR",
                "--metadata",
                "FAR",
                "BOO",
            ],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
            output_metadata={
                "foo": "BAR",
                "far": "BOO",
            },
        ),
        OutputTestCase(
            id="metadata file",
            input_opts=[
                "--quiet",
                "--overwrite",
                "--metadata-file",
                "tests/files/test.ffmetadata",
            ],
            input_tbc="pal_svideo",
            output_file="pal_svideo.mkv",
            output_video_codec=codec_ffv1,
            output_video_base=VideoBasePAL(),
            output_video_color=VideoColorPAL(
                color_space="YUV",
                bit_depth=10,
                chroma_subsampling="4:2:2",
            ),
            output_metadata={
                "TEST1": "Test",
                "TEST2": "Multi word test",
            },
        ),
    ]

    def check_video_track(
        self, test_case: OutputTestCase, media_info: MediaInfo
    ) -> None:
        """Check video track of output file."""
        video_track = media_info.video_tracks[0]

        # check video codec
        for k, v in test_case.output_video_codec.items():
            if v is not None:
                target_field = getattr(video_track, k, None)
                assert target_field is not None
                assert target_field == v

        # check video info
        for field in fields(test_case.output_video_base):
            if (value := getattr(test_case.output_video_base, field.name)) is not None:
                target_field = getattr(video_track, field.name, None)
                assert target_field is not None
                assert target_field == value

        # check video color
        for field in fields(test_case.output_video_color):
            if (value := getattr(test_case.output_video_color, field.name)) is not None:
                target_field = getattr(video_track, field.name, None)
                assert target_field is not None
                assert target_field == value

    def check_audio_tracks(
        self, test_case: OutputTestCase, media_info: MediaInfo
    ) -> None:
        """Check audio tracks of output file."""
        assert len(media_info.audio_tracks) == len(test_case.output_audio_base)

        track_idx = 0
        for test_track in test_case.output_audio_base:
            audio_track = media_info.audio_tracks[track_idx]

            for field in fields(test_track):
                if (value := getattr(test_track, field.name)) is not None:
                    target_field = getattr(audio_track, field.name, None)
                    assert target_field is not None
                    assert target_field == value

            track_idx += 1

    def check_metadata(self, test_case: OutputTestCase, media_info: MediaInfo) -> None:
        """Check metadata of output file."""
        assert media_info.general_tracks
        general_track = media_info.general_tracks[0]

        for k, v in test_case.output_metadata.items():
            if (
                v is not None
                and (target_field := getattr(general_track, k, None)) is not None
            ):
                assert target_field == v

    def run_output_validation(self, test_case: OutputTestCase) -> None:
        """Test output video files with mediainfo."""
        with test_case.expected_exc:
            main([f"tests/files/{test_case.input_tbc}", *test_case.input_opts])

            with Path(f"tests/files/{test_case.output_file}") as output_file:
                try:
                    assert output_file.is_file()

                    media_info = MediaInfo.parse(output_file)

                    assert isinstance(media_info, MediaInfo)
                    assert len(media_info.video_tracks) == 1

                    self.check_video_track(test_case, media_info)
                    self.check_audio_tracks(test_case, media_info)
                    self.check_metadata(test_case, media_info)

                finally:
                    # delete file
                    with suppress(FileNotFoundError):
                        output_file.unlink()

    @pytest.mark.parametrize(
        "test_case",
        (
            pytest.param(test_case, id=test_case.id)
            for test_case in pal_svideo_test_cases
        ),
    )
    def test_pal_svideo(self, test_case: OutputTestCase):  # noqa: D102
        self.run_output_validation(test_case)

    @pytest.mark.parametrize(
        "test_case",
        (
            pytest.param(test_case, id=test_case.id)
            for test_case in pal_composite_test_cases
        ),
    )
    def test_pal_composite(self, test_case: OutputTestCase):  # noqa: D102
        self.run_output_validation(test_case)

    @pytest.mark.parametrize(
        "test_case",
        (
            pytest.param(test_case, id=test_case.id)
            for test_case in pal_composite_ld_test_cases
        ),
    )
    def test_pal_composite_ld(self, test_case: OutputTestCase):  # noqa: D102
        self.run_output_validation(test_case)

    @pytest.mark.parametrize(
        "test_case",
        (
            pytest.param(test_case, id=test_case.id)
            for test_case in ntsc_svideo_test_cases
        ),
    )
    def test_ntsc_svideo(self, test_case: OutputTestCase):  # noqa: D102
        self.run_output_validation(test_case)

    @pytest.mark.parametrize(
        "test_case",
        (
            pytest.param(test_case, id=test_case.id)
            for test_case in ntsc_composite_test_cases
        ),
    )
    def test_ntsc_composite(self, test_case: OutputTestCase):  # noqa: D102
        self.run_output_validation(test_case)

    @pytest.mark.parametrize(
        "test_case",
        (
            pytest.param(test_case, id=test_case.id)
            for test_case in ntsc_composite_ld_test_cases
        ),
    )
    def test_ntsc_composite_ld(self, test_case: OutputTestCase):  # noqa: D102
        self.run_output_validation(test_case)

    @pytest.mark.parametrize(
        "test_case",
        (
            pytest.param(test_case, id=test_case.id)
            for test_case in palm_svideo_test_cases
        ),
    )
    def test_palm_svideo(self, test_case: OutputTestCase):  # noqa: D102
        self.run_output_validation(test_case)

    @pytest.mark.parametrize(
        "test_case",
        (
            pytest.param(test_case, id=test_case.id)
            for test_case in video_format_test_cases
        ),
    )
    def test_video_formats(self, test_case: OutputTestCase):  # noqa: D102
        self.run_output_validation(test_case)

    @pytest.mark.parametrize(
        "test_case",
        (pytest.param(test_case, id=test_case.id) for test_case in audio_test_cases),
    )
    def test_audio_muxing(self, test_case: OutputTestCase):  # noqa: D102
        self.run_output_validation(test_case)

    @pytest.mark.parametrize(
        "test_case",
        (pytest.param(test_case, id=test_case.id) for test_case in metadata_test_cases),
    )
    def test_metadata(self, test_case: OutputTestCase):  # noqa: D102
        self.run_output_validation(test_case)
