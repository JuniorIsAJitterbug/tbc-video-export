from __future__ import annotations

import logging
import os
from ast import literal_eval
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import ChromaDecoder, ProfileType, VideoSystem
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
    _validate_luma_only_opts(state, parser, opts)
    _validate_decoder_opts(state, opts)


def _validate_line_opts(parser: argparse.ArgumentParser, opts: Opts) -> None:
    # check custom field/frame line opts
    field_frame_opts = [
        "first_active_field_line",
        "last_active_field_line",
        "first_active_frame_line",
        "last_active_frame_line",
    ]

    if any(getattr(opts, x) is not None for x in field_frame_opts):
        if opts.vbi or opts.full_vertical or opts.letterbox:
            parser.error(
                "arguments [--vbi | --letterbox]: not allowed with arguments "
                "[--ffll | --lfll | --ffrl | --lfrl]"
            )
        elif not all(getattr(opts, x) is not None for x in field_frame_opts):
            parser.error(
                "the following arguments are required: "
                "[--ffll & --lfll & --ffrl & --lfrl]"
            )


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


def _validate_ansi_support(opts: Opts) -> None:
    # check if ansi is supported on Windows and disable progress if not
    if not ansi.has_ansi_support():
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


def _validate_luma_only_opts(
    state: ProgramState, parser: argparse.ArgumentParser, opts: Opts
) -> None:
    # check luma only redundant opts
    if opts.luma_only or opts.luma_4fsc:
        if opts.chroma_decoder is not None:
            parser.error(
                "arguments --chroma-decoder: not allowed with --luma-only or "
                "--luma-4fsc (redundant)"
            )

        if opts.profile != state.config.get_default_profile(ProfileType.DEFAULT).name:
            parser.error(
                "arguments --profile: not allowed with --luma-only or "
                "--luma-4fsc (redundant), try --profile-luma"
            )

    elif opts.profile_luma != state.config.get_default_profile(ProfileType.LUMA).name:
        parser.error(
            "arguments --profile-luma: only allowed with --luma-only or --luma-4fsc"
        )


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


def _validate_decoder_opts(state: ProgramState, opts: Opts) -> None:
    """Validate chroma-decoder opts."""
    # this is only available on cvbs/ld or when --chroma-decoder-luma is used
    if opts.luma_nr is not None and state.decoder_luma is ChromaDecoder.MONO:
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
