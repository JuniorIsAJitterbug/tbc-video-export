from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

import pytest

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import ProcessName, TBCType, VideoSystem
from tbc_video_export.common.file_helper import FileHelper

from .conftest import FileHelperTestCase

if TYPE_CHECKING:
    from collections.abc import Callable

    from tbc_video_export.program_state import ProgramState


class TestTBCJson:
    """Tests for tbc json helper."""

    test_cases = [
        FileHelperTestCase(
            id="pal svideo",
            input_tbc=Path("tests/files/pal_svideo.tbc"),
            input_name=Path("tests/files/pal_svideo"),
            luma_tbc=Path("tests/files/pal_svideo.tbc"),
            output_name=Path("out_file"),
            output_container="mkv",
            output_video_file=Path("out_file.mkv"),
            output_video_file_luma=Path("out_file.luma.mkv"),
            is_ld=False,
            efm_file=None,
            ffmetadata_file=Path("out_file.ffmetadata"),
            cc_file=Path("out_file.scc"),
            tbc_types=TBCType.LUMA | TBCType.CHROMA,
        ),
        FileHelperTestCase(
            id="pal composite",
            input_tbc=Path("tests/files/pal_composite.tbc"),
            input_name=Path("tests/files/pal_composite"),
            luma_tbc=Path("tests/files/pal_composite.tbc"),
            output_name=Path("out_file"),
            output_container="mkv",
            output_video_file=Path("out_file.mkv"),
            output_video_file_luma=Path("out_file.luma.mkv"),
            is_ld=False,
            efm_file=None,
            ffmetadata_file=Path("out_file.ffmetadata"),
            cc_file=Path("out_file.scc"),
            tbc_types=TBCType.COMBINED,
        ),
        FileHelperTestCase(
            id="pal composite (ld)",
            input_tbc=Path("tests/files/pal_composite_ld.tbc"),
            input_name=Path("tests/files/pal_composite_ld"),
            luma_tbc=Path("tests/files/pal_composite_ld.tbc"),
            output_name=Path("out_file"),
            output_container="mkv",
            output_video_file=Path("out_file.mkv"),
            output_video_file_luma=Path("out_file.luma.mkv"),
            is_ld=True,
            efm_file=Path("tests/files/pal_composite_ld.efm"),
            ffmetadata_file=Path("out_file.ffmetadata"),
            cc_file=Path("out_file.scc"),
            tbc_types=TBCType.COMBINED,
        ),
    ]

    @pytest.mark.parametrize(
        "test_case",
        (pytest.param(test_case, id=test_case.id) for test_case in test_cases),
    )
    def test_paths(  # noqa: D102
        self,
        program_state: Callable[[list[str], Path], ProgramState],
        test_case: FileHelperTestCase,
    ) -> None:
        state = program_state([], test_case.input_tbc)
        helper = FileHelper(state.opts, state.config)

        assert test_case.input_name == helper.input_name
        assert test_case.luma_tbc == helper.tbc_luma
        assert test_case.output_name == helper.output_name
        assert test_case.output_container == helper.output_container
        assert test_case.output_video_file == helper.output_video_file
        assert test_case.output_video_file_luma == helper.output_video_file_luma
        assert test_case.is_ld == helper.is_combined_ld
        assert test_case.efm_file == helper.efm_file
        assert test_case.ffmetadata_file == helper.ffmetadata_file
        assert test_case.cc_file == helper.cc_file
        assert test_case.tbc_types == helper.tbc_types

    def test_setting_json(  # noqa: D102
        self,
        program_state: Callable[[list[str], Path], ProgramState],
    ) -> None:
        state = program_state([], Path("tests/files/pal_svideo.tbc"))
        helper = FileHelper(state.opts, state.config)

        tbc_json_helper = helper.tbc_json
        assert tbc_json_helper.video_system == VideoSystem.PAL

        helper.tbc_json = Path("tests/files/ntsc_svideo.tbc.json")
        tbc_json_helper = helper.tbc_json
        assert tbc_json_helper.video_system == VideoSystem.NTSC

    def test_missing_tbc(  # noqa: D102
        self,
        program_state: Callable[[list[str], Path], ProgramState],
    ) -> None:
        state = program_state([], Path("tests/files/pal_svideo.tbc"))
        helper = FileHelper(state.opts, state.config)

        # Clear tbc locations to cause exception
        helper.tbcs.clear()
        with pytest.raises(exceptions.TBCError) as e:
            _ = helper.tbc_luma

            assert e.value == "Unable to find luma TBC."

        with (
            NamedTemporaryFile(suffix="_chroma.tbc") as file,
            pytest.raises(exceptions.TBCError) as e,
        ):
            state = program_state([], Path(file.name.replace("_chroma.tbc", "")))
            helper = FileHelper(state.opts, state.config)

            assert e.value == "TBC not found at location."

        with pytest.raises(exceptions.TBCError) as e:
            state = program_state([], Path("tests/files/invalid"))
            helper = FileHelper(state.opts, state.config)

            assert e.value == "Location contains chroma TBC but no luma TBC."

    procs = [
        ProcessName.FFMPEG,
        ProcessName.LD_CHROMA_DECODER,
        ProcessName.LD_DROPOUT_CORRECT,
        ProcessName.LD_EXPORT_METADATA,
        ProcessName.LD_PROCESS_EFM,
        ProcessName.LD_PROCESS_VBI,
    ]

    tbc_types = [
        TBCType.CHROMA,
        TBCType.COMBINED,
        TBCType.LUMA,
    ]

    @pytest.mark.parametrize("proc", procs)
    @pytest.mark.parametrize("tbc_type", tbc_types)
    def test_log_files(  # noqa: D102
        self,
        program_state: Callable[[list[str], Path], ProgramState],
        proc: ProcessName,
        tbc_type: TBCType,
    ) -> None:
        state = program_state([], Path("tests/files/pal_svideo.tbc"))
        helper = FileHelper(state.opts, state.config)

        timestamp = "__timestamp__"

        assert helper.get_log_file(proc, tbc_type, timestamp) == Path(
            f"__timestamp___{helper.input_name.stem}_{str(proc)}_{str(tbc_type)}.log"
        )

    @pytest.mark.parametrize("proc", procs)
    def test_tools(  # noqa: D102
        self,
        program_state: Callable[[list[str], Path], ProgramState],
        proc: ProcessName,
    ) -> None:
        state = program_state(
            [
                "--process-efm",
                "--process-vbi",
                "--export-metadata",
            ],
            Path("tests/files/pal_svideo.tbc"),
        )
        helper = FileHelper(state.opts, state.config)

        assert helper.tools[proc] == Path(str(proc))

    appimage_tbc_tools_procs = [
        ProcessName.LD_CHROMA_DECODER,
        ProcessName.LD_DROPOUT_CORRECT,
        ProcessName.LD_EXPORT_METADATA,
        ProcessName.LD_PROCESS_EFM,
        ProcessName.LD_PROCESS_VBI,
    ]

    def test_tools_appimage(  # noqa: D102
        self,
        program_state: Callable[[list[str], Path], ProgramState],
    ) -> None:
        with NamedTemporaryFile() as file:
            state = program_state(
                [
                    "--process-efm",
                    "--process-vbi",
                    "--export-metadata",
                    "--appimage",
                    file.name,
                ],
                Path("tests/files/pal_svideo.tbc"),
            )
            helper = FileHelper(state.opts, state.config)

            # ensure appimage only used for tbc-tools
            for k, v in helper.tools.items():
                if k in self.appimage_tbc_tools_procs:
                    assert v == [Path(file.name), str(k)]
                else:
                    assert v == Path(str(k))

    def test_out_file_dir(  # noqa: D102
        self,
        program_state: Callable[[list[str], Path, str], ProgramState],
    ) -> None:
        state = program_state(
            [
                "--process-efm",
                "--process-vbi",
                "--export-metadata",
            ],
            Path("tests/files/pal_svideo.tbc"),
            "invalid_dir/test",
        )
        helper = FileHelper(state.opts, state.config)

        with pytest.raises(exceptions.FileIOError) as e:
            helper.check_output_dir()

            assert e.value == "Output directory does not exist (invalid_dir/test)."

    def test_out_file(  # noqa: D102
        self,
        program_state: Callable[[list[str], Path, str], ProgramState],
    ) -> None:
        with NamedTemporaryFile(suffix=".mkv") as file:
            state = program_state(
                [
                    "--process-efm",
                    "--process-vbi",
                    "--export-metadata",
                ],
                Path("tests/files/pal_svideo.tbc"),
                file.name,
            )
            helper = FileHelper(state.opts, state.config)

            with pytest.raises(exceptions.FileIOError) as e:
                helper.check_output_file()

                assert (
                    e.value == f"{file.name} exists, use --overwrite or move the file."
                )

        with NamedTemporaryFile(suffix=".luma.mkv") as file:
            state = program_state(
                [
                    "--process-efm",
                    "--process-vbi",
                    "--export-metadata",
                    "--two-step",
                ],
                Path("tests/files/pal_svideo.tbc"),
                file.name,
            )
            helper = FileHelper(state.opts, state.config)

            with pytest.raises(exceptions.FileIOError) as e:
                helper.check_output_file()

                assert (
                    e.value == f"{file.name} exists, use --overwrite or move the file."
                )
