from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING

from tbc_video_export.common import VideoSystemData, consts, exceptions
from tbc_video_export.common.enums import (
    ChromaDecoder,
    ExportMode,
    FlagHelper,
    TBCType,
    VideoSystem,
)
from tbc_video_export.common.utils import ansi
from tbc_video_export.config.config import GetProfileFilter
from tbc_video_export.process.parser.export_state import ExportState

if TYPE_CHECKING:
    from tbc_video_export.common.file_helper import FileHelper
    from tbc_video_export.common.tbc_json_helper import TBCJsonHelper
    from tbc_video_export.config.config import Config
    from tbc_video_export.config.profile import Profile
    from tbc_video_export.opts import Opts


@dataclass
class ProgramState:
    """Stores the program state."""

    opts: Opts
    config: Config
    file_helper: FileHelper
    export = ExportState()

    @property
    def current_export_mode(self) -> ExportMode:
        """Return the current export mode.

        This will return export_mode unless it has been set manually.
        """
        if not getattr(self, "_current_export_mode", False):
            return self.export_mode

        return self._current_export_mode

    @current_export_mode.setter
    def current_export_mode(self, export_mode: ExportMode) -> None:
        """Set the current export mode."""
        logging.getLogger("console").debug(
            f"Current export mode changed from {self.current_export_mode.name} "
            f"to {export_mode.name}."
        )
        self._current_export_mode = export_mode

    @property
    def tbc_json(self) -> TBCJsonHelper:
        """Return TBC JSON helper."""
        return self.file_helper.tbc_json

    @cached_property
    def export_mode(self) -> ExportMode:
        """The export mode of the program.

        This determines the processes that will run and their configuration.
        """
        tbc_types = self.tbc_types

        # overwrite export mode if opts set
        if self.opts.luma_4fsc:
            return ExportMode.LUMA_4FSC

        # set export mode
        match tbc_types:
            case TBCType.LUMA:
                return ExportMode.LUMA

            case _ as tbc_types if TBCType.CHROMA in tbc_types:
                return (
                    ExportMode.LUMA if self.opts.luma_only else ExportMode.CHROMA_MERGE
                )

            case TBCType.COMBINED:
                return (
                    ExportMode.LUMA_EXTRACTED
                    if self.opts.luma_only
                    else ExportMode.CHROMA_COMBINED_LD
                    if self.file_helper.is_combined_ld
                    else ExportMode.CHROMA_COMBINED
                )

            case _:
                raise exceptions.TBCTypeError(
                    f"No export mode found for tbc type {tbc_types}."
                )

    @cached_property
    def tbc_types(self) -> TBCType:
        """List of TBC types detected."""
        return self.file_helper.tbc_types

    @cached_property
    def video_system(self) -> VideoSystem:
        """Video system detected."""
        return (
            self.tbc_json.video_system
            if self.opts.video_system is None
            else self.opts.video_system
        )

    @cached_property
    def video_system_data(self) -> VideoSystemData:
        """Video system data."""
        return VideoSystemData.get(self.video_system)

    @cached_property
    def decoder_luma(self) -> ChromaDecoder:
        """Chroma decoder for Luma TBCs."""
        if self.opts.chroma_decoder_luma is not None:
            return self.opts.chroma_decoder_luma

        return ChromaDecoder.MONO

    @cached_property
    def decoder_chroma(self) -> ChromaDecoder:
        """Chroma decoder for Chroma/Combined TBCs."""
        if self.opts.chroma_decoder is None:
            return self.video_system_data.chroma_decoder[self.export_mode]

        return self.opts.chroma_decoder

    @cached_property
    def is_widescreen(self) -> bool:
        """Return true if widescreen is set in json or manually."""
        if self.tbc_json.is_widescreen and self.opts.letterbox:
            raise exceptions.InvalidOptsError(
                "--letterbox should not be used when isWidescreen is set."
            )

        return self.opts.force_anamorphic or self.tbc_json.is_widescreen

    @cached_property
    def decoder_line_preset(self) -> VideoSystemData.ActiveLines:
        """Return decoder line preset from opts/config."""
        video_system = self.video_system_data

        # add full vertical -> vbi crop
        if self.opts.vbi or self.profile.include_vbi:
            return video_system.active_lines["vbi"]

        if self.opts.full_vertical or self.opts.vbi or self.profile.include_vbi:
            return video_system.active_lines["full_vertical"]

        if self.opts.letterbox:
            if self.video_system is VideoSystem.PAL_M:
                raise exceptions.SampleRequiredError(
                    f"{str(self.video_system).upper()} letterbox"
                )

            return video_system.active_lines["letterbox"]

        return video_system.active_lines["default"]

    @cached_property
    def dry_run(self) -> bool:
        """Whether the program will execute the procs or just print them."""
        return self.opts.dry_run

    @property
    def profile(self) -> Profile:
        """Return selected profile."""
        return self.config.get_profile(
            GetProfileFilter(
                self.opts.profile,
                self.opts.hwaccel_type,
                self.video_system,
            )
        )

    @cached_property
    def total_frames(self) -> int:
        """Total frames detected from the TBC json."""
        tbc_frame_count = self.tbc_json.frame_count
        start = self.opts.start or 0
        length = (
            self.opts.length
            if self.opts.length is not None
            else tbc_frame_count - start
        )

        return min(tbc_frame_count - start, max(0, length))

    def __str__(self) -> str:
        """Return formatted string of program state."""
        log_files: list[str] = []

        if self.opts.log_process_output:
            log_files.append(f"{consts.CURRENT_TIMESTAMP}_*.log")

        if self.opts.debug:
            log_files.append(f"{consts.CURRENT_TIMESTAMP}_debug.log")

        log_files_str = "Disabled" if not log_files else ", ".join(log_files)

        match self.current_export_mode:
            case ExportMode.CHROMA_MERGE:
                decoders = f"{self.decoder_luma} + {self.decoder_chroma}"
                export_mode = "Luma + Chroma (merged)"

            case ExportMode.CHROMA_COMBINED | ExportMode.CHROMA_COMBINED_LD:
                decoders = f"{self.decoder_chroma}"
                export_mode = "Luma + Chroma (combined)"

            case ExportMode.LUMA_4FSC:
                decoders = f"{TBCType.NONE}"
                export_mode = "Luma (4FSC)"

            case ExportMode.LUMA_EXTRACTED:
                decoders = f"{self.decoder_luma}"
                export_mode = "Luma (extracted)"

            case ExportMode.LUMA:
                decoders = f"{self.decoder_luma}"
                export_mode = "Luma"

        if all(
            t in FlagHelper.get_flags(self.tbc_types)
            for t in (TBCType.LUMA, TBCType.CHROMA)
        ):
            tbc_type = "S-Video (Y+C)"
        else:
            tbc_type = "Composite (CVBS)"

        two_step_mode_str = "(two-step)" if self.opts.two_step else ""

        output_file: list[str] = []
        profile: list[str] = []

        if self.opts.two_step:
            output_file.append(str(self.file_helper.output_video_file_luma))

        output_file.append(str(self.file_helper.output_video_file))

        profile.append(
            self.profile.name
            + (ansi.error_color(" **DEPRECATED**") if self.profile.deprecated else "")
        )

        output_files = ", ".join(output_file)
        profiles = (
            f"{', '.join(profile)} "
            f"{'[external]' if self.config.get_config_file() is not None else ''}"
        )

        col_w: dict[str, int] = {
            "k1": 32,
            "v1": 7,
            "k2": 31,
            "v2": 17,
            "k3": 33,
            "v3": 50,
        }

        return (
            f"{ansi.dim('Input TBC:'):<{col_w['k1']}s} "
            f"{self.file_helper.tbc_luma}\n"
            f"{ansi.dim('Output Files:'):<{col_w['k1']}s} "
            f"{output_files}\n"
            f"{ansi.dim('Log Files:'):<{col_w['k1']}s} "
            f"{log_files_str}\n\n"
            f"{ansi.dim('Video System:'):<{col_w['k1']}s} "
            f"{str(self.video_system).upper():<{col_w['v1']}s}"
            f"{ansi.dim('TBC Type:'):<{col_w['k2']}s} "
            f"{tbc_type:<{col_w['v2']}s}"
            f"{ansi.dim('Chroma Decoder:'):<{col_w['k3']}s} "
            f"{decoders:<{col_w['v3']}s}\n"
            f"{ansi.dim('Total Fields:'):<{col_w['k1']}s} "
            f"{self.tbc_json.field_count:<{col_w['v1']}d}"
            f"{ansi.dim('Total Frames:'):<{col_w['k2']}s} "
            f"{self.total_frames:<{col_w['v2']}d}"
            f"{ansi.dim('Export Mode:'):<{col_w['k3']}s} "
            f"{export_mode} {two_step_mode_str:<{col_w['v3']}s}\n\n"
            f"{ansi.dim('Profile:'):<{col_w['k1']}s} "
            f"{profiles}\n"
            f"{ansi.dim('Frame Type:'):<{col_w['k1']}s} "
            f"{self.opts.field_order}\n\n"
        )
