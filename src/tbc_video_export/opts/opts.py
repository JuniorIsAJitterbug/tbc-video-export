from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from tbc_video_export.common.enums import (
        ChromaDecoder,
        FieldOrder,
        HardwareAccelType,
        VideoFormatType,
        VideoSystem,
    )


class Opts(argparse.Namespace):
    """Program opts namespace.

    We define available options and their types to keep the linter happy.
    """

    # general
    input_file: str
    output_file: str | None
    threads: int
    tbc_tools_appimage: str
    two_step: bool
    async_nt_pipes: bool
    video_system: VideoSystem | None
    input_tbc_json: str | None
    overwrite: bool
    dry_run: bool
    config_file: str | None
    dump_default_config: bool

    # verbosity
    quiet: bool
    debug: bool
    no_debug_log: bool
    no_progress: bool
    show_process_output: bool
    log_process_output: bool

    # decoder
    decoder_threads: int | None
    start: int | None
    length: int | None
    reverse: bool
    output_padding: int | None
    vbi: bool
    full_vertical: bool
    letterbox: bool
    first_active_field_line: int | None
    last_active_field_line: int | None
    first_active_frame_line: int | None
    last_active_frame_line: int | None
    chroma_decoder: ChromaDecoder | None
    chroma_decoder_luma: ChromaDecoder | None
    chroma_gain: float | None
    chroma_phase: float | None
    luma_nr: float | None
    transform_threshold: float | None
    transform_thresholds: str | None

    # decoder (ntsc)
    ntsc_phase_comp: bool | None
    oftest: bool
    chroma_nr: float | None

    # decoder (pal)
    simple_pal: bool

    # dropout-correct
    no_dropout_correct: bool
    dropout_correct_threads: int | None

    # luma
    luma_only: bool
    luma_4fsc: bool

    # process-vbi
    process_vbi: bool
    process_vbi_keep_going: bool
    process_vbi_threads: int | None

    # process-efm
    process_efm: bool
    process_efm_keep_going: bool
    process_efm_dts: bool

    # export-metadata
    export_metadata: bool
    export_metadata_keep_going: bool

    # ffmpeg
    ffmpeg_threads: int | None
    audio_track: list[AudioTrackOpt]
    metadata: list[list[str]]
    metadata_file: list[Path]
    field_order: FieldOrder
    force_anamorphic: bool
    force_black_level: tuple[int, int, int] | None
    hwaccel_device: str | None
    no_attach_json: bool
    thread_queue_size: int
    checksum: bool

    # profile
    profile: str
    profile_luma: str

    # profile overrides
    profile_container: str | None
    profile_additional_filters: list[str]
    append_video_filter: str | None
    append_other_filter: str | None

    hwaccel_type: HardwareAccelType | None
    video_format: VideoFormatType | None
    video_bitdepth: int | None
    audio_profile: str | None

    def convert_opt(
        self, program_opt_name: str, target_opt_name: str
    ) -> str | tuple[str, str] | None:
        """Convert a program opt to a subprocess opt (list[str])."""
        if (value := getattr(self, program_opt_name)) is not None:
            if isinstance(value, bool):
                if value:
                    return target_opt_name
            else:
                return (target_opt_name, str(value))
        return None

    def contains_active_line_opts(self) -> bool:
        """Returns true if any active line opts are set."""
        return any(
            getattr(self, x) is not None
            for x in [
                "first_active_field_line",
                "last_active_field_line",
                "first_active_frame_line",
                "last_active_frame_line",
            ]
        )


@dataclass
class AudioTrackOpt:
    """Container class for audio track data."""

    file_name: Path
    title: str | None = None
    language: str | None = None

    rate: str | int | None = None
    sample_format: str | None = None
    channels: int | None = None
    layout: str | None = None
    offset: int | float | None = None


@dataclass
class MetaDataOpt:
    """Container class for meta data."""

    key: str
    value: str | int | float
