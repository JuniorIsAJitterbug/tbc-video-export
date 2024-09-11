from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import TBCType

from tests.conftest import WrapperTestCase, get_path

if TYPE_CHECKING:
    from collections.abc import Callable

    from tbc_video_export.process.wrapper.wrapper_ld_chroma_decoder import (
        WrapperLDChromaDecoder,
    )
    from tbc_video_export.process.wrapper.wrapper_ld_dropout_correct import (
        WrapperLDDropoutCorrect,
    )
    from tbc_video_export.process.wrapper.wrapper_ld_process_vbi import (
        WrapperLDProcessVBI,
    )
    from tbc_video_export.program_state import ProgramState


class TestWrappersProcessVBI:
    """Tests for ld-process-vbi wrapper."""

    test_cases = [
        WrapperTestCase(
            id="default ld-process-vbi opts",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            input_opts=["--process-vbi"],
            expected_opts=[
                {"--input-json", f"{get_path('pal_svideo')}.tbc.json"},
                {"--output-json", f"{get_path('pal_svideo')}.vbi.json"},
                {f"{get_path('pal_svideo')}.tbc"},
            ],
        ),
        WrapperTestCase(
            id="set input json",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            input_opts=[
                "--process-vbi",
                "--input-tbc-json",
                str(get_path("ntsc_svideo.tbc.json")),
            ],
            expected_opts=[
                {"--input-json", f"{get_path('ntsc_svideo')}.tbc.json"},
                {"--output-json", f"{get_path('pal_svideo')}.vbi.json"},
                {f"{get_path('pal_svideo')}.tbc"},
            ],
        ),
        WrapperTestCase(
            id="set threads",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            input_opts=["--process-vbi", "--threads", "4"],
            expected_opts=[
                {"-t", "4"},
            ],
        ),
    ]

    @pytest.mark.parametrize(
        "test_case",
        (pytest.param(test_case, id=test_case.id) for test_case in test_cases),
    )
    def test_process_vbi_opts(  # noqa: D102
        self,
        program_state: Callable[[list[str], str], ProgramState],
        ldtools_process_vbi_wrapper: Callable[
            [ProgramState, TBCType], WrapperLDProcessVBI
        ],
        test_case: WrapperTestCase,
    ) -> None:
        with test_case.expected_exc:
            state = program_state(test_case.input_opts, test_case.input_tbc)
            process_vbi_wrapper = ldtools_process_vbi_wrapper(state, test_case.tbc_type)
            cmds = process_vbi_wrapper.command.data

            for e in test_case.expected_opts:
                assert e.issubset(cmds)

            for e in test_case.expected_str:
                assert any(e in cmd for cmd in cmds)

            for e in test_case.unexpected_opts:
                assert not e.issubset(cmds)

            for e in test_case.unexpected_str:
                assert not any(e in cmd for cmd in cmds)

    def test_process_vbi_json(  # noqa: D102
        self,
        program_state: Callable[[list[str], str], ProgramState],
        ldtools_process_vbi_wrapper: Callable[
            [ProgramState, TBCType], WrapperLDProcessVBI
        ],
    ) -> None:
        state = program_state(["--process-vbi"], f"{get_path('pal_svideo')}.tbc")
        process_vbi_wrapper = ldtools_process_vbi_wrapper(state, TBCType.LUMA)

        assert state.file_helper.tbc_json.file_name == Path(
            f"{get_path('pal_svideo')}.tbc.json"
        )

        process_vbi_wrapper.post_fn()
        assert state.file_helper.tbc_json.file_name == Path(
            f"{get_path('pal_svideo')}.vbi.json"
        )

        state = program_state(
            [
                "--process-vbi",
                "--dry-run",
            ],
            f"{get_path('pal_svideo')}.tbc",
        )
        process_vbi_wrapper = ldtools_process_vbi_wrapper(state, TBCType.LUMA)

        assert state.file_helper.tbc_json.file_name == Path(
            f"{get_path('pal_svideo')}.tbc.json"
        )

        process_vbi_wrapper.post_fn()
        assert state.file_helper.tbc_json.file_name == Path(
            f"{get_path('pal_svideo')}.vbi.json"
        )


