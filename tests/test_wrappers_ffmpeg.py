from __future__ import annotations

import unittest
from functools import partial
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from tbc_video_export.common.enums import TBCType
from tbc_video_export.common.exceptions import (
    InvalidProfileError,
)
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

    def test_ffmpeg_audio_track_opts(self) -> None:  # noqa: D102
        audio_track = "tests/files/audio.flac"
        _, opts = self.parse_opts(
            [str(self.path), "pal_svideo", "--audio-track", "tests/files/audio.flac"]
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
            {"-i", str(Path(audio_track).absolute())}.issubset(
                ffmpeg_wrapper.command.data
            )
        )

        self.assertTrue({"-map", "2:a"}.issubset(ffmpeg_wrapper.command.data))

    def test_ffmpeg_audio_track_advanced_opts(self) -> None:  # noqa: D102
        audio_track = "tests/files/audio.flac"
        _, opts = self.parse_opts(
            [
                str(self.path),
                "pal_svideo",
                "--audio-track-advanced",
                "["
                "'tests/files/audio.flac',"
                "'Test',"
                "'eng',"
                "44100,"
                "'s16le',"
                "2,"
                "'2.1',"
                "0.15"
                "]",
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

        cmd = ffmpeg_wrapper.command.data

        self.assertTrue(
            {
                "-itsoffset",
                "0.15",
                "-f",
                "s16le",
                "-ar",
                "44100",
                "-ac",
                "2",
                "-i",
                str(Path(audio_track).absolute()),
            }.issubset(cmd)
        )
        self.assertTrue({"-map", "2:a"}.issubset(cmd))
        self.assertTrue({"-metadata:s:a:0", "title=Test"}.issubset(cmd))
        self.assertTrue({"-metadata:s:a:0", "language=eng"}.issubset(cmd))
        self.assertTrue(
            {"-channel_layout:a:0", "2.1"}.issubset(ffmpeg_wrapper.command.data)
        )

    def test_ffmpeg_metadata_opts(self) -> None:  # noqa: D102
        _, opts = self.parse_opts(
            [
                str(self.path),
                "pal_svideo",
                "--metadata",
                "foo",
                "bar",
                "--metadata",
                "bar",
                "foo",
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

        cmd = ffmpeg_wrapper.command.data

        self.assertTrue({"-metadata", "foo=bar"}.issubset(cmd))
        self.assertTrue({"-metadata", "bar=foo"}.issubset(cmd))

    def test_ffmpeg_default_field_order_opt(self) -> None:  # noqa: D102
        _, opts = self.parse_opts([str(self.path), "pal_svideo"])
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

        self.assertTrue(any("setfield=tff" in cmds for cmds in cmd))

    def test_ffmpeg_field_order_opt(self) -> None:  # noqa: D102
        _, opts = self.parse_opts(
            [str(self.path), "pal_svideo", "--field-order", "bff"]
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

        self.assertTrue(any("setfield=bff" in cmds for cmds in cmd))

    @patch("sys.stderr", new_callable=StringIO)
    def test_ffmpeg_field_order_invalid_opt(self, mock_stderr: StringIO) -> None:  # noqa: D102
        # invalid option
        with self.assertRaises(SystemExit):
            _, __ = self.parse_opts(
                [str(self.path), "pal_svideo", "--field-order", "invalid"]
            )

        self.assertRegex(
            mock_stderr.getvalue(),
            r"error: argument --field-order: invalid FieldOrder value: 'invalid'",
        )

    def test_ffmpeg_override_container_opt(self) -> None:  # noqa: D102
        _, opts = self.parse_opts(
            [
                str(self.path),
                "pal_svideo",
                "--profile",
                "prores_hq",
                "--profile-container",
                "mxf",
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

        cmd = ffmpeg_wrapper.command.data

        self.assertTrue(any("pal_svideo.mxf" in cmds for cmds in cmd))

    def test_ffmpeg_add_filter_profile_opt(self) -> None:  # noqa: D102
        _, opts = self.parse_opts(
            [
                str(self.path),
                "pal_svideo",
                "--profile-add-filter",
                "bwdif",
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

        cmd = ffmpeg_wrapper.command.data

        self.assertTrue(any(",bwdif" in cmds for cmds in cmd))

    def test_ffmpeg_append_filters_opt(self) -> None:  # noqa: D102
        _, opts = self.parse_opts(
            [
                str(self.path),
                "pal_svideo",
                "--append-video-filter",
                "TEST_VIDEO_FILTER",
                "--append-other-filter",
                "TEST_OTHER_FILTER",
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

        cmd = ffmpeg_wrapper.command.data

        self.assertTrue(any(",TEST_VIDEO_FILTER[v_output]" in cmds for cmds in cmd))
        self.assertTrue(any("[v_output],TEST_OTHER_FILTER" in cmds for cmds in cmd))

    def test_ffmpeg_add_invalid_filter_profile_opt(self) -> None:  # noqa: D102
        _, opts = self.parse_opts(
            [
                str(self.path),
                "pal_svideo",
                "--profile-add-filter",
                "invalid",
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

    def test_ffmpeg_test_invalid_filter_str_opt(self) -> None:  # noqa: D102
        _, opts = self.parse_opts(
            [
                str(self.path),
                "pal_svideo",
                "--profile-add-filter",
                "bwdif",
                "--profile-add-filter",
                "colorlevels32",
                "--profile-add-filter",
                "map_r_to_lr",
                "--force-black-level",
                "255,255,255",
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

        cmd = ffmpeg_wrapper.command.data

        self.assertFalse(any(",," in cmds for cmds in cmd))


if __name__ == "__main__":
    unittest.main()
