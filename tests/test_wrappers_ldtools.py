from __future__ import annotations

import unittest
from functools import partial

from path import Path
from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import TBCType
from tbc_video_export.common.file_helper import FileHelper
from tbc_video_export.config import Config as ProgramConfig
from tbc_video_export.opts import opts_parser
from tbc_video_export.process.wrapper import WrapperConfig
from tbc_video_export.process.wrapper.pipe import Pipe, PipeFactory
from tbc_video_export.process.wrapper.wrapper_ld_chroma_decoder import (
    WrapperLDChromaDecoder,
)
from tbc_video_export.process.wrapper.wrapper_ld_dropout_correct import (
    WrapperLDDropoutCorrect,
)
from tbc_video_export.process.wrapper.wrapper_ld_process_vbi import WrapperLDProcessVBI
from tbc_video_export.program_state import ProgramState


class TestWrappersLDTools(unittest.TestCase):
    """Tests for ld-tools wrappers."""

    def setUp(self) -> None:  # noqa: D102
        self.path = Path.joinpath(Path(__file__).parent, "files", "pal_svideo")

        self.config = ProgramConfig()
        self.parse_opts = partial(opts_parser.parse_opts, self.config)

        self.pipe = PipeFactory.create_dummy_pipe()

    def test_process_vbi_default_opts(self) -> None:  # noqa: D102
        opts = self.parse_opts(
            [self.path, "pal_svideo", "--threads", "4", "--process-vbi"]
        )
        self.files = FileHelper(opts, self.config)
        state = ProgramState(opts, self.config, self.files)

        vbi_process = WrapperLDProcessVBI(
            state,
            WrapperConfig[None, None](
                state.current_export_mode, TBCType.NONE, None, None
            ),
        )

        self.assertEqual(
            str(vbi_process.command),
            f"ld-process-vbi "
            f"-t 4 "
            f"--input-json {self.path}.tbc.json "
            f"--output-json {self.path}.vbi.json "
            f"{self.path}.tbc",
        )

    def test_process_vbi_custom_json(self) -> None:  # noqa: D102
        custom_json = Path.joinpath(
            Path(__file__).parent, "files", "ntsc_svideo.tbc.json"
        )

        opts = self.parse_opts(
            [
                self.path,
                "pal_svideo",
                "--threads",
                "4",
                "--process-vbi",
                "--input-tbc-json",
                custom_json,
            ],
        )
        self.files = FileHelper(opts, self.config)
        state = ProgramState(opts, self.config, self.files)

        vbi_process = WrapperLDProcessVBI(
            state,
            WrapperConfig[None, None](
                state.current_export_mode, TBCType.NONE, None, None
            ),
        )

        self.assertEqual(
            str(vbi_process.command),
            f"ld-process-vbi "
            f"-t 4 "
            f"--input-json {custom_json} "
            f"--output-json {self.path}.vbi.json "
            f"{self.path}.tbc",
        )

    def test_dropout_correct_default_opts(self) -> None:  # noqa: D102
        opts = opts_parser.parse_opts(
            self.config, [self.path, "pal_svideo", "--threads", "4"]
        )
        self.files = FileHelper(opts, self.config)
        state = ProgramState(opts, self.config, self.files)

        dropout_correct = WrapperLDDropoutCorrect(
            state,
            WrapperConfig[None, Pipe](
                state.current_export_mode,
                TBCType.LUMA,
                input_pipes=None,
                output_pipes=self.pipe,
            ),
        )

        self.assertEqual(
            str(dropout_correct.command),
            f"ld-dropout-correct "
            f"-i {self.path}.tbc "
            f"--input-json {self.path}.tbc.json "
            f"--output-json /dev/null PIPE_OUT",
        )

    def test_decoder_invalid_videosystem(self) -> None:  # noqa: D102
        opts = self.parse_opts([self.path, "pal_svideo", "--chroma-decoder", "ntsc2d"])
        self.files = FileHelper(opts, self.config)
        state = ProgramState(opts, self.config, self.files)

        with self.assertRaises(exceptions.InvalidChromaDecoderError):
            WrapperLDChromaDecoder(
                state,
                WrapperConfig[Pipe, Pipe](
                    state.current_export_mode,
                    TBCType.CHROMA,
                    input_pipes=self.pipe,
                    output_pipes=self.pipe,
                ),
            )

    def test_decoder_letterbox_pal(self) -> None:  # noqa: D102
        path = Path.joinpath(Path(__file__).parent, "files", "pal_svideo")
        opts = self.parse_opts([path, "pal_svideo", "--letterbox"])
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

        self.assertTrue(
            {"--ffll", "2", "--lfll", "308", "--ffrl", "118", "--lfrl", "548"}.issubset(
                decoder.command.data
            )
        )

    def test_decoder_letterbox_ntsc(self) -> None:  # noqa: D102
        path = Path.joinpath(Path(__file__).parent, "files", "ntsc_svideo")
        opts = self.parse_opts([path, "ntsc_svideo", "--letterbox"])
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

        self.assertTrue(
            {"--ffll", "2", "--lfll", "308", "--ffrl", "118", "--lfrl", "453"}.issubset(
                decoder.command.data
            )
        )

    def test_decoder_letterbox_palm(self) -> None:  # noqa: D102
        path = Path.joinpath(Path(__file__).parent, "files", "palm_svideo")
        opts = self.parse_opts([path, "palm_svideo", "--letterbox"])
        self.files = FileHelper(opts, self.config)
        state = ProgramState(opts, self.config, self.files)

        with self.assertRaises(exceptions.SampleRequiredError):
            WrapperLDChromaDecoder(
                state,
                WrapperConfig[Pipe, Pipe](
                    state.current_export_mode,
                    TBCType.CHROMA,
                    input_pipes=self.pipe,
                    output_pipes=self.pipe,
                ),
            )

    def test_decoder_vbi_pal(self) -> None:  # noqa: D102
        path = Path.joinpath(Path(__file__).parent, "files", "pal_svideo")
        opts = self.parse_opts([path, "pal_svideo", "--vbi"])
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

        self.assertTrue({"--ffll", "2", "--lfll", "308"}.issubset(decoder.command.data))
        self.assertTrue({"--ffrl", "2", "--lfrl", "620"}.issubset(decoder.command.data))

    def test_decoder_vbi_ntsc(self) -> None:  # noqa: D102
        path = Path.joinpath(Path(__file__).parent, "files", "ntsc_svideo")
        opts = self.parse_opts([path, "ntsc_svideo", "--vbi"])
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

        self.assertTrue(
            {"--ffll", "1", "--lfll", "259", "--ffrl", "2", "--lfrl", "525"}.issubset(
                decoder.command.data
            )
        )

    def test_decoder_vbi_palm(self) -> None:  # noqa: D102
        path = Path.joinpath(Path(__file__).parent, "files", "palm_svideo")
        opts = self.parse_opts([path, "palm_svideo", "--vbi"])
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
        self.assertTrue(
            {"--ffll", "1", "--lfll", "259", "--ffrl", "2", "--lfrl", "525"}.issubset(
                decoder.command.data
            )
        )


if __name__ == "__main__":
    unittest.main()
