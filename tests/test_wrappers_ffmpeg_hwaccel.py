from __future__ import annotations

import unittest
from functools import partial
from pathlib import Path

from tbc_video_export.common.enums import TBCType
from tbc_video_export.common.exceptions import InvalidProfileError
from tbc_video_export.common.file_helper import FileHelper
from tbc_video_export.config import Config as ProgramConfig
from tbc_video_export.opts import opts_parser
from tbc_video_export.process.wrapper import WrapperConfig
from tbc_video_export.process.wrapper.pipe import Pipe, PipeFactory
from tbc_video_export.process.wrapper.wrapper_ffmpeg import WrapperFFmpeg
from tbc_video_export.program_state import ProgramState


class TestWrappersFFmpeg(unittest.TestCase):
    """Tests for ffmpeg wrapper."""

    def setUp(self) -> None:  # noqa: D102
        self.path = Path.joinpath(Path(__file__).parent, "files", "pal_svideo")

        self.config = ProgramConfig()
        self.parse_opts = partial(opts_parser.parse_opts, self.config)

        self.pipe = PipeFactory.create_dummy_pipe()

    def test_ffmpeg_hwaccel_vaapi(self) -> None:  # noqa: D102
        _, opts = self.parse_opts(
            [
                str(self.path),
                "pal_svideo",
                "--x264_web",
                "--vaapi",
                "--hwaccel-device",
                "TEST",
            ]
        )
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

        self.assertTrue(
            {
                "-hwaccel",
                "vaapi",
            }.issubset(ffmpeg_wrapper.command.data)
        )

        self.assertTrue(
            {
                "-hwaccel_output_format",
                "vaapi",
            }.issubset(ffmpeg_wrapper.command.data)
        )

        self.assertTrue(
            {
                "-vaapi_device",
                "TEST",
            }.issubset(ffmpeg_wrapper.command.data)
        )

        self.assertTrue(
            {
                "-c:v",
                "h264_vaapi",
            }.issubset(ffmpeg_wrapper.command.data)
        )

        cmd = ffmpeg_wrapper.command.data
        self.assertTrue(any("hwupload[v_output]" in cmds for cmds in cmd))

    def test_ffmpeg_hwaccel_nvenc(self) -> None:  # noqa: D102
        _, opts = self.parse_opts(
            [
                str(self.path),
                "pal_svideo",
                "--x264_web",
                "--nvenc",
                "--hwaccel-device",
                "TEST",
            ]
        )
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

        self.assertTrue(
            {
                "-gpu",
                "TEST",
            }.issubset(ffmpeg_wrapper.command.data)
        )

        self.assertTrue(
            {
                "-c:v",
                "h264_nvenc",
            }.issubset(ffmpeg_wrapper.command.data)
        )

    def test_ffmpeg_hwaccel_quicksync(self) -> None:  # noqa: D102
        _, opts = self.parse_opts(
            [
                str(self.path),
                "pal_svideo",
                "--x264_web",
                "--quicksync",
                "--hwaccel-device",
                "TEST",
            ]
        )
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

        self.assertTrue(
            {
                "-hwaccel",
                "qsv",
            }.issubset(ffmpeg_wrapper.command.data)
        )

        self.assertTrue(
            {
                "-hwaccel_output_format",
                "qsv",
            }.issubset(ffmpeg_wrapper.command.data)
        )

        self.assertTrue(
            {
                "-qsv_device",
                "TEST",
            }.issubset(ffmpeg_wrapper.command.data)
        )

        self.assertTrue(
            {
                "-c:v",
                "h264_qsv",
            }.issubset(ffmpeg_wrapper.command.data)
        )

    def test_ffmpeg_hwaccel_amf(self) -> None:  # noqa: D102
        _, opts = self.parse_opts(
            [
                str(self.path),
                "pal_svideo",
                "--x264_web",
                "--amf",
            ]
        )
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

        self.assertTrue(
            {
                "-c:v",
                "h264_amf",
            }.issubset(ffmpeg_wrapper.command.data)
        )

    def test_ffmpeg_hwaccel_amf_device(self) -> None:  # noqa: D102
        _, opts = self.parse_opts(
            [
                str(self.path),
                "pal_svideo",
                "--x264_web",
                "--amf",
                "--hwaccel-device",
                "TEST",
            ]
        )
        self.files = FileHelper(opts, self.config)
        state = ProgramState(opts, self.config, self.files)

        with self.assertRaises(InvalidProfileError):
            WrapperFFmpeg(
                state,
                WrapperConfig[tuple[Pipe], None](
                    state.current_export_mode,
                    TBCType.CHROMA,
                    input_pipes=(self.pipe, self.pipe),
                    output_pipes=None,
                ),
            )

    def test_ffmpeg_hwaccel_videotoolbox(self) -> None:  # noqa: D102
        _, opts = self.parse_opts(
            [
                str(self.path),
                "pal_svideo",
                "--x264_web",
                "--videotoolbox",
            ]
        )
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

        self.assertTrue(
            {
                "-c:v",
                "h264_videotoolbox",
            }.issubset(ffmpeg_wrapper.command.data)
        )
