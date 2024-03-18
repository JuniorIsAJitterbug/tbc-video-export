from __future__ import annotations

import unittest
from functools import partial
from pathlib import Path

from tbc_video_export.common.enums import ProcessName, TBCType, VideoSystem
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


class TestWrappersNTSCComposite(unittest.TestCase):
    """Test wrapper opts for NTSC Composite (CVBS) TBC."""

    def setUp(self) -> None:  # noqa: D102
        self.path = Path.joinpath(Path(__file__).parent, "files", "ntsc_composite")
        self.tbc_json = Path.joinpath(
            Path(__file__).parent, "files", "ntsc_composite.tbc.json"
        )

        self.config = ProgramConfig()
        self.parse_opts = partial(opts_parser.parse_opts, self.config)

        self.pipe = PipeFactory.create_dummy_pipe()

    def test_videosystem(self) -> None:  # noqa: D102
        _, opts = self.parse_opts(
            [str(self.path), "ntsc_composite", "--input-tbc-json", str(self.tbc_json)]
        )
        self.files = FileHelper(opts, self.config)
        self.assertTrue(self.files.tbc_json.video_system, VideoSystem.NTSC)

    def test_default_decoder_ntsc_cvbs(self) -> None:  # noqa: D102
        _, opts = opts_parser.parse_opts(
            self.config,
            [
                str(self.path),
                "ntsc_composite",
                "--input-tbc-json",
                str(self.tbc_json),
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
            f"{self.files.get_tool(ProcessName.LD_CHROMA_DECODER)} "
            f"-p y4m "
            f"-f ntsc3d "
            f"-t 4 "
            f"--ntsc-phase-comp "
            f"--input-json {self.tbc_json} "
            f"PIPE_IN "
            f"PIPE_OUT",
        )

    def test_ffmpeg_opts_ntsc_cvbs(self) -> None:
        """Test FFmpeg opts for Composite (CVBS) NTSC TBC.

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
        _, opts = opts_parser.parse_opts(
            self.config,
            [
                str(self.path),
                "ntsc_composite",
                "--input-tbc-json",
                str(self.tbc_json),
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
                    f"{self.files.get_tool(ProcessName.FFMPEG)}",
                    "-hide_banner",
                    "-loglevel error",
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
                    "[0:v]setfield=tff[v_output]",
                    "-map [v_output]",
                    "-timecode 00:00:00:00",
                    "-framerate ntsc",
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

    def test_ffmpeg_opts_ntsc_cvbs_luma(self) -> None:
        """Test FFmpeg opts for luma only Composite (CVBS) NTSC TBC.

        General
        Unique ID                                : 186105228103018445559182721721580153494 (0x8C02902B52C7BD095D9CFA4035046A96)
        Complete name                            : ntsc_composite_luma_4fsc.mkv
        Format                                   : Matroska
        Format version                           : Version 4
        File size                                : 123 KiB
        Duration                                 : 33 ms
        Overall bit rate mode                    : Variable
        Overall bit rate                         : 30.5 Mb/s
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
        _, opts = self.parse_opts(
            [
                str(self.path),
                "ntsc_composite",
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
                    f"{self.files.get_tool(ProcessName.FFMPEG)}",
                    "-hide_banner",
                    "-loglevel error",
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
                    "-color_range tv",
                    "-colorspace smpte170m",
                    "-color_primaries smpte170m",
                    "-color_trc bt709",
                    "-pix_fmt gray16le",
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

    def test_ffmpeg_opts_ntsc_cvbs_luma_4fsc(self) -> None:
        """Test FFmpeg opts for luma 4FSC Composite (CVBS) NTSC TBC.

        General
        Unique ID                                : 186105228103018445559182721721580153494 (0x8C02902B52C7BD095D9CFA4035046A96)
        Complete name                            : ntsc_composite_luma_4fsc.mkv
        Format                                   : Matroska
        Format version                           : Version 4
        File size                                : 123 KiB
        Duration                                 : 33 ms
        Overall bit rate mode                    : Variable
        Overall bit rate                         : 30.5 Mb/s
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
        _, opts = self.parse_opts(
            [
                str(self.path),
                "ntsc_composite",
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
                    f"{self.files.get_tool(ProcessName.FFMPEG)}",
                    "-hide_banner",
                    "-loglevel error",
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
                    "-color_range tv",
                    "-colorspace smpte170m",
                    "-color_primaries smpte170m",
                    "-color_trc bt709",
                    "-pix_fmt gray16le",
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
