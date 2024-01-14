from __future__ import annotations

import unittest
from functools import partial

from path import Path
from tbc_video_export.common.enums import TBCType, VideoSystem
from tbc_video_export.common.file_helper import FileHelper
from tbc_video_export.config import Config as ProgramConfig
from tbc_video_export.opts import opts_parser
from tbc_video_export.process.wrapper import WrapperConfig
from tbc_video_export.process.wrapper.pipe import Pipe, PipeFactory
from tbc_video_export.process.wrapper.wrapper_ffmpeg import WrapperFFmpeg
from tbc_video_export.process.wrapper.wrapper_ld_chroma_decoder import (
    WrapperLDChromaDecoder,
)
from tbc_video_export.program_state import ProgramState


class TestWrappersNTSCCompositeLD(unittest.TestCase):
    """Test wrapper opts for NTSC Composite (CVBS) LD TBC."""

    def setUp(self) -> None:  # noqa: D102
        self.path = Path.joinpath(Path(__file__).parent, "files", "ntsc_composite_ld")
        self.tbc_json = Path.joinpath(
            Path(__file__).parent, "files", "ntsc_composite_ld.tbc.json"
        )

        self.config = ProgramConfig()
        self.parse_opts = partial(opts_parser.parse_opts, self.config)

        self.pipe = PipeFactory.create_dummy_pipe()

    def test_videosystem(self) -> None:  # noqa: D102
        opts = self.parse_opts(
            [self.path, "ntsc_composite_ld", "--input-tbc-json", self.tbc_json]
        )
        self.files = FileHelper(opts, self.config)
        self.assertTrue(self.files.tbc_json.video_system, VideoSystem.NTSC)

    def test_ld_detect(self) -> None:  # noqa: D102
        opts = self.parse_opts(
            [self.path, "ntsc_composite_ld", "--input-tbc-json", self.tbc_json]
        )
        self.files = FileHelper(opts, self.config)
        self.assertTrue(self.files.is_combined_ld)

    def test_default_decoder_ntsc_ld(self) -> None:  # noqa: D102
        opts = opts_parser.parse_opts(
            self.config,
            [
                self.path,
                "ntsc_composite_ld",
                "--input-tbc-json",
                self.tbc_json,
                "--threads",
                "4",
            ],
        )
        self.files = FileHelper(opts, self.config)
        state = ProgramState(opts, self.config, self.files)

        decoder = WrapperLDChromaDecoder(
            state,
            WrapperConfig[Pipe, Pipe](
                state.current_export_mode,
                TBCType.COMBINED,
                input_pipes=self.pipe,
                output_pipes=self.pipe,
            ),
        )

        self.assertEqual(
            str(decoder.command),
            f"ld-chroma-decoder "
            f"--luma-nr 0 "
            f"-p y4m "
            f"-f ntsc2d "
            f"-t 4 "
            f"--input-json {self.tbc_json} "
            f"PIPE_IN "
            f"PIPE_OUT",
        )

    def test_ffmpeg_opts_ntsc_ld(self) -> None:
        """Test FFmpeg opts for Composite (CVBS) NTSC LD TBC.

        General
        Unique ID                                : 269537316766470028691717893346617501383 (0xCAC6FFBB1FB4228F0D825C37EA2CA6C7)
        Complete name                            : ntsc_composite.mkv
        Format                                   : Matroska
        Format version                           : Version 4
        File size                                : 251 KiB
        Duration                                 : 33 ms
        Overall bit rate mode                    : Variable
        Overall bit rate                         : 62.2 Mb/s
        Frame rate                               : 29.970 FPS
        Writing application                      : Lavf60.3.100
        Writing library                          : Lavf60.3.100
        ErrorDetectionType                       : Per level 1
        Attachments                              : ntsc_composite.tbc.json
        Time code of first frame                 : 00:00:00:00
        Time code source                         : Matroska tags

        Video
        ID                                       : 1
        Format                                   : FFV1
        Format version                           : Version 3.4
        Format settings, GOP                     : N=1
        Codec ID                                 : V_MS/VFW/FOURCC / FFV1
        Duration                                 : 33 ms
        Bit rate mode                            : Variable
        Width                                    : 760 pixels
        Height                                   : 488 pixels
        Display aspect ratio                     : 4:3
        Frame rate mode                          : Constant
        Frame rate                               : 29.970 (30000/1001) FPS
        Color space                              : YUV
        Chroma subsampling                       : 4:2:2
        Bit depth                                : 10 bits
        Scan type                                : Interlaced
        Scan type, store method                  : Interleaved fields
        Scan order                               : Top Field First
        Compression mode                         : Lossless
        Writing library                          : Lavc60.3.100 ffv1
        Default                                  : No
        Forced                                   : No
        Color range                              : Limited
        Color primaries                          : BT.601 NTSC
        Transfer characteristics                 : BT.709
        Matrix coefficients                      : BT.601
        coder_type                               : Range Coder
        MaxSlicesCount                           : 24
        ErrorDetectionType                       : Per slice
        """  # noqa: E501
        opts = opts_parser.parse_opts(
            self.config,
            [
                self.path,
                "ntsc_composite_ld",
                "--input-tbc-json",
                self.tbc_json,
                "--threads",
                "4",
            ],
        )
        self.files = FileHelper(opts, self.config)
        state = ProgramState(opts, self.config, self.files)

        ffmpeg_wrapper = WrapperFFmpeg(
            state,
            WrapperConfig[tuple[Pipe], None](
                state.current_export_mode,
                TBCType.COMBINED,
                input_pipes=(self.pipe, self.pipe),
                output_pipes=None,
            ),
        )

        self.maxDiff = None

        if state.profile.audio_profile is None:
            self.assertTrue(False)

        self.assertEqual(
            str(ffmpeg_wrapper.command),
            " ".join(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel verbose",
                    "-progress pipe:2",
                    "-threads 4",
                    "-nostdin",
                    "-hwaccel auto",
                    "-color_range tv",
                    "-thread_queue_size 1024",
                    "-i PIPE_IN",
                    "-thread_queue_size 1024",
                    "-i PIPE_IN",
                    "-filter_complex",
                    "[0:v]null,setfield=tff[v_output]",
                    "-map [v_output]",
                    "-timecode 00:00:00:00",
                    "-framerate ntsc",
                    "-aspect 4:3",
                    "-color_range tv",
                    "-colorspace smpte170m",
                    "-color_primaries smpte170m",
                    "-color_trc bt709",
                    "-pix_fmt yuv422p10le",
                    f"-c:v {state.profile.video_profile.codec}",
                    f"{state.profile.video_profile.opts}",
                    f"-c:a {state.profile.audio_profile.codec}",  # pyright:  ignore [reportOptionalMemberAccess]
                    f"{state.profile.audio_profile.opts}",  # pyright:  ignore [reportOptionalMemberAccess]
                    f"-attach {self.tbc_json}",
                    "-metadata:s:t:0 mimetype=application/json",
                    f"{self.files.output_video_file}",
                ]
            ),
        )

    def test_ffmpeg_opts_ntsc_ld_luma(self) -> None:
        """Test FFmpeg opts for luma only Composite (CVBS) LD NTSC TBC.

        General
        Unique ID                                : 324488904309794552468304505864414603046 (0xF41E4A2C9BA4A3C86D2BE699D644A726)
        Complete name                            : ntsc_composite_luma.mkv
        Format                                   : Matroska
        Format version                           : Version 4
        File size                                : 183 KiB
        Duration                                 : 40 ms
        Overall bit rate mode                    : Variable
        Overall bit rate                         : 37.4 Mb/s
        Frame rate                               : 25.000 FPS
        Writing application                      : Lavf60.3.100
        Writing library                          : Lavf60.3.100
        ErrorDetectionType                       : Per level 1
        Attachments                              : pal_composite.tbc.json
        Time code of first frame                 : 00:00:00:00
        Time code source                         : Matroska tags

        Video
        ID                                       : 1
        Format                                   : FFV1
        Format version                           : Version 3.4
        Format settings, GOP                     : N=1
        Codec ID                                 : V_MS/VFW/FOURCC / FFV1
        Duration                                 : 40 ms
        Bit rate mode                            : Variable
        Width                                    : 928 pixels
        Height                                   : 576 pixels
        Display aspect ratio                     : 4:3
        Frame rate mode                          : Constant
        Frame rate                               : 25.000 FPS
        Color space                              : Y
        Bit depth                                : 8 bits
        Scan type                                : Interlaced
        Scan type, store method                  : Interleaved fields
        Scan order                               : Top Field First
        Compression mode                         : Lossless
        Writing library                          : Lavc60.3.100 ffv1
        Default                                  : No
        Forced                                   : No
        Color range                              : Limited
        Color primaries                          : BT.601 PAL
        Transfer characteristics                 : BT.709
        Matrix coefficients                      : BT.470 System B/G
        coder_type                               : Range Coder
        MaxSlicesCount                           : 24
        ErrorDetectionType                       : Per slice
        """  # noqa: E501
        opts = self.parse_opts(
            [
                self.path,
                "ntsc_composite_ld",
                "--threads",
                "4",
                "--luma-only",
            ]
        )
        self.files = FileHelper(opts, self.config)
        state = ProgramState(opts, self.config, self.files)

        ffmpeg_wrapper = WrapperFFmpeg(
            state,
            WrapperConfig[tuple[Pipe], None](
                state.current_export_mode,
                TBCType.LUMA,
                input_pipes=(self.pipe,),
                output_pipes=None,
            ),
        )

        self.maxDiff = None

        if state.profile.audio_profile is None:
            self.assertTrue(False)

        self.assertEqual(
            str(ffmpeg_wrapper.command),
            " ".join(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel verbose",
                    "-progress pipe:2",
                    "-threads 4",
                    "-nostdin",
                    "-hwaccel auto",
                    "-color_range tv",
                    "-thread_queue_size 1024",
                    "-i PIPE_IN",
                    "-filter_complex",
                    "[0:v]extractplanes=y,setfield=tff[v_output]",
                    "-map [v_output]",
                    "-timecode 00:00:00:00",
                    "-framerate ntsc",
                    "-aspect 4:3",
                    "-color_range tv",
                    "-colorspace smpte170m",
                    "-color_primaries smpte170m",
                    "-color_trc bt709",
                    "-pix_fmt y8",
                    f"-c:v {state.profile.video_profile.codec}",
                    f"{state.profile.video_profile.opts}",
                    f"-c:a {state.profile.audio_profile.codec}",  # pyright:  ignore [reportOptionalMemberAccess]
                    f"{state.profile.audio_profile.opts}",  # pyright:  ignore [reportOptionalMemberAccess]
                    f"-attach {self.tbc_json}",
                    "-metadata:s:t:0 mimetype=application/json",
                    f"{self.files.output_video_file}",
                ]
            ),
        )

    def test_ffmpeg_opts_ntsc_ld_luma_4fsc(self) -> None:
        """Test FFmpeg opts for luma 4FSC Composite (CVBS) LD NTSC TBC.

        General
        Unique ID                                : 5818021118490484964194352093342346235 (0x46082967F7F691A7C04E13292162BFB)
        Complete name                            : ntsc_composite_ld_luma_4fsc.mkv
        Format                                   : Matroska
        Format version                           : Version 4
        File size                                : 411 KiB
        Duration                                 : 66 ms
        Overall bit rate mode                    : Variable
        Overall bit rate                         : 51.0 Mb/s
        Frame rate                               : 29.970 FPS
        Writing application                      : Lavf60.3.100
        Writing library                          : Lavf60.3.100
        ErrorDetectionType                       : Per level 1
        Attachments                              : ntsc_composite_ld.tbc.json
        Time code of first frame                 : 00:00:00:00
        Time code source                         : Matroska tags

        Video
        ID                                       : 1
        Format                                   : FFV1
        Format version                           : Version 3.4
        Format settings, GOP                     : N=1
        Codec ID                                 : V_MS/VFW/FOURCC / FFV1
        Duration                                 : 66 ms
        Bit rate mode                            : Variable
        Width                                    : 910 pixels
        Height                                   : 526 pixels
        Display aspect ratio                     : 4:3
        Frame rate mode                          : Constant
        Frame rate                               : 29.970 (30000/1001) FPS
        Color space                              : Y
        Bit depth                                : 8 bits
        Scan type                                : Interlaced
        Scan type, store method                  : Interleaved fields
        Scan order                               : Top Field First
        Compression mode                         : Lossless
        Writing library                          : Lavc60.3.100 ffv1
        Default                                  : No
        Forced                                   : No
        Color range                              : Limited
        Color primaries                          : BT.601 NTSC
        Transfer characteristics                 : BT.709
        Matrix coefficients                      : BT.601
        coder_type                               : Range Coder
        MaxSlicesCount                           : 24
        ErrorDetectionType                       : Per slice
        """  # noqa: E501
        opts = self.parse_opts(
            [
                self.path,
                "ntsc_composite_ld",
                "--threads",
                "4",
                "--luma-4fsc",
            ]
        )
        self.files = FileHelper(opts, self.config)
        state = ProgramState(opts, self.config, self.files)
        self.pipe = PipeFactory.create_dummy_pipe(stdin_str=self.files.tbc_luma)

        ffmpeg_wrapper = WrapperFFmpeg(
            state,
            WrapperConfig[tuple[Pipe], None](
                state.current_export_mode,
                TBCType.LUMA,
                input_pipes=(self.pipe,),
                output_pipes=None,
            ),
        )

        self.maxDiff = None

        if state.profile.audio_profile is None:
            self.assertTrue(False)

        self.assertEqual(
            str(ffmpeg_wrapper.command),
            " ".join(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel verbose",
                    "-progress pipe:2",
                    "-threads 4",
                    "-nostdin",
                    "-hwaccel auto",
                    "-color_range tv",
                    "-f rawvideo",
                    "-pix_fmt gray16le",
                    "-framerate ntsc",
                    "-video_size 910x526",
                    "-thread_queue_size 1024",
                    f"-i {self.files.tbc_luma}",
                    "-filter_complex",
                    "[0:v]il=l=i:c=i,setfield=tff[v_output]",
                    "-map [v_output]",
                    "-timecode 00:00:00:00",
                    "-framerate ntsc",
                    "-aspect 4:3",
                    "-color_range tv",
                    "-colorspace smpte170m",
                    "-color_primaries smpte170m",
                    "-color_trc bt709",
                    "-pix_fmt y8",
                    f"-c:v {state.profile.video_profile.codec}",
                    f"{state.profile.video_profile.opts}",
                    f"-c:a {state.profile.audio_profile.codec}",  # pyright:  ignore [reportOptionalMemberAccess]
                    f"{state.profile.audio_profile.opts}",  # pyright:  ignore [reportOptionalMemberAccess]
                    f"-attach {self.tbc_json}",
                    "-metadata:s:t:0 mimetype=application/json",
                    f"{self.files.output_video_file}",
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
