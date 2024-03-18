from __future__ import annotations

import unittest
from functools import partial
from pathlib import Path

from tbc_video_export.common.enums import TBCType
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

    def test_ffmpeg_format_10bit(self) -> None:  # noqa: D102
        _, opts = self.parse_opts([str(self.path), "pal_svideo", "--10bit"])
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

        cmd = ffmpeg_wrapper.command.data
        self.assertTrue(any(",format=yuv422p10le" in cmds for cmds in cmd))

    def test_ffmpeg_format_16bit(self) -> None:  # noqa: D102
        _, opts = self.parse_opts([str(self.path), "pal_svideo", "--16bit"])
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

        cmd = ffmpeg_wrapper.command.data
        self.assertTrue(any(",format=yuv422p16le" in cmds for cmds in cmd))

    def test_ffmpeg_format_yuv444_8bit(self) -> None:  # noqa: D102
        _, opts = self.parse_opts([str(self.path), "pal_svideo", "--yuv444", "--8bit"])
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

        cmd = ffmpeg_wrapper.command.data
        self.assertTrue(any(",format=yuv444p" in cmds for cmds in cmd))

    def test_ffmpeg_format_yuv444_10bit(self) -> None:  # noqa: D102
        _, opts = self.parse_opts([str(self.path), "pal_svideo", "--yuv444", "--10bit"])
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

        cmd = ffmpeg_wrapper.command.data
        self.assertTrue(any(",format=yuv444p10le" in cmds for cmds in cmd))

    def test_ffmpeg_format_yuv444_16bit(self) -> None:  # noqa: D102
        _, opts = self.parse_opts([str(self.path), "pal_svideo", "--yuv444", "--16bit"])
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

        cmd = ffmpeg_wrapper.command.data
        self.assertTrue(any(",format=yuv444p16le" in cmds for cmds in cmd))

    def test_ffmpeg_format_luma(self) -> None:  # noqa: D102
        _, opts = self.parse_opts([str(self.path), "pal_svideo", "--luma-only"])
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

        cmd = ffmpeg_wrapper.command.data
        self.assertTrue(any(",format=gray16le" in cmds for cmds in cmd))

    def test_ffmpeg_format_luma_16bit(self) -> None:  # noqa: D102
        _, opts = self.parse_opts(
            [str(self.path), "pal_svideo", "--luma-only", "--16bit"]
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

        cmd = ffmpeg_wrapper.command.data
        self.assertTrue(any(",format=gray16le" in cmds for cmds in cmd))
