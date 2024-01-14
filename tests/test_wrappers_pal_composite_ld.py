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


class TestWrappersPALCompositeLD(unittest.TestCase):
    """Test wrapper opts for PAL Composite (CVBS) LD TBC."""

    def setUp(self) -> None:  # noqa: D102
        self.path = Path.joinpath(Path(__file__).parent, "files", "pal_composite_ld")
        self.tbc_json = Path.joinpath(
            Path(__file__).parent, "files", "pal_composite_ld.tbc.json"
        )

        self.config = ProgramConfig()
        self.parse_opts = partial(opts_parser.parse_opts, self.config)

        self.pipe = PipeFactory.create_dummy_pipe()

    def test_videosystem(self) -> None:  # noqa: D102
        opts = self.parse_opts(
            [str(self.path), "pal_composite_ld", "--input-tbc-json", str(self.tbc_json)]
        )
        self.files = FileHelper(opts, self.config)
        self.assertTrue(self.files.tbc_json.video_system, VideoSystem.PAL)

    def test_ld_detect(self) -> None:  # noqa: D102
        opts = self.parse_opts(
            [str(self.path), "pal_composite_ld", "--input-tbc-json", str(self.tbc_json)]
        )
        self.files = FileHelper(opts, self.config)
        self.assertTrue(self.files.is_combined_ld)

    def test_default_decoder_pal_ld(self) -> None:  # noqa: D102
        opts = opts_parser.parse_opts(
            self.config,
            [
                str(self.path),
                "pal_composite_ld",
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
            f"--luma-nr 0 "
            f"-p y4m "
            f"-f transform3d "
            f"-t 4 "
            f"--input-json {self.tbc_json} "
            f"PIPE_IN "
            f"PIPE_OUT",
        )

    def test_ffmpeg_opts_pal_ld(self) -> None:
        """Test FFmpeg opts for Composite (CVBS) PAL LD TBC.

        General
        Unique ID                                : 161401761525858677167728531271771700241 (0x796CD93B399179AD62C3B1347F133C11)
        Complete name                            : pal_composite_ld.mkv
        Format                                   : Matroska
        Format version                           : Version 4
        File size                                : 1.10 MiB
        Duration                                 : 80 ms
        Overall bit rate mode                    : Variable
        Overall bit rate                         : 116 Mb/s
        Frame rate                               : 25.000 FPS
        Writing application                      : Lavf60.3.100
        Writing library                          : Lavf60.3.100
        ErrorDetectionType                       : Per level 1
        Attachments                              : pal_composite_ld.tbc.json
        Time code of first frame                 : 00:00:00:00
        Time code source                         : Matroska tags

        Video
        ID                                       : 1
        Format                                   : FFV1
        Format version                           : Version 3.4
        Format settings, GOP                     : N=1
        Codec ID                                 : V_MS/VFW/FOURCC / FFV1
        Duration                                 : 80 ms
        Bit rate mode                            : Variable
        Width                                    : 928 pixels
        Height                                   : 576 pixels
        Display aspect ratio                     : 4:3
        Frame rate mode                          : Constant
        Frame rate                               : 25.000 FPS
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
        Color primaries                          : BT.601 PAL
        Transfer characteristics                 : BT.709
        Matrix coefficients                      : BT.470 System B/G
        coder_type                               : Range Coder
        MaxSlicesCount                           : 24
        ErrorDetectionType                       : Per slice
        """  # noqa: E501
        opts = opts_parser.parse_opts(
            self.config,
            [
                str(self.path),
                "pal_composite_ld",
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
                    "-framerate pal",
                    "-aspect 4:3",
                    "-color_range tv",
                    "-colorspace bt470bg",
                    "-color_primaries bt470bg",
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

    def test_ffmpeg_opts_pal_ld_luma(self) -> None:
        """Test FFmpeg opts for luma only Composite (CVBS) LD PAL TBC.

        General
        Unique ID                                : 172568283220807751268919922854068581357 (0x81D37141D2F41F8DA5D258D4349573ED)
        Complete name                            : pal_composite_ld_luma.mkv
        Format                                   : Matroska
        Format version                           : Version 4
        File size                                : 469 KiB
        Duration                                 : 80 ms
        Overall bit rate mode                    : Variable
        Overall bit rate                         : 48.1 Mb/s
        Frame rate                               : 25.000 FPS
        Writing application                      : Lavf60.3.100
        Writing library                          : Lavf60.3.100
        ErrorDetectionType                       : Per level 1
        Attachments                              : pal_composite_ld.tbc.json
        Time code of first frame                 : 00:00:00:00
        Time code source                         : Matroska tags

        Video
        ID                                       : 1
        Format                                   : FFV1
        Format version                           : Version 3.4
        Format settings, GOP                     : N=1
        Codec ID                                 : V_MS/VFW/FOURCC / FFV1
        Duration                                 : 80 ms
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
                str(self.path),
                "pal_composite_ld",
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
                    "-framerate pal",
                    "-aspect 4:3",
                    "-color_range tv",
                    "-colorspace bt470bg",
                    "-color_primaries bt470bg",
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

    def test_ffmpeg_opts_pal_ld_luma_4fsc(self) -> None:
        """Test FFmpeg opts for luma 4FSC Composite (CVBS) LD PAL TBC.

        General
        Unique ID                                : 192228378941771277770153031373529157278 (0x909DD6D056B9E430320C7907BB9A0E9E)
        Complete name                            : pal_composite_ld_luma_4fsc.mkv
        Format                                   : Matroska
        Format version                           : Version 4
        File size                                : 788 KiB
        Duration                                 : 80 ms
        Overall bit rate mode                    : Variable
        Overall bit rate                         : 80.7 Mb/s
        Frame rate                               : 25.000 FPS
        Writing application                      : Lavf60.3.100
        Writing library                          : Lavf60.3.100
        ErrorDetectionType                       : Per level 1
        Attachments                              : pal_composite_ld.tbc.json
        Time code of first frame                 : 00:00:00:00
        Time code source                         : Matroska tags

        Video
        ID                                       : 1
        Format                                   : FFV1
        Format version                           : Version 3.4
        Format settings, GOP                     : N=1
        Codec ID                                 : V_MS/VFW/FOURCC / FFV1
        Duration                                 : 80 ms
        Bit rate mode                            : Variable
        Width                                    : 1 135 pixels
        Height                                   : 626 pixels
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
                str(self.path),
                "pal_composite_ld",
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
                    "-loglevel verbose",
                    "-progress pipe:2",
                    "-threads 4",
                    "-nostdin",
                    "-hwaccel auto",
                    "-color_range tv",
                    "-f rawvideo",
                    "-pix_fmt gray16le",
                    "-framerate pal",
                    "-video_size 1135x626",
                    "-thread_queue_size 1024",
                    f"-i {self.files.tbc_luma}",
                    "-filter_complex",
                    "[0:v]il=l=i:c=i,setfield=tff[v_output]",
                    "-map [v_output]",
                    "-timecode 00:00:00:00",
                    "-framerate pal",
                    "-aspect 4:3",
                    "-color_range tv",
                    "-colorspace bt470bg",
                    "-color_primaries bt470bg",
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
