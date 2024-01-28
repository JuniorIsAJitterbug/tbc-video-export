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


class TestWrappersNTSCSvideo(unittest.TestCase):
    """Test wrapper opts for NTSC S-Video (Y+C) TBC."""

    def setUp(self) -> None:  # noqa: D102
        self.path = Path.joinpath(Path(__file__).parent, "files", "ntsc_svideo")
        self.tbc_json = Path.joinpath(
            Path(__file__).parent, "files", "ntsc_svideo.tbc.json"
        )

        self.config = ProgramConfig()
        self.parse_opts = partial(opts_parser.parse_opts, self.config)

        self.pipe = PipeFactory.create_dummy_pipe()

    def test_videosystem(self) -> None:  # noqa: D102
        _, opts = self.parse_opts([str(self.path), "ntsc_svideo"])
        self.files = FileHelper(opts, self.config)
        self.assertTrue(self.files.tbc_json.video_system, VideoSystem.PAL)

    def test_decoder_default_luma_decoder_ntsc_svideo(self) -> None:  # noqa: D102
        _, opts = self.parse_opts([str(self.path), "ntsc_svideo", "--threads", "4"])
        self.files = FileHelper(opts, self.config)
        state = ProgramState(opts, self.config, self.files)

        decoder = WrapperLDChromaDecoder(
            state,
            WrapperConfig[Pipe, Pipe](
                state.current_export_mode,
                TBCType.LUMA,
                input_pipes=self.pipe,
                output_pipes=self.pipe,
            ),
        )

        self.assertEqual(
            str(decoder.command),
            f"{self.files.get_tool(ProcessName.LD_CHROMA_DECODER)} "
            f"--chroma-gain 0 "
            f"-p y4m "
            f"-f mono "
            f"-t 4 "
            f"--ntsc-phase-comp "
            f"--input-json {self.path}.tbc.json "
            f"PIPE_IN "
            f"PIPE_OUT",
        )

    def test_decoder_default_chroma_decoder_ntsc_svideo(self) -> None:  # noqa: D102
        _, opts = self.parse_opts([str(self.path), "ntsc_svideo", "--threads", "4"])
        self.files = FileHelper(opts, self.config)
        state = ProgramState(opts, self.config, self.files)

        decoder = WrapperLDChromaDecoder(
            state,
            WrapperConfig[Pipe, Pipe](
                state.current_export_mode,
                TBCType.CHROMA,
                input_pipes=self.pipe,
                output_pipes=self.pipe,
            ),
        )

        self.assertEqual(
            str(decoder.command),
            f"{self.files.get_tool(ProcessName.LD_CHROMA_DECODER)} "
            f"--luma-nr 0 "
            f"-p y4m "
            f"-f ntsc2d "
            f"-t 4 "
            f"--ntsc-phase-comp "
            f"--input-json {self.path}.tbc.json "
            f"PIPE_IN "
            f"PIPE_OUT",
        )

    def test_ffmpeg_opts_ntsc_svideo(self) -> None:
        """Test FFmpeg opts for NTSC S-Video (Y+C) TBCs.

        General
        Unique ID                                : 23410690034527633882498040415764143156 (0x119CBC221EA9A0F937D6C9728090DC34)
        Complete name                            : ntsc_svideo.mkv
        Format                                   : Matroska
        Format version                           : Version 4
        File size                                : 405 KiB
        Duration                                 : 33 ms
        Overall bit rate mode                    : Variable
        Overall bit rate                         : 101 Mb/s
        Frame rate                               : 29.970 FPS
        Writing application                      : Lavf60.3.100
        Writing library                          : Lavf60.3.100
        ErrorDetectionType                       : Per level 1
        Attachments                              : ntsc_svideo.tbc.json
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
        _, opts = self.parse_opts([str(self.path), "ntsc_svideo", "--threads", "4"])
        self.files = FileHelper(opts, self.config)
        state = ProgramState(opts, self.config, self.files)

        ffmpeg_wrapper = WrapperFFmpeg(
            state,
            WrapperConfig[tuple[Pipe], None](
                state.current_export_mode,
                TBCType.CHROMA,
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
                    "[1:v]format=yuv422p10le[chroma];[0:v][chroma]mergeplanes=0x001112:format=yuv422p10le,setfield=tff[v_output]",
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

    def test_ffmpeg_opts_ntsc_svideo_luma(self) -> None:
        """Test FFmpeg opts for luma only NTSC S-Video (Y+C) TBCs.

        General
        Unique ID                                : 293296624786061163447218925330033371410 (0xDCA6E00ED4FD97BB5E653B9735756912)
        Complete name                            : ntsc_svideo_luma.mkv
        Format                                   : Matroska
        Format version                           : Version 4
        File size                                : 153 KiB
        Duration                                 : 33 ms
        Overall bit rate mode                    : Variable
        Overall bit rate                         : 37.9 Mb/s
        Frame rate                               : 29.970 FPS
        Writing application                      : Lavf60.3.100
        Writing library                          : Lavf60.3.100
        ErrorDetectionType                       : Per level 1
        Attachments                              : ntsc_svideo.tbc.json
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
                "ntsc_svideo",
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
                    "[0:v]null,setfield=tff[v_output]",
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

    def test_ffmpeg_opts_ntsc_svideo_luma_4fsc(self) -> None:
        """Test FFmpeg opts for luma 4FSC NTSC S-Video (Y+C) TBCs.

        General
        Unique ID                                : 125210076947971285552448551447492774605 (0x5E32956A4DB29E2C8337A102E60B4ACD)
        Complete name                            : ntsc_svideo_luma_4fsc.mkv
        Format                                   : Matroska
        Format version                           : Version 4
        File size                                : 168 KiB
        Duration                                 : 33 ms
        Overall bit rate mode                    : Variable
        Overall bit rate                         : 41.8 Mb/s
        Frame rate                               : 29.970 FPS
        Writing application                      : Lavf60.3.100
        Writing library                          : Lavf60.3.100
        ErrorDetectionType                       : Per level 1
        Attachments                              : ntsc_svideo.tbc.json
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
                "ntsc_svideo",
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