class TestWrappersDropoutCorrect:
    """Tests for ld-dropout-correct wrapper."""

    test_cases = [
        WrapperTestCase(
            id="default ld-dropout-correct luma opts",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            input_opts=[],
            expected_opts=[
                {"-i", f"{get_path('pal_svideo')}.tbc"},
                {"--input-json", f"{get_path('pal_svideo')}.tbc.json"},
                {"--output-json", os.devnull},
                {"PIPE_OUT"},
            ],
            tbc_type=TBCType.LUMA,
        ),
        WrapperTestCase(
            id="default ld-dropout-correct chroma opts",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            input_opts=[],
            expected_opts=[
                {"-i", f"{get_path('pal_svideo')}_chroma.tbc"},
                {"--input-json", f"{get_path('pal_svideo')}.tbc.json"},
                {"--output-json", os.devnull},
                {"PIPE_OUT"},
            ],
            tbc_type=TBCType.CHROMA,
        ),
    ]

    @pytest.mark.parametrize(
        "test_case",
        (pytest.param(test_case, id=test_case.id) for test_case in test_cases),
    )
    def test_dropout_correct_opts(  # noqa: D102
        self,
        program_state: Callable[[list[str], str], ProgramState],
        ldtools_dropout_correct_wrapper: Callable[
            [ProgramState, TBCType], WrapperLDDropoutCorrect
        ],
        test_case: WrapperTestCase,
    ) -> None:
        with test_case.expected_exc:
            state = program_state(test_case.input_opts, test_case.input_tbc)
            dropout_correct_wrapper = ldtools_dropout_correct_wrapper(
                state, test_case.tbc_type
            )
            cmds = dropout_correct_wrapper.command.data

            for e in test_case.expected_opts:
                assert e.issubset(cmds)

            for e in test_case.expected_str:
                assert any(e in cmd for cmd in cmds)

            for e in test_case.unexpected_opts:
                assert not e.issubset(cmds)

            for e in test_case.unexpected_str:
                assert not any(e in cmd for cmd in cmds)


