from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from tbc_video_export.common.enums import ExportMode, TBCType, ToolType
from tbc_video_export.common.file_helper import FileHelper
from tbc_video_export.files import ConfigFile
from tbc_video_export.opts import opt_validators, opts_parser
from tbc_video_export.process.wrapper import WrapperConfig
from tbc_video_export.process.wrapper.pipe import Pipe, PipeFactory
from tbc_video_export.process.wrapper.wrapper_chroma_decode import (
    WrapperChromaDecode,
)
from tbc_video_export.process.wrapper.wrapper_dropout_correct import (
    WrapperDropoutCorrect,
)
from tbc_video_export.process.wrapper.wrapper_ffmpeg import WrapperFFmpeg
from tbc_video_export.process.wrapper.wrapper_vbi_process import WrapperVBIProcess
from tbc_video_export.program_state import ProgramState

if TYPE_CHECKING:
    from pytest_mock import MockFixture


@dataclass
class WrapperTestCase:
    id: str
    input_opts: list[str]
    input_tbc: str
    out_file: str | None = "out_file"
    tbc_type: TBCType = TBCType.NONE
    export_mode: ExportMode | None = None
    expected_opts: list[set[str]] = field(default_factory=list[set[str]])
    expected_str: list[str] = field(default_factory=list[str])
    expected_exc: type[BaseException] | None = None
    unexpected_opts: list[set[str]] = field(default_factory=list[set[str]])
    unexpected_str: list[str] = field(default_factory=list[str])


@dataclass
class WrapperGroupTestCase:
    id: str
    input_opts: list[str]
    input_tbc: Path
    tbc_type: TBCType
    wrapper_groups: list[list[ToolType]]


@dataclass
class FileHelperTestCase:
    id: str
    input_name: str
    input_path: Path
    luma_tbc: Path
    output_name: str
    output_path: Path
    output_container: str
    output_video_file: Path
    output_video_file_luma: Path
    is_ld: bool
    ffmetadata_file: Path
    cc_file: Path
    tbc_types: TBCType


@dataclass
class VideoBase:
    width: int
    height: int
    pixel_aspect_ratio: str
    display_aspect_ratio: str
    framerate_num: str
    framerate_den: str
    scan_type: str
    scan_order: str | None


@dataclass
class VideoBasePAL(VideoBase):
    width: int = field(default=928)
    height: int = field(default=576)
    pixel_aspect_ratio: str = field(default="0.833")
    display_aspect_ratio: str = field(default="1.342")
    framerate_num: str = field(default="25")
    framerate_den: str = field(default="1")
    scan_type: str = field(default="Interlaced")
    scan_order: str | None = field(default="TFF")


@dataclass
class VideoBasePALM(VideoBase):
    width: int = field(default=760)
    height: int = field(default=488)
    pixel_aspect_ratio: str = field(default="0.852")
    display_aspect_ratio: str = field(default="1.327")
    framerate_num: str = field(default="30000")
    framerate_den: str = field(default="1001")
    scan_type: str = field(default="Interlaced")
    scan_order: str | None = field(default="TFF")


@dataclass
class VideoBaseNTSC(VideoBase):
    width: int = field(default=760)
    height: int = field(default=488)
    pixel_aspect_ratio: str = field(default="0.852")
    display_aspect_ratio: str = field(default="1.327")
    framerate_num: str = field(default="30000")
    framerate_den: str = field(default="1001")
    scan_type: str = field(default="Interlaced")
    scan_order: str | None = field(default="TFF")


@dataclass
class VideoColor:
    color_space: str
    bit_depth: int | None
    chroma_subsampling: str | None
    color_range: str | None
    color_primaries: str
    transfer_characteristics: str
    matrix_coefficients: str
    matrix_coefficients_original: str | None


@dataclass
class VideoColorPAL(VideoColor):
    color_space: str = field(default="YUV")
    bit_depth: int | None = field(default=None)
    chroma_subsampling: str | None = field(default=None)
    color_range: str | None = field(default="Limited")
    color_primaries: str = field(default="BT.601 PAL")
    transfer_characteristics: str = field(default="BT.709")
    matrix_coefficients: str = field(default="BT.470 System B/G")
    matrix_coefficients_original: str | None = field(default=None)


