from __future__ import annotations

import logging
import os
from ast import literal_eval
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import (
    ChromaDecoder,
    ExportMode,
    TBCType,
    VideoSystem,
)
from tbc_video_export.common.utils import ansi
from tbc_video_export.opts.opts import AudioTrackOpt, Opts

if TYPE_CHECKING:
    import argparse
    from typing import Any

    from tbc_video_export.program_state import ProgramState


def validate_opts(
    state: ProgramState, parser: argparse.ArgumentParser, opts: Opts
) -> None:
    """Validate any nonsensical opt combinations."""
    _validate_line_opts(parser, opts)
    _validate_video_system(state, parser, opts)
    _validate_ansi_support(opts)
    _validate_luma_only_opts(parser, opts)
    _validate_video_format(parser, opts)
    _validate_decoder_opts(state, opts)


def valiate_metadata_file_exists(value: str) -> Path:
    """Return metadata path if it exists."""
    if (path := Path(value)).is_file():
        return path.absolute()

    raise exceptions.FileIOError(f"Metadata file {value} not found.")


def validate_audio_track_opts(value: str) -> AudioTrackOpt:
    """Return AudioTrackOpt from string."""
    return AudioTrackOpt(Path(value).absolute())


def validate_audio_track_advanced_opts(value: str) -> AudioTrackOpt:
    """Validate input types for the audio track advanced object."""
    try:
        data: list[Any] = literal_eval(value)
        type_check: set[bool] = set()

        if not data:
            raise exceptions.FileIOError(
                "File path is required for ffmpeg track, see --help for examples."
            )

        # ensure input are correct types
        with suppress(IndexError):
            type_check.add(isinstance(data[0], str))
            type_check.add(isinstance(data[1], str | None))
            type_check.add(isinstance(data[2], str | None))
            type_check.add(isinstance(data[3], str | int | None))
            type_check.add(isinstance(data[4], str | None))
            type_check.add(isinstance(data[5], int | None))
            type_check.add(isinstance(data[6], str | None))
            type_check.add(isinstance(data[7], int | float | None))

        if False in type_check:
            raise SyntaxError

        # clone input and change file name to absolute path
        opts = data.copy()
        opts[0] = Path(data[0]).absolute()

        return AudioTrackOpt(*opts)
    except (SyntaxError, AttributeError) as e:
        raise exceptions.InvalidOptsError(
            "Invalid FFmpeg audio track opts, check --help for examples."
        ) from e


def validate_black_levels_opts(value: str) -> tuple[int, int, int] | None:
    """Validate black level opts.

    If a single value is provded we return it three times, if 3 values are provides we
    return all 3.
    """
    try:
        if values := value.split(","):
            if len(values) == 1:
                return (int(values[0]), int(values[0]), int(values[0]))

            if len(values) == 3:
                return (int(values[0]), int(values[1]), int(values[2]))
    except ValueError as e:
        raise exceptions.InvalidOptsError(
            "Invalid black level opts, check --help for examples."
        ) from e

    raise exceptions.InvalidOptsError(
        "Invalid black levels, check --help for examples."
    )


def _validate_line_opts(parser: argparse.ArgumentParser, opts: Opts) -> None:
    if opts.contains_active_line_opts() and (
        opts.vbi or opts.full_vertical or opts.letterbox
    ):
        parser.error(
            "arguments [--vbi | --full-vertical | --letterbox]: "
            "not allowed with arguments "
            "[--ffll | --lfll | --ffrl | --lfrl]"
        )

    if opts.letterbox and opts.force_anamorphic:
        parser.error("arguments --force-anamorphic: not allowed when letterbox is set")


def _validate_video_system(
    state: ProgramState, parser: argparse.ArgumentParser, opts: Opts
) -> None:
    # check video system incompatible opts
    match state.video_system:
        case VideoSystem.PAL | VideoSystem.PAL_M:
            if opts.oftest:
                parser.error(
                    "arguments --oftest: not allowed when video-system is not ntsc"
                )

            if opts.ntsc_phase_comp is not None:
                parser.error(
                    "arguments --ntsc-phase-comp/--no-ntsc-phase-comp: not allowed "
                    "when video-system is not NTSC"
                )

            if opts.chroma_nr is not None:
                parser.error(
                    "arguments --chroma-nr: not allowed when video-system is not ntsc"
                )

        case VideoSystem.NTSC:
            if opts.simple_pal:
                parser.error(
                    "arguments --simple-pal: not allowed when --video-system is ntsc"
                )


def _validate_video_format(parser: argparse.ArgumentParser, opts: Opts) -> None:
    # require bitdepth if format set
    if opts.video_format is not None and opts.video_bitdepth is None:
        parser.error("setting a video format requires a bitdepth.\n")


def _validate_ansi_support(opts: Opts) -> None:
    # check if ansi is supported on Windows and disable progress if not
    if not ansi.has_ansi_support() and (not opts.quiet or not opts.no_progress):
        if os.name == "nt":
            logging.getLogger("console").critical(
                "Windows Version < 10.0.14393 (Windows 10 Anniversary Update 1607) "
                "detected.\n"
                "This version of Windows is unable to support ANSI escape sequences.\n"
                "The software will run but be unable to display realtime progress.\n"
            )

        logging.getLogger("console").critical(
            "No support for ANSI escape sequences.\n"
            "The software will run but be unable to display realtime progress.\n"
        )

        opts.no_progress = True


def _validate_luma_only_opts(parser: argparse.ArgumentParser, opts: Opts) -> None:
    # check luma only redundant opts
    if (opts.luma_only or opts.luma_4fsc) and opts.chroma_decoder is not None:
        parser.error(
            "arguments --chroma-decoder: not allowed with --luma-only or "
            "--luma-4fsc (redundant)"
        )


def _validate_decoder_opts(state: ProgramState, opts: Opts) -> None:
    """Validate chroma-decoder opts."""
    if state.export_mode is ExportMode.LUMA_4FSC:
        return

    # check if luma-nr is valid with luma decoder for split and chroma for combined
    # this requires luma decoder to be manually set for split
    decoder = (
        state.decoder_chroma
        if TBCType.COMBINED in state.tbc_types
        else state.decoder_luma
    )

    if opts.luma_nr is not None and decoder is ChromaDecoder.MONO:
        raise exceptions.InvalidOptsError(
            "--luma-nr is not implemented with the mono decoder."
        )

    if opts.simple_pal and state.decoder_chroma not in [
        ChromaDecoder.TRANSFORM2D,
        ChromaDecoder.TRANSFORM3D,
    ]:
        raise exceptions.InvalidOptsError(
            "--simple-pal is only implemented with Transform2D/Transform3D."
        )

    if opts.reverse and not opts.no_dropout_correct:
        raise exceptions.InvalidOptsError(
            "arguments --reverse: requires --no-dropout-correct, run dropout "
            "correction manually if required"
        )
