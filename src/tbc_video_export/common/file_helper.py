from __future__ import annotations

import os
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from tbc_video_export.common import consts, exceptions
from tbc_video_export.common.enums import FlagHelper, ProcessName, TBCType
from tbc_video_export.common.tbc_json_helper import TBCJsonHelper
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
        """Returns absolute path fo metadata file."""
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
    def tbc_json(self) -> TBCJsonHelper:
        """Returns TBCJson helper.

        This will create the helper if it does not exist.
        """
        if not getattr(
            self,
            "_tbc_json",
            False,
        ):
            self._tbc_json = TBCJsonHelper(
                Path(self._opts.input_tbc_json)
                if self._opts.input_tbc_json is not None
                else Path(f"{self.input_name}.tbc.json")
            )

        return self._tbc_json

    @tbc_json.setter
    def tbc_json(self, file_name: Path) -> None:
        """Set the TBCJson Helper.

        This can be used when ld-process-vbi generates a new JSON file.
        """
        self._tbc_json = TBCJsonHelper(file_name)

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
        process_name: ProcessName,
        tbc_type: TBCType,
        timestamp: str = consts.CURRENT_TIMESTAMP,
    ):
        """Return absolute path to log file for process/tbc type."""
        return Path(self._output_path).joinpath(
            f"{timestamp}_{self._input_file_name}_{process_name}"
            f"_{FlagHelper.get_flags_str(tbc_type, '_')}.log"
        )

    def get_output_file_from_ext(self, extension: Path | str) -> Path:
        """Return absolute path to output file with extension."""
        return Path(f"{self.output_name}.{extension}")

    def get_input_file_from_ext(self, extension: Path | str) -> Path:
        """Return absolute path to input file with extension."""
        return Path(f"{self.input_name}.{extension}")

    def get_tool(self, process_name: ProcessName) -> Path | list[Path | str]:
        """Return absolute path to tool binary from process."""
        # if appimage is set, all binary paths are set to the appimage location
        # so we return a list containing the appimage file with the binary
        # name we want to use
        if self._opts.appimage:
            return [self.tools[process_name], str(process_name)]

        return self.tools[process_name]

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

    def _get_tool_paths(self) -> dict[ProcessName, Path]:
        """Get required tool paths from PATH or script path."""
        tools: dict[ProcessName, Path] = {}
        tools[ProcessName.FFMPEG] = self._get_tool_path(ProcessName.FFMPEG)

        if not self._opts.no_dropout_correct and not self._opts.luma_4fsc:
            tools[ProcessName.LD_DROPOUT_CORRECT] = self._get_tool_path(
                ProcessName.LD_DROPOUT_CORRECT
            )

        if not self._opts.luma_4fsc:
            tools[ProcessName.LD_CHROMA_DECODER] = self._get_tool_path(
                ProcessName.LD_CHROMA_DECODER
            )

        if self._opts.process_vbi:
            tools[ProcessName.LD_PROCESS_VBI] = self._get_tool_path(
                ProcessName.LD_PROCESS_VBI
            )

        if self._opts.process_efm:
            tools[ProcessName.LD_PROCESS_EFM] = self._get_tool_path(
                ProcessName.LD_PROCESS_EFM
            )

        if self._opts.export_metadata:
            tools[ProcessName.LD_EXPORT_METADATA] = self._get_tool_path(
                ProcessName.LD_EXPORT_METADATA
            )

        return tools

    def _get_tool_path(self, tool_name: ProcessName) -> Path:
        # if appimage is defined, use it as the location for the tools
        if os.name != "nt":
            binary = (
                self._opts.appimage
                if self._opts.appimage
                else str(tool_name).lower().replace("_", "-")
            )
        else:
            # append .exe on NT
            binary = f"{tool_name}.exe"

        return files.find_binary(binary)