class TestWrappersChromaDecoder:
    """Tests for ld-chroma-decoder wrapper."""

    test_cases = [
        # PAL
        WrapperTestCase(
            id="pal svideo luma opts",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            input_opts=[],
            expected_opts=[
                {"--chroma-gain", "0"},
                {"-f", "mono"},
                {"--input-json", f"{get_path('pal_svideo')}.tbc.json"},
                {"PIPE_IN", "PIPE_OUT"},
            ],
            tbc_type=TBCType.LUMA,
        ),
        WrapperTestCase(
            id="pal svideo chroma opts",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            input_opts=[],
            expected_opts=[
                {"--luma-nr", "0"},
                {"-f", "pal2d"},
                {"--input-json", f"{get_path('pal_svideo')}.tbc.json"},
                {"PIPE_IN", "PIPE_OUT"},
            ],
            tbc_type=TBCType.CHROMA,
        ),
        WrapperTestCase(
            id="pal composite opts",
            input_tbc=f"{get_path('pal_composite')}.tbc",
            input_opts=[],
            expected_opts=[
                {"-f", "transform3d"},
                {"--input-json", f"{get_path('pal_composite')}.tbc.json"},
                {"PIPE_IN", "PIPE_OUT"},
            ],
            tbc_type=TBCType.COMBINED,
        ),
        WrapperTestCase(
            id="pal invalid decoder (exception)",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            input_opts=["--chroma-decoder", "ntsc2d"],
            expected_opts=[],
            expected_exc=pytest.raises(exceptions.InvalidChromaDecoderError),
        ),
        WrapperTestCase(
            id="pal letterbox",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            input_opts=["--letterbox"],
            expected_opts=[
                {"--ffll", "2"},
                {"--lfll", "308"},
                {"--ffrl", "118"},
                {"--lfrl", "548"},
            ],
        ),
        WrapperTestCase(
            id="pal vbi",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            input_opts=["--vbi"],
            expected_opts=[
                {"--ffll", "2"},
                {"--lfll", "308"},
                {"--ffrl", "2"},
                {"--lfrl", "620"},
            ],
        ),
        # PAL-M
        WrapperTestCase(
            id="pal-m svideo luma opts",
            input_tbc=f"{get_path('palm_svideo')}.tbc",
            input_opts=[],
            expected_opts=[
                {"--chroma-gain", "0"},
                {"-f", "mono"},
                {"--input-json", f"{get_path('palm_svideo')}.tbc.json"},
                {"PIPE_IN", "PIPE_OUT"},
            ],
            tbc_type=TBCType.LUMA,
        ),
        WrapperTestCase(
            id="pal-m svideo chroma opts",
            input_tbc=f"{get_path('palm_svideo')}.tbc",
            input_opts=[],
            expected_opts=[
                {"--luma-nr", "0"},
                {"-f", "pal2d"},
                {"--input-json", f"{get_path('palm_svideo')}.tbc.json"},
                {"PIPE_IN", "PIPE_OUT"},
            ],
            tbc_type=TBCType.CHROMA,
        ),
        WrapperTestCase(
            id="pal-m invalid decoder (exception)",
            input_tbc=f"{get_path('palm_svideo')}.tbc",
            input_opts=["--chroma-decoder", "ntsc2d"],
            expected_opts=[],
            expected_exc=pytest.raises(exceptions.InvalidChromaDecoderError),
        ),
        WrapperTestCase(
            id="pal-m letterbox (exception)",
            input_tbc=f"{get_path('palm_svideo')}.tbc",
            input_opts=["--letterbox"],
            expected_opts=[],
            expected_exc=pytest.raises(exceptions.SampleRequiredError),
        ),
        WrapperTestCase(
            id="pal-m vbi",
            input_tbc=f"{get_path('palm_svideo')}.tbc",
            input_opts=["--vbi"],
            expected_opts=[
                {"--ffll", "1"},
                {"--lfll", "259"},
                {"--ffrl", "2"},
                {"--lfrl", "525"},
            ],
        ),
        # NTSC
        WrapperTestCase(
            id="ntsc svideo luma opts",
            input_tbc=f"{get_path('ntsc_svideo')}.tbc",
            input_opts=[],
            expected_opts=[
                {"--chroma-gain", "0"},
                {"-f", "mono"},
                {"--input-json", f"{get_path('ntsc_svideo')}.tbc.json"},
                {"PIPE_IN", "PIPE_OUT"},
            ],
            tbc_type=TBCType.LUMA,
        ),
        WrapperTestCase(
            id="ntsc svideo chroma opts",
            input_tbc=f"{get_path('ntsc_svideo')}.tbc",
            input_opts=[],
            expected_opts=[
                {"--luma-nr", "0"},
                {"-f", "ntsc2d"},
                {"--input-json", f"{get_path('ntsc_svideo')}.tbc.json"},
                {"PIPE_IN", "PIPE_OUT"},
            ],
            tbc_type=TBCType.CHROMA,
        ),
        WrapperTestCase(
            id="ntsc composite opts",
            input_tbc=f"{get_path('ntsc_composite')}.tbc",
            input_opts=[],
            expected_opts=[
                {"-f", "ntsc3d"},
                {"--input-json", f"{get_path('ntsc_composite')}.tbc.json"},
                {"PIPE_IN", "PIPE_OUT"},
            ],
            tbc_type=TBCType.COMBINED,
        ),
        WrapperTestCase(
            id="ntsc composite (ld) opts",
            input_tbc=f"{get_path('ntsc_composite_ld')}.tbc",
            input_opts=[],
            expected_opts=[
                {"-f", "ntsc2d"},
                {"--input-json", f"{get_path('ntsc_composite_ld')}.tbc.json"},
                {"PIPE_IN", "PIPE_OUT"},
            ],
            tbc_type=TBCType.COMBINED,
        ),
        WrapperTestCase(
            id="ntsc invalid decoder (exception)",
            input_tbc=f"{get_path('ntsc_svideo')}.tbc",
            input_opts=["--chroma-decoder", "transform2d"],
            expected_opts=[],
            expected_exc=pytest.raises(exceptions.InvalidChromaDecoderError),
        ),
        WrapperTestCase(
            id="ntsc letterbox",
            input_tbc=f"{get_path('ntsc_svideo')}.tbc",
            input_opts=["--letterbox"],
            expected_opts=[
                {"--ffll", "61"},
                {"--lfll", "224"},
                {"--ffrl", "122"},
                {"--lfrl", "448"},
            ],
        ),
        WrapperTestCase(
            id="ntsc vbi",
            input_tbc=f"{get_path('ntsc_svideo')}.tbc",
            input_opts=["--vbi"],
            expected_opts=[
                {"--ffll", "1"},
                {"--lfll", "259"},
                {"--ffrl", "2"},
                {"--lfrl", "525"},
            ],
        ),
        # general
        WrapperTestCase(
            id="luma nr with transform2d (luma)",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            tbc_type=TBCType.LUMA,
            input_opts=[
                "--luma-nr",
                "5",
                "--chroma-decoder-luma",
                "transform2d",
            ],
            expected_opts=[{"--luma-nr", "5.0"}],
        ),
        WrapperTestCase(
            id="luma nr with mono (chroma)",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            tbc_type=TBCType.CHROMA,
            input_opts=[
                "--luma-nr",
                "5",
                "--chroma-decoder-luma",
                "transform2d",
            ],
            expected_opts=[{"--luma-nr", "0"}],
        ),
        WrapperTestCase(
            id="luma nr with mono (luma)",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            tbc_type=TBCType.LUMA,
            input_opts=[
                "--luma-nr",
                "5",
            ],
            expected_exc=pytest.raises(exceptions.InvalidOptsError),
            expected_opts=[{"--luma-nr", "5.0"}],
        ),
        WrapperTestCase(
            id="luma nr with mono (chroma)",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            tbc_type=TBCType.CHROMA,
            input_opts=[
                "--luma-nr",
                "5",
            ],
            expected_exc=pytest.raises(exceptions.InvalidOptsError),
            expected_opts=[{"--luma-nr", "0"}],
        ),
        WrapperTestCase(
            id="luma nr (composite)",
            input_tbc=f"{get_path('pal_composite')}.tbc",
            tbc_type=TBCType.COMBINED,
            input_opts=[
                "--luma-nr",
                "5",
            ],
            expected_opts=[{"--luma-nr", "5.0"}],
        ),
        WrapperTestCase(
            id="chroma nr (luma)",
            input_tbc=f"{get_path('ntsc_svideo')}.tbc",
            tbc_type=TBCType.LUMA,
            input_opts=[
                "--chroma-nr",
                "5",
            ],
            unexpected_opts=[{"--chroma-nr"}],
        ),
        WrapperTestCase(
            id="chroma nr (chroma)",
            input_tbc=f"{get_path('ntsc_svideo')}.tbc",
            tbc_type=TBCType.CHROMA,
            input_opts=[
                "--chroma-nr",
                "5",
            ],
            expected_opts=[{"--chroma-nr", "5.0"}],
        ),
        WrapperTestCase(
            id="chroma nr (composite)",
            input_tbc=f"{get_path('ntsc_composite')}.tbc",
            tbc_type=TBCType.COMBINED,
            input_opts=[
                "--chroma-nr",
                "5",
            ],
            expected_opts=[{"--chroma-nr", "5.0"}],
        ),
        WrapperTestCase(
            id="chroma nr non-pal (exception)",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            tbc_type=TBCType.COMBINED,
            input_opts=[
                "--chroma-nr",
                "5",
            ],
            expected_exc=pytest.raises(SystemExit),
        ),
        WrapperTestCase(
            id="chroma gain (luma)",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            tbc_type=TBCType.LUMA,
            input_opts=[
                "--chroma-gain",
                "5",
            ],
            expected_opts=[{"--chroma-gain", "0"}],
        ),
        WrapperTestCase(
            id="chroma gain (chroma)",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            tbc_type=TBCType.CHROMA,
            input_opts=[
                "--chroma-gain",
                "5",
            ],
            expected_opts=[{"--chroma-gain", "5.0"}],
        ),
        WrapperTestCase(
            id="chroma gain (composite)",
            input_tbc=f"{get_path('pal_composite')}.tbc",
            tbc_type=TBCType.COMBINED,
            input_opts=[
                "--chroma-gain",
                "5",
            ],
            expected_opts=[{"--chroma-gain", "5.0"}],
        ),
        WrapperTestCase(
            id="chroma phase (luma)",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            tbc_type=TBCType.LUMA,
            input_opts=[
                "--chroma-phase",
                "5",
            ],
            unexpected_opts=[{"--chroma-phase"}],
        ),
        WrapperTestCase(
            id="chroma phase (chroma)",
            input_tbc=f"{get_path('pal_svideo')}.tbc",
            tbc_type=TBCType.CHROMA,
            input_opts=[
                "--chroma-phase",
                "5",
            ],
            expected_opts=[{"--chroma-phase", "5.0"}],
        ),
        WrapperTestCase(
            id="chroma phase (composite)",
            input_tbc=f"{get_path('pal_composite')}.tbc",
            tbc_type=TBCType.COMBINED,
            input_opts=[
                "--chroma-phase",
                "5",
            ],
            expected_opts=[{"--chroma-phase", "5.0"}],
        ),
    ]

    @pytest.mark.parametrize(
        "test_case",
        (pytest.param(test_case, id=test_case.id) for test_case in test_cases),
    )
    def test_chroma_decoder_opts(  # noqa: D102
        self,
        program_state: Callable[[list[str], str], ProgramState],
        ldtools_chroma_decoder_wrapper: Callable[
            [ProgramState, TBCType], WrapperLDChromaDecoder
        ],
        test_case: WrapperTestCase,
    ) -> None:
        with test_case.expected_exc:
            state = program_state(test_case.input_opts, test_case.input_tbc)
            chroma_decoder_wrapper = ldtools_chroma_decoder_wrapper(
                state, test_case.tbc_type
            )
            cmds = chroma_decoder_wrapper.command.data

            for e in test_case.expected_opts:
                assert e.issubset(cmds)

            for e in test_case.expected_str:
                assert any(e in cmd for cmd in cmds)

            for e in test_case.unexpected_opts:
                assert not e.issubset(cmds)

            for e in test_case.unexpected_str:
                assert not any(e in cmd for cmd in cmds)
