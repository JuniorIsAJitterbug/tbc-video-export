from __future__ import annotations

import os
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from tbc_video_export.common import consts, exceptions
from tbc_video_export.common.enums import FlagHelper, TBCType, ToolType
from tbc_video_export.common.metadata_helper import MetadataHelper
from tbc_video_export.common.toolsets import toolsets
from tbc_video_export.common.utils import files
from tbc_video_export.config.config import GetProfileFilter

if TYPE_CHECKING:
    from tbc_video_export.config.config import Config
    from tbc_video_export.opts import Opts


class FileHelper:
    """Helper for files.

    Handles reading the TBC json, checking if files exist and generating paths.
    """

    def __init__(self, opts: Opts, config: Config) -> None:
        self._opts = opts
        self._config = config

        self._profile = self._config.get_profile(GetProfileFilter(self._opts.profile))

        # overwrite audio profile if opt set
        if self._opts.audio_profile is not None:
            self._profile.audio_profile = config.get_audio_profile(
                self._opts.audio_profile
            )
        # initially set both input and output files to the input file
        # file without file extension
        self._input_path = self._output_path = Path(self._opts.input_file).parent

        # path to file
        self._input_file_name = self._output_file_name = Path(
            self._opts.input_file
        ).stem

        # set output file path/name if set to new path
        if self._opts.output_file is not None:
            self._output_path = Path(self._opts.output_file).parent
            self._output_file_name = Path(self._opts.output_file).stem

        self.tools = self._get_tool_paths()
        self.tbcs = self._set_tbc_files()

    @cached_property
    def input_name(self) -> Path:
        """Return absolute path to input file without file extension."""
        return Path(self._input_path).joinpath(self._input_file_name)

    @cached_property
    def output_name(self) -> Path:
        """Return absolute path to output without file extension."""
        return Path(self._output_path).joinpath(self._output_file_name)

    @cached_property
    def is_combined_ld(self) -> bool:
        """Returns True if the TBC is for LaserDisc.

        This only checks if the TBC type is combined and an EFM file is
        located. There may be a more reliable way of doing this.
        """
        return TBCType.COMBINED in self.tbcs and self.efm_file is not None

    @property
    def efm_file(self) -> Path | None:
        """Returns absolute path to EFM file if it exists."""
        if (file := self.get_input_file_from_ext("efm")).is_file():
            return file
        return None

    @property
    def ffmetadata_file(self) -> Path:
        """Returns absolute path to metadata file."""
        return self.get_output_file_from_ext("ffmetadata")

    @property
    def cc_file(self) -> Path:
        """Returns absolute path to subtitle file ."""
        return self.get_output_file_from_ext("scc")

    @property
    def tbc_types(self) -> TBCType:
        """Returns all TBC types found."""
        types = TBCType.NONE

        for t in self.tbcs:
            types |= t

        # remove none if others set
        if types is not TBCType.NONE:
            types &= ~TBCType.NONE

        return types

    @property
    def tbc_metadata(self) -> MetadataHelper:
        """Returns metadata helper.

        This will create the helper if it does not exist.
        """
        if not getattr(
            self,
            "_tbc_metadata",
            False,
        ):
            self._tbc_metadata = MetadataHelper(
                Path(self._opts.input_tbc_json)
                if self._opts.input_tbc_json is not None
                else self.input_name.with_suffix(".tbc.json")
            )

        return self._tbc_metadata

    @tbc_metadata.setter
    def tbc_metadata(self, file_name: Path) -> None:
        """Set the metadata Helper.

        This can be used when vbi-process generates a new metadata file.
        """
        self._tbc_metadata = MetadataHelper(file_name)

    @cached_property
    def tbc_luma(self) -> Path:
        """Return the absolute path to the luma (or combined) TBC."""
        if TBCType.LUMA in self.tbcs:
            return self.tbcs[TBCType.LUMA]

        if TBCType.COMBINED in self.tbcs:
            return self.tbcs[TBCType.COMBINED]

        raise exceptions.TBCError("Unable to find luma TBC.")

    @cached_property
    def output_container(self) -> str:
        """Return container used for output video file."""
        return (
            self._opts.profile_container
            if self._opts.profile_container is not None
            else self._profile.video_profile.container
        )

    @cached_property
    def output_video_file(self) -> Path:
        """Return absolute path to the output video file."""
        return self.get_output_file_from_ext(self.output_container)

    @cached_property
    def output_video_file_luma(self) -> Path:
        """Return absolute path to the output video file for luma.

        This is used when two-step is enabled when merging.
        """
        return self.get_output_file_from_ext(
            f"{consts.TWO_STEP_OUT_FILE_LUMA_SUFFIX}.{self.output_container}"
        )

    def get_log_file(
        self,
        tool_type: ToolType,
        tbc_type: TBCType,
        timestamp: str = consts.CURRENT_TIMESTAMP,
    ):
        """Return absolute path to log file for tool/tbc type."""
        return Path(self._output_path).joinpath(
            f"{timestamp}_{self._input_file_name}_{tool_type}"
            f"_{FlagHelper.get_flags_str(tbc_type, '_')}.log"
        )

    def get_output_file_from_ext(self, extension: Path | str) -> Path:
        """Return absolute path to output file with extension."""
        return self.output_name.with_suffix(f".{extension}")

    def get_input_file_from_ext(self, extension: Path | str) -> Path:
        """Return absolute path to input file with extension."""
        return self.input_name.with_suffix(f".{extension}")

    def check_output_dir(self) -> None:
        """Check if output directory exists.

        This throws an exception if output directory does not exist.
        """
        if not Path(self._output_path).is_dir():
            raise exceptions.FileIOError(
                f"Output directory does not exist ({self._output_path})."
            )

    def check_output_file(self) -> None:
        """Check if output file exists.

        This throws an exception if output file exists.
        """
        if not self._opts.overwrite:
            files = [self.output_video_file]

            if self._opts.two_step:
                files.append(self.output_video_file_luma)

            for file in files:
                if file.is_file():
                    raise exceptions.FileIOError(
                        f"{file} exists, use --overwrite or move the file."
                    )

    def _set_tbc_files(self) -> dict[TBCType, Path]:
        """Create a dict containing the absolute path to the TBC files based on type."""
        tbcs: dict[TBCType, Path] = {}

        # input files
        tbc = f"{self.input_name}.tbc"
        tbc_chroma = f"{self.input_name}_chroma.tbc"

        if (tbc_chroma := Path(tbc_chroma)).is_file():
            tbcs[TBCType.CHROMA] = tbc_chroma

        if (tbc := Path(tbc)).is_file():
            if TBCType.CHROMA in tbcs:
                tbcs[TBCType.LUMA] = tbc
            else:
                tbcs[TBCType.COMBINED] = tbc

        # ensure tbcs exist
        if len(tbcs) == 0:
            raise exceptions.TBCError("TBC not found at location.")

        # if for some reason we found a _chroma.tbc but no .tbc
        if TBCType.CHROMA in tbcs and TBCType.LUMA not in tbcs:
            raise exceptions.TBCError("Location contains chroma TBC but no luma TBC.")

        return tbcs

    def _get_tool_paths(self) -> dict[ToolType, list[Path]]:
        """Get required tool paths from PATH or script path."""
        tools: dict[ToolType, list[Path]] = {}
        required_tools: list[ToolType] = [
            ToolType.FFMPEG,
        ]

        if not self._opts.no_dropout_correct and not self._opts.luma_4fsc:
            required_tools.append(ToolType.DROPOUT_CORRECT)

        if not self._opts.luma_4fsc:
            required_tools.append(ToolType.CHROMA_DECODE)

        if self._opts.process_vbi:
            required_tools.append(ToolType.VBI_PROCESS)

        if self._opts.export_metadata:
            required_tools.append(ToolType.METADATA_EXPORT)

        for tool in required_tools:
            tools[tool] = self._get_tool_path(tool)

        return tools

    def _get_tool_path(self, tool_type: ToolType) -> list[Path]:
        """Return path for tool."""
        toolset = toolsets[self._opts.toolset]

        if os.name == "nt":
            # append .exe on NT
            return [files.find_binary(f"{toolset.get_tool_name(tool_type)!s}.exe")]

        paths = [
            files.find_binary(f"{toolset.get_tool_name(tool_type)!s}"),
        ]

        if self._opts.tbc_tools_appimage and toolset.supports_appimage(tool_type):
            # prepend list with appimage file
            paths.insert(
                0,
                files.find_binary(self._opts.tbc_tools_appimage),
            )

        return paths