@dataclass
class VideoColorPALM(VideoColor):
    color_space: str = field(default="YUV")
    bit_depth: int | None = field(default=None)
    chroma_subsampling: str | None = field(default=None)
    color_range: str | None = field(default="Limited")
    color_primaries: str = field(default="BT.601 PAL")
    transfer_characteristics: str = field(default="BT.709")
    matrix_coefficients: str = field(default="BT.470 System B/G")
    matrix_coefficients_original: str | None = field(default=None)


@dataclass
class VideoColorNTSC(VideoColor):
    color_space: str = field(default="YUV")
    bit_depth: int | None = field(default=None)
    chroma_subsampling: str | None = field(default=None)
    color_range: str | None = field(default="Limited")
    color_primaries: str = field(default="BT.601 NTSC")
    transfer_characteristics: str = field(default="BT.709")
    matrix_coefficients: str = field(default="BT.601")
    matrix_coefficients_original: str | None = field(default=None)


@dataclass
class AudioBase:
    format: str
    bit_depth: int
    sampling_rate: int
    title: str | None = field(default=None)
    language: str | None = field(default=None)
    channel_s: int = field(default=2)
    channel_layout: str | None = field(default="L R")


@dataclass
class OutputTestCase:
    id: str
    input_opts: list[str]
    input_tbc: str
    output_file: str
    output_video_codec: dict[str, str | list[str]]
    output_video_base: VideoBase
    output_video_color: VideoColor
    output_audio_base: list[AudioBase] = field(default_factory=list[AudioBase])
    output_metadata: dict[str, Any] = field(default_factory=dict[str, Any])
    expected_exc: type[BaseException] | None = None


def get_path(path: str):
    return Path.joinpath(Path(__file__).parent, "files", path).absolute()


def get_path_str(path: str):
    return f"{get_path(path)}"


@pytest.fixture
def force_ansi_support_on(mocker: MockFixture):
    mocker.patch(
        "tbc_video_export.common.utils.ansi.has_ansi_support",
        mocker.Mock(return_value=True),
    )


@pytest.fixture
def force_ansi_support_off(mocker: MockFixture) -> None:
    mocker.patch(
        "tbc_video_export.common.utils.ansi.has_ansi_support",
        mocker.Mock(return_value=False),
    )


@pytest.fixture
def program_state():
    def _inner(test_opts: list[str], path: Path, out_file: str | None = "out_file"):
        config = ConfigFile()

        in_opts = [str(path), *test_opts] + ([out_file] if out_file is not None else [])
        parser, opts = opts_parser.parse_opts(config, in_opts)
        files = FileHelper(opts, config)
        state = ProgramState(opts, config, files)
        opt_validators.validate_opts(state, parser, opts)

        return state

    return _inner


@pytest.fixture
def ldtools_process_vbi_wrapper():
    def _init(state: ProgramState, tbc_type: TBCType):
        return WrapperVBIProcess(
            state,
            WrapperConfig[None, None](state.current_export_mode, tbc_type, None, None),
        )

    return _init


@pytest.fixture
def ldtools_dropout_correct_wrapper():
    def _init(state: ProgramState, tbc_type: TBCType):
        pipe = PipeFactory.create_dummy_pipe()

        return WrapperDropoutCorrect(
            state,
            WrapperConfig[None, Pipe](state.current_export_mode, tbc_type, None, pipe),
        )

    return _init


@pytest.fixture
def ldtools_chroma_decoder_wrapper():
    def _init(state: ProgramState, tbc_type: TBCType):
        pipe = PipeFactory.create_dummy_pipe()

        return WrapperChromaDecode(
            state,
            WrapperConfig[Pipe, Pipe](state.current_export_mode, tbc_type, pipe, pipe),
        )

    return _init


@pytest.fixture
def ffmpeg_wrapper_chroma():
    def _inner(
        state: ProgramState, tbc_type: TBCType, export_mode: ExportMode | None = None
    ):
        pipe = PipeFactory.create_dummy_pipe()
        input_pipes = (pipe,)

        if export_mode is None:
            export_mode = state.current_export_mode

        if export_mode is ExportMode.CHROMA_MERGE:
            input_pipes = (pipe, pipe)

        return WrapperFFmpeg(
            state,
            WrapperConfig[tuple[Pipe, ...], None](
                export_mode,
                tbc_type,
                input_pipes,
                output_pipes=None,
            ),
        )

    return _inner
