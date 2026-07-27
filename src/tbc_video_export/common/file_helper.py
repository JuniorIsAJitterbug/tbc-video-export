from __future__ import annotations

import os
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from tbc_video_export.common import consts, exceptions
from tbc_video_export.common.enums import FlagHelper, TBCType, ToolType
from tbc_video_export.common.utils import files
from tbc_video_export.data import ToolsetData
from tbc_video_export.files import (
    ConfigFile,
    InputFile,
    MetadataFile,
    OutputFile,
)

if TYPE_CHECKING:
    from tbc_video_export.opts import Opts


class FileHelper:
    """Helper for files.

    Handles reading the TBC json, checking if files exist and generating paths.
    """

    def __init__(self, opts: Opts, config: ConfigFile) -> None:
        self._opts = opts
        self._config = config

        self._profile = self._config.get_profile(
            ConfigFile.ProfileFilter(self._opts.profile)
        )

        # overwrite audio profile if opt set
        if self._opts.audio_profile is not None:
            self._profile.audio_profile = config.get_audio_profile(
                self._opts.audio_profile
            )
        # initially set both input and output files to the input file
        self.input_file = InputFile.from_opt(self._opts.input_file)
        self.output_file = OutputFile.from_opt(
            self._opts.output_file or self._opts.input_file
        )

        self.tools = self._get_tool_paths()

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
        ext = (
            self.output_container
            if self.output_container.startswith(".")
            else f".{self.output_container}"
        )
        return self.output_file.path.with_suffix(ext)

    @cached_property
    def output_video_file_luma(self) -> Path:
        """Return absolute path to the output video file for luma.

        This is used when two-step is enabled when merging.
        """
        return self.output_file.path.with_suffix(
            f".{consts.TWO_STEP_OUT_FILE_LUMA_SUFFIX}.{self.output_container}"
        )

    @property
    def tbc_metadata(self) -> MetadataFile:
        """Returns metadata helper.

        This will create the helper if it does not exist.
        """
        if not getattr(
            self,
            "_tbc_metadata",
            False,
        ):
            self._tbc_metadata = MetadataFile(
                Path(self._opts.input_tbc_json)
                if self._opts.input_tbc_json is not None
                else self.input_file.path.with_suffix(".tbc.json")
            )

        return self._tbc_metadata

    @tbc_metadata.setter
    def tbc_metadata(self, file_name: Path) -> None:
        """Set the metadata Helper.

        This can be used when vbi-process generates a new metadata file.
        """
        self._tbc_metadata = MetadataFile(file_name)

    def check_output_dir(self) -> None:
        """Check if output directory exists.

        This throws an exception if output directory does not exist.
        """
        if not self.output_file.dir.is_dir():
            raise exceptions.FileIOError(
                f"Output directory does not exist ({self.output_file.dir})."
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

    def get_log_file(
        self,
        tool_type: ToolType,
        tbc_type: TBCType,
        timestamp: str = consts.CURRENT_TIMESTAMP,
    ) -> Path:
        """Return absolute path to log file for tool/tbc type."""
        return self.output_file.dir.joinpath(
            f"{timestamp}_{self.input_file.name}_{tool_type}"
            f"_{FlagHelper.get_flags_str(tbc_type, '_')}.log"
        )

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
        toolset = ToolsetData.get(self._opts.toolset)

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
