from __future__ import annotations

import sys
from pathlib import Path
from re import escape
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, ClassVar

import pytest

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import TBCType, ToolsetType, ToolType, VideoSystem
from tbc_video_export.common.file_helper import FileHelper
from tbc_video_export.data import ToolsetData

from .conftest import FileHelperTestCase

if TYPE_CHECKING:
    from collections.abc import Callable

    from tbc_video_export.program_state import ProgramState


class TestTBCJson:
    """Tests for tbc json helper."""

    test_cases: ClassVar[list[FileHelperTestCase]] = [
        FileHelperTestCase(
            id="pal svideo",
            input_name="pal_svideo",
            input_path=Path("tests/files/pal_svideo"),
            luma_tbc=Path("tests/files/pal_svideo.tbc"),
            output_name="out_file",
            output_path=Path("out_file"),
            output_container="mkv",
            output_video_file=Path("out_file.mkv"),
            output_video_file_luma=Path("out_file.luma.mkv"),
            is_ld=False,
            ffmetadata_file=Path("out_file.ffmetadata"),
            cc_file=Path("out_file.scc"),
            tbc_types=TBCType.LUMA | TBCType.CHROMA,
        ),
        FileHelperTestCase(
            id="pal composite",
            input_name="pal_composite",
            input_path=Path("tests/files/pal_composite"),
            luma_tbc=Path("tests/files/pal_composite.tbc"),
            output_name="out_file",
            output_path=Path("out_file"),
            output_container="mkv",
            output_video_file=Path("out_file.mkv"),
            output_video_file_luma=Path("out_file.luma.mkv"),
            is_ld=False,
            ffmetadata_file=Path("out_file.ffmetadata"),
            cc_file=Path("out_file.scc"),
            tbc_types=TBCType.COMBINED,
        ),
        FileHelperTestCase(
            id="pal composite (ld)",
            input_name="pal_composite_ld",
            input_path=Path("tests/files/pal_composite_ld"),
            luma_tbc=Path("tests/files/pal_composite_ld.tbc"),
            output_name="out_file",
            output_path=Path("out_file"),
            output_container="mkv",
            output_video_file=Path("out_file.mkv"),
            output_video_file_luma=Path("out_file.luma.mkv"),
            is_ld=True,
            ffmetadata_file=Path("out_file.ffmetadata"),
            cc_file=Path("out_file.scc"),
            tbc_types=TBCType.COMBINED,
        ),
    ]

    @pytest.mark.parametrize(
        "test_case",
        tuple(pytest.param(test_case, id=test_case.id) for test_case in test_cases),
    )
    def test_paths(
        self,
        program_state: Callable[[list[str], Path], ProgramState],
        test_case: FileHelperTestCase,
    ) -> None:
        state = program_state([], test_case.input_path)
        helper = FileHelper(state.opts, state.config)

        assert test_case.input_name == helper.input_file.name
        assert test_case.input_path.absolute() == helper.input_file.path
        assert test_case.luma_tbc.absolute() == helper.input_file.tbc_luma
        assert test_case.output_name == helper.output_file.name
        assert test_case.output_path.absolute() == helper.output_file.path
        assert test_case.output_container == helper.output_container
        assert test_case.output_video_file.absolute() == helper.output_video_file
        assert (
            test_case.output_video_file_luma.absolute() == helper.output_video_file_luma
        )
        assert test_case.is_ld == helper.input_file.is_combined_ld
        assert (
            test_case.ffmetadata_file.absolute() == helper.output_file.ffmetadata_file
        )
        assert test_case.cc_file.absolute() == helper.output_file.cc_file
        assert test_case.tbc_types == helper.input_file.tbc_types

    def test_setting_json(
        self,
        program_state: Callable[[list[str], Path], ProgramState],
    ) -> None:
        state = program_state([], Path("tests/files/pal_svideo.tbc"))
        helper = FileHelper(state.opts, state.config)

        metadata_helper = helper.tbc_metadata
        assert metadata_helper.video_system == VideoSystem.PAL

        helper.tbc_metadata = Path("tests/files/ntsc_svideo.tbc.json")
        metadata_helper = helper.tbc_metadata
        assert metadata_helper.video_system == VideoSystem.NTSC

    def test_missing_tbc(
        self,
        program_state: Callable[[list[str], Path], ProgramState],
    ) -> None:
        state = program_state([], Path("tests/files/pal_svideo.tbc"))
        helper = FileHelper(state.opts, state.config)

        # Clear tbc locations to cause exception
        helper.input_file.tbcs.clear()
        with pytest.raises(
            exceptions.TBCError, match=escape("Unable to find luma TBC.")
        ):
            _ = helper.input_file.tbc_luma

        with (
            NamedTemporaryFile(suffix="_chroma.tbc") as file,
            pytest.raises(
                exceptions.TBCError,
                match=escape("Location contains chroma TBC but no luma TBC."),
            ),
        ):
            _ = program_state([], Path(file.name.replace("_chroma.tbc", "")))

        with pytest.raises(
            exceptions.TBCError, match=escape("TBC not found at location.")
        ):
            _ = program_state([], Path("tests/files/invalid"))

    tools: ClassVar[list[ToolType]] = [
        ToolType.CHROMA_DECODE,
        ToolType.DROPOUT_CORRECT,
        ToolType.FFMPEG,
        ToolType.METADATA_EXPORT,
        ToolType.VBI_PROCESS,
    ]

    tbc_types: ClassVar[list[TBCType]] = [
        TBCType.CHROMA,
        TBCType.COMBINED,
        TBCType.LUMA,
    ]

    @pytest.mark.parametrize("tool", tuple(tools))
    @pytest.mark.parametrize("tbc_type", tuple(tbc_types))
    def test_log_files(
        self,
        program_state: Callable[[list[str], Path], ProgramState],
        tool: ToolType,
        tbc_type: TBCType,
    ) -> None:
        state = program_state([], Path("tests/files/pal_svideo.tbc"))
        helper = FileHelper(state.opts, state.config)

        timestamp = "__timestamp__"

        assert (
            helper.get_log_file(tool, tbc_type, timestamp)
            == Path(
                f"__timestamp___{helper.input_file.name}_{tool}_{tbc_type}.log"
            ).absolute()
        )

    @pytest.mark.parametrize("tool", tuple(tools))
    def test_tools(
        self,
        program_state: Callable[[list[str], Path], ProgramState],
        tool: ToolType,
    ) -> None:
        state = program_state(
            [
                "--process-vbi",
                "--export-metadata",
                "--toolset",
                f"{ToolsetType.LEGACY_TOOLS!s}",
            ],
            Path("tests/files/pal_svideo.tbc"),
        )
        helper = FileHelper(state.opts, state.config)
        toolset = ToolsetData.get(ToolsetType.LEGACY_TOOLS)

        assert helper.tools[tool] == [Path(f"{toolset.get_tool_name(tool)!s}")]

    def test_tools_appimage(
        self,
        program_state: Callable[[list[str], Path], ProgramState],
    ) -> None:
        if sys.platform != "linux":
            pytest.skip("Linux only")

        with NamedTemporaryFile() as file:
            state = program_state(
                [
                    "--process-vbi",
                    "--export-metadata",
                    "--toolset",
                    f"{ToolsetType.LEGACY_TOOLS!s}",
                    "--tbc-tools-appimage",
                    file.name,
                ],
                Path("tests/files/pal_svideo.tbc"),
            )
            helper = FileHelper(state.opts, state.config)
            toolset = ToolsetData.get(ToolsetType.LEGACY_TOOLS)

            # ensure appimage only used for tbc-tools
            for tool_type, tool_path in helper.tools.items():
                tool_name = toolset.get_tool_name(tool_type)
                if tool_type in self.tools and toolset.supports_appimage(tool_type):
                    assert tool_path == [Path(file.name), Path(f"{tool_name!s}")]
                else:
                    assert tool_path == [Path(f"{tool_name!s}")]

    def test_out_file_dir(
        self,
        program_state: Callable[[list[str], Path, str], ProgramState],
    ) -> None:
        out_name = "invalid_dir/test"
        out_path = Path(out_name)
        state = program_state(
            [
                "--process-vbi",
                "--export-metadata",
            ],
            Path("tests/files/pal_svideo.tbc"),
            out_name,
        )
        helper = FileHelper(state.opts, state.config)

        with pytest.raises(
            exceptions.FileIOError,
            match=escape(
                f"Output directory does not exist ({out_path.parent.absolute()})."
            ),
        ):
            helper.check_output_dir()

    def test_out_file(
        self,
        program_state: Callable[[list[str], Path, str], ProgramState],
    ) -> None:
        with NamedTemporaryFile(suffix=".mkv") as file:
            state = program_state(
                [
                    "--process-vbi",
                    "--export-metadata",
                ],
                Path("tests/files/pal_svideo.tbc"),
                file.name,
            )
            helper = FileHelper(state.opts, state.config)

            with pytest.raises(
                exceptions.FileIOError,
                match=escape(f"{file.name} exists, use --overwrite or move the file."),
            ):
                helper.check_output_file()

        with NamedTemporaryFile(suffix=".luma.mkv") as file:
            state = program_state(
                [
                    "--process-vbi",
                    "--export-metadata",
                    "--two-step",
                ],
                Path("tests/files/pal_svideo.tbc"),
                file.name,
            )
            helper = FileHelper(state.opts, state.config)

            with pytest.raises(
                exceptions.FileIOError,
                match=escape(f"{file.name} exists, use --overwrite or move the file."),
            ):
                helper.check_output_file()
