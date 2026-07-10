from __future__ import annotations

import os
from contextlib import nullcontext
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import pytest

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import ExportMode, TBCType
from tbc_video_export.common.video_system import video_system_pal
from tests.conftest import WrapperTestCase, get_path_str

if TYPE_CHECKING:
    from collections.abc import Callable

    from tbc_video_export.process.wrapper.pipe.pipe import Pipe
    from tbc_video_export.process.wrapper.wrapper_ffmpeg import WrapperFFmpeg
    from tbc_video_export.program_state import ProgramState


class TestWrappersFFmpeg:
    """Tests for FFmpeg wrapper."""

    pal_setparams = (
        f"setparams="
        f"range={video_system_pal.ffmpeg_config.color_range}:"
        f"colorspace={video_system_pal.ffmpeg_config.color_space}:"
        f"color_primaries={video_system_pal.ffmpeg_config.color_primaries}:"
        f"color_trc={video_system_pal.ffmpeg_config.color_trc}"
    )

    audio_file = "tests/files/audio.flac"

    general_cases: ClassVar[list[WrapperTestCase]] = [
        WrapperTestCase(
            id="set threads (global)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--threads", "100"],
            expected_opts=[{"-threads", "100"}],
        ),
        WrapperTestCase(
            id="set threads (specific)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--ffmpeg-threads", "100"],
            expected_opts=[{"-threads", "100"}],
        ),
        WrapperTestCase(
            id="set threads (override)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--threads", "200", "--ffmpeg-threads", "100"],
            expected_opts=[{"-threads", "100"}],
        ),
        WrapperTestCase(
            id="set threads (global disable)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--threads", "0"],
            unexpected_opts=[{"-threads"}],
        ),
        WrapperTestCase(
            id="set threads (local disable)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--ffmpeg-threads", "0"],
            unexpected_opts=[{"-threads"}],
        ),
        WrapperTestCase(
            id="set threads (global set, local disable)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--threads", "100", "--ffmpeg-threads", "0"],
            unexpected_opts=[{"-threads"}],
        ),
        WrapperTestCase(
            id="set threads (global disable, local set)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--threads", "0", "--ffmpeg-threads", "100"],
            expected_opts=[{"-threads", "100"}],
        ),
        WrapperTestCase(
            id="simple audio track",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--audio-track", audio_file],
            expected_opts=[
                {"-i", f"{Path(audio_file).absolute()!s}"},
                {"-map", "2:a"},
            ],
        ),
        WrapperTestCase(
            id="add subtitles from export-metadata",
            input_tbc=get_path_str("pal_composite_ld.tbc"),
            input_opts=["--export-metadata"],
            out_file=None,
            tbc_type=TBCType.COMBINED,
            export_mode=ExportMode.CHROMA_COMBINED,
            expected_opts=[
                {"-i", get_path_str("pal_composite_ld.scc")},
                {"-map", "1:s"},
                {"-i", get_path_str("pal_composite_ld.ffmetadata")},
                {"-map_metadata", "2"},
            ],
        ),
        WrapperTestCase(
            id="add subtitles from export-metadata (dry-run)",
            input_tbc=get_path_str("pal_composite_ld.tbc"),
            input_opts=["--export-metadata", "--dry-run"],
            expected_opts=[
                {"{-i", "[SUBTITLE_FILE]}"},
                {"{-map", "[SUBTITLE_INDEX]:s}"},
                {"{-i", "[METADATA_FILE]}"},
                {"{-map_metadata", "[METADATA_INDEX]}"},
            ],
        ),
        WrapperTestCase(
            id="use ffmetadata file",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--metadata-file", "tests/files/pal_composite_ld.ffmetadata"],
            expected_opts=[
                {"-i", get_path_str("pal_composite_ld.ffmetadata")},
                {"-map_metadata", "3"},
            ],
        ),
        WrapperTestCase(
            id="add multiple metadata",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--metadata", "foo", "bar", "--metadata", "bar", "foo"],
            expected_opts=[
                {"-metadata", "foo=bar"},
                {"-metadata", "bar=foo"},
            ],
        ),
        WrapperTestCase(
            id="check default field order",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=[],
            expected_str=["setfield=tff"],
        ),
        WrapperTestCase(
            id="set top field order",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--field-order", "tff"],
            expected_str=["setfield=tff"],
        ),
        WrapperTestCase(
            id="set bottom field order",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--field-order", "bff"],
            expected_str=["setfield=bff"],
        ),
        WrapperTestCase(
            id="set invalid field order (exception)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--field-order", "invalid"],
            expected_exc=SystemExit,
        ),
        WrapperTestCase(
            id="set widescreen (pal)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--force-anamorphic"],
            expected_str=["setsar=865/779:max=1000"],
        ),
        WrapperTestCase(
            id="set widescreen (ntsc)",
            input_tbc=get_path_str("ntsc_svideo.tbc"),
            input_opts=["--force-anamorphic"],
            expected_str=["setsar=25/22:max=1000"],
        ),
        WrapperTestCase(
            id="set widescreen (palm)",
            input_tbc=get_path_str("palm_svideo.tbc"),
            input_opts=["--force-anamorphic"],
            expected_str=["setsar=25/22:max=1000"],
        ),
        WrapperTestCase(
            id="two-step luma input",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--two-step"],
            export_mode=ExportMode.CHROMA_MERGE,
            expected_opts=[{"-i", "out_file.luma.mkv"}],
        ),
        WrapperTestCase(
            id="luma-only filters (svideo)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--luma-only"],
            unexpected_str=[
                "extractplanes",
                "mergeplanes",
            ],
        ),
        WrapperTestCase(
            id="luma-only filters (composite)",
            input_tbc=get_path_str("pal_composite.tbc"),
            input_opts=["--luma-only"],
            expected_str=["extractplanes=y"],
        ),
        WrapperTestCase(
            id="4fsc (pal svideo)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--luma-4fsc"],
            expected_opts=[
                {"-f", "rawvideo"},
                {"-pix_fmt", "gray16le"},
                {"-framerate", "pal"},
                {"-video_size", "1135x626"},
            ],
            expected_str=["il=l=i:c=i"],
        ),
        WrapperTestCase(
            id="4fsc (ntsc)",
            input_tbc=get_path_str("ntsc_svideo.tbc"),
            input_opts=["--luma-4fsc"],
            expected_opts=[
                {"-f", "rawvideo"},
                {"-pix_fmt", "gray16le"},
                {"-framerate", "ntsc"},
                {"-video_size", "910x526"},
            ],
            expected_str=["il=l=i:c=i"],
        ),
        WrapperTestCase(
            id="4fsc (palm)",
            input_tbc=get_path_str("palm_svideo.tbc"),
            input_opts=["--luma-4fsc"],
            expected_opts=[
                {"-f", "rawvideo"},
                {"-pix_fmt", "gray16le"},
                {"-framerate", "ntsc"},
                {"-video_size", "909x526"},
            ],
            expected_str=["il=l=i:c=i"],
        ),
        WrapperTestCase(
            id="override container",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--profile", "h264", "--profile-container", "mkv"],
            expected_opts=[{"out_file.mkv"}],
        ),
        WrapperTestCase(
            id="verbosity (std)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=[],
            expected_opts=[
                {"-loglevel", "error"},
                {"-progress", "pipe:2"},
            ],
        ),
        WrapperTestCase(
            id="verbosity (show output)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--show-process-output"],
            expected_opts=[
                {"-loglevel", "verbose"},
            ],
        ),
        WrapperTestCase(
            id="checksum",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--checksum"],
            expected_opts=[
                {"-f", "tee", "[f=streamhash]out_file.mkv.sha256|out_file.mkv"},
            ],
        ),
        WrapperTestCase(
            id="checksum (output format set)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--checksum", "--d10"],
            expected_opts=[
                {
                    "-f",
                    "tee",
                    "[f=streamhash]out_file.mxf.sha256|[f=mxf_d10]out_file.mxf",
                },
            ],
        ),
    ]

    hwaccel_cases: ClassVar[list[WrapperTestCase]] = [
        WrapperTestCase(
            id="vaapi hwaccel",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--h264", "--vaapi", "--hwaccel-device", "TEST"],
            expected_opts=[
                {"-hwaccel", "vaapi"},
                {"-hwaccel_output_format", "vaapi"},
                {"-vaapi_device", "TEST"},
                {"-c:v", "h264_vaapi"},
            ],
            expected_str=[f",format=yuv420p,{pal_setparams},hwupload[v_output]"],
        ),
        WrapperTestCase(
            id="nvenc hwaccel",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--h264", "--nvenc", "--hwaccel-device", "TEST"],
            expected_opts=[
                {"-gpu", "TEST"},
                {"-c:v", "h264_nvenc"},
            ],
            expected_str=[f",format=yuv420p,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="quicksync hwaccel",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--h264", "--quicksync", "--hwaccel-device", "TEST"],
            expected_opts=[
                {"-hwaccel", "qsv"},
                {"-qsv_device", "TEST"},
                {"-c:v", "h264_qsv"},
            ],
            expected_str=[f",format=yuv420p,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="amf hwaccel",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--h264", "--amf"],
            expected_opts=[
                {"-c:v", "h264_amf"},
            ],
            expected_str=[f",format=yuv420p,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="amf hwaccel invalid device (exception)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--h264", "--amf", "--hwaccel-device", "TEST"],
            expected_opts=[
                {"-c:v", "h264_amf"},
            ],
            expected_str=[f",format=yuv420p,{pal_setparams}[v_output]"],
            expected_exc=exceptions.InvalidProfileError,
        ),
        WrapperTestCase(
            id="videotoolbox hwaccel",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--h264", "--videotoolbox"],
            expected_opts=[
                {"-c:v", "h264_videotoolbox"},
            ],
            expected_str=[f",format=yuv420p,{pal_setparams}[v_output]"],
        ),
    ]

    bitdepth_cases: ClassVar[list[WrapperTestCase]] = [
        WrapperTestCase(
            id="8bit",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--8bit"],
            expected_str=[f"format=yuv422p,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="10bit",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--10bit"],
            expected_str=[f"format=yuv422p10le,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="16bit",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--16bit"],
            expected_str=[f"format=yuv422p16le,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="8bit yuv420p",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--8bit", "--yuv420"],
            expected_str=[f"format=yuv420p,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="10bit yuv420p",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--10bit", "--yuv420"],
            expected_str=[f"format=yuv420p10le,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="16bit yuv420p",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--16bit", "--yuv420"],
            expected_str=[f"format=yuv420p16le,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="8bit yuv422p",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--8bit", "--yuv422"],
            expected_str=[f"format=yuv422p,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="10bit yuv422p",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--10bit", "--yuv422"],
            expected_str=[f"format=yuv422p10le,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="16bit yuv422p",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--16bit", "--yuv422"],
            expected_str=[f"format=yuv422p16le,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="8bit yuv444p",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--8bit", "--yuv444"],
            expected_str=[f"format=yuv444p,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="10bit yuv444p",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--10bit", "--yuv444"],
            expected_str=[f"format=yuv444p10le,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="16bit yuv444p",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--16bit", "--yuv444"],
            expected_str=[f"format=yuv444p16le,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="8bit gray",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--8bit", "--gray"],
            expected_str=[f"format=gray8,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="10bit gray",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--10bit", "--gray"],
            expected_str=[f"format=gray16le,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="16bit gray",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--16bit", "--gray"],
            expected_str=[f"format=gray16le,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="luma only",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--luma-only"],
            expected_str=[f"format=gray16le,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="8bit gray (luma only)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--luma-only", "--8bit"],
            expected_str=[f"format=gray8,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="10bit gray (luma only)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--luma-only", "--10bit"],
            expected_str=[f"format=gray16le,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="16bit gray (luma only)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--luma-only", "--16bit"],
            expected_str=[f"format=gray16le,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="format without bitdepth (exception)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--yuv420"],
            expected_exc=SystemExit,
        ),
    ]

    filter_cases: ClassVar[list[WrapperTestCase]] = [
        WrapperTestCase(
            id="add filter profile",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--profile-add-filter", "bwdif"],
            expected_str=[",bwdif"],
        ),
        WrapperTestCase(
            id="add invalid filter profile (exception)",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--profile-add-filter", "invalid"],
            expected_exc=exceptions.InvalidProfileError,
        ),
        WrapperTestCase(
            id="add custom filters",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=[
                "--append-video-filter",
                "TEST_FILTER",
                "--append-other-filter",
                "TEST_FILTER",
            ],
            expected_str=[
                f",TEST_FILTER,format=yuv422p10le,{pal_setparams}[v_output]",
                "[v_output],TEST_FILTER",
            ],
        ),
        WrapperTestCase(
            id="add filters",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=[
                "--profile-add-filter",
                "bwdif",
                "--profile-add-filter",
                "colorlevels32",
                "--profile-add-filter",
                "map_r_to_lr",
                "--append-video-filter",
                "test_video_filter",
                "--append-other-filter",
                "test_other_filter",
                "--force-black-level",
                "255,255,255",
            ],
            expected_str=[
                ",bwdif"
                ",colorlevels=rimin=32/255:gimin=32/255:bimin=32/255"
                ",colorlevels=rimin=255/255:gimin=255/255:bimin=255/255"
                ",test_video_filter"
                ",format=yuv422p10le"
                f",{pal_setparams}"
                "[v_output]"
                ",[2:a]pan=stereo|FR=FR|FL=FR"
                ",test_other_filter"
            ],
            unexpected_str=[",,"],
        ),
        WrapperTestCase(
            id="two-step filters",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--two-step"],
            tbc_type=TBCType.LUMA,
            export_mode=ExportMode.LUMA,
            expected_str=[f"[0:v]setfield=tff,{pal_setparams}[v_output]"],
        ),
        WrapperTestCase(
            id="embed tbc json",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=[],
            expected_opts=[
                {
                    "-attach",
                    get_path_str("pal_svideo.tbc.json"),
                    "-metadata:s:t:0",
                    "mimetype=application/json",
                }
            ],
        ),
        WrapperTestCase(
            id="disable embed tbc json",
            input_tbc=get_path_str("pal_svideo.tbc"),
            input_opts=["--no-attach-json"],
            unexpected_opts=[
                {
                    "-attach",
                    get_path_str("pal_svideo.tbc.json"),
                    "-metadata:s:t:0",
                    "mimetype=application/json",
                }
            ],
        ),
    ]

    test_cases = general_cases + hwaccel_cases + bitdepth_cases + filter_cases

    @pytest.mark.parametrize(
        "test_case",
        tuple(pytest.param(test_case, id=test_case.id) for test_case in test_cases),
    )
    def test_ffmpeg_opts(
        self,
        force_ansi_support_on: None,
        program_state: Callable[[list[str], str, str | None], ProgramState],
        ffmpeg_wrapper_chroma: Callable[
            [ProgramState, TBCType, ExportMode | None],
            WrapperFFmpeg[tuple[Pipe, ...], None],
        ],
        test_case: WrapperTestCase,
    ) -> None:
        with (
            pytest.raises(test_case.expected_exc)
            if test_case.expected_exc is not None
            else nullcontext()
        ):
            state = program_state(
                test_case.input_opts, test_case.input_tbc, test_case.out_file
            )
            ffmpeg_wrapper = ffmpeg_wrapper_chroma(
                state, test_case.tbc_type, test_case.export_mode
            )
            cmds = ffmpeg_wrapper.command.data

            for e in test_case.expected_opts:
                assert e.issubset(cmds)

            for e in test_case.expected_str:
                assert any(e in cmd for cmd in cmds)

            for e in test_case.unexpected_opts:
                assert not e.issubset(cmds)

            for e in test_case.unexpected_str:
                assert not any(e in cmd for cmd in cmds)

    def test_ffmpeg_env(
        self,
        force_ansi_support_on: None,
        program_state: Callable[[list[str], str, str | None], ProgramState],
        ffmpeg_wrapper_chroma: Callable[
            [ProgramState, TBCType, ExportMode | None],
            WrapperFFmpeg[tuple[Pipe, ...], None],
        ],
    ) -> None:
        state = program_state([], "tests/files/pal_svideo.tbc", "out_file")
        ffmpeg_wrapper = ffmpeg_wrapper_chroma(
            state, TBCType.CHROMA, ExportMode.CHROMA_MERGE
        )

        assert ffmpeg_wrapper.env is None

        state = program_state(
            ["--log-process-output"], "tests/files/pal_svideo.tbc", "out_file"
        )
        ffmpeg_wrapper = ffmpeg_wrapper_chroma(
            state, TBCType.CHROMA, ExportMode.CHROMA_MERGE
        )

        assert ffmpeg_wrapper.env is not None
        assert "FFREPORT" in ffmpeg_wrapper.env

    def test_ffmpeg_missing_audio_track(
        self,
        force_ansi_support_on: None,
        program_state: Callable[[list[str], str, str | None], ProgramState],
        ffmpeg_wrapper_chroma: Callable[
            [ProgramState, TBCType, ExportMode | None],
            WrapperFFmpeg[tuple[Pipe, ...], None],
        ],
    ) -> None:
        with pytest.RaisesExc(SystemExit) as e:
            program_state(
                ["--audio-track", "tests/files/invalid"],
                "tests/files/pal_svideo.tbc",
                "out_file",
            )

        assert e.value.code == os.EX_NOINPUT
