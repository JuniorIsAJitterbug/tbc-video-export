from __future__ import annotations

import argparse
import logging
from ast import literal_eval
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import FieldOrder, ProfileType
from tbc_video_export.common.utils import ansi
from tbc_video_export.opts.opts import AudioTrackOpt

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from tbc_video_export.config import Config, Profile, SubProfile


def add_ffmpeg_opts(config: Config, parent: argparse.ArgumentParser) -> None:
    """Add FFmpeg opts to the parent arg parser."""
    # chroma/combined profiles
    profile_names = config.get_profile_names(ProfileType.DEFAULT)
    profile_default = config.get_default_profile(ProfileType.DEFAULT).name

    # ffmpeg arguments
    ffmpeg_opts = parent.add_argument_group("ffmpeg")

    ffmpeg_opts.add_argument(
        "--profile",
        type=str,
        choices=profile_names,
        default=profile_default,
        metavar="profile_name",
        help="Specify an FFmpeg profile to use. "
        f"(default: {profile_default})\n"
        "See --list-profiles to see the available profiles.",
    )

    # luma profiles
    luma_profile_names = config.get_profile_names(ProfileType.LUMA)
    luma_profile_default = config.get_default_profile(ProfileType.LUMA).name

    ffmpeg_opts.add_argument(
        "--profile-luma",
        type=str,
        choices=luma_profile_names,
        default=luma_profile_default,
        metavar="profile_name",
        help="Specify an FFmpeg profile to use for luma. "
        f"(default: {luma_profile_default})\n"
        "See --list-profiles to see the available profiles.",
    )

    ffmpeg_opts.add_argument(
        "--list-profiles",
        action=_ActionListProfiles,
        profiles=config.profiles,
        help="Show available profiles.",
    )

    ffmpeg_opts.add_argument(
        "--audio-track",
        dest="audio_track",
        action="append",
        default=[],
        type=_validate_audio_track_opts,
        metavar="file_name",
        help="Audio track to mux.\nYou can use this option multiple times.",
    )

    ffmpeg_opts.add_argument(
        "--audio-track-advanced",
        dest="audio_track",
        action="append",
        default=[],
        type=_validate_audio_track_advanced_opts,
        metavar=(
            "["
            "file_name, "
            "title, "
            "language, "
            "rate, "
            "sample_format, "
            "channels, "
            "channel_layout, "
            "offset"
            "]"
        ),
        help="Audio track to mux (advanced).\n"
        "You can use this option multiple times.\n"
        "Only file_name is required. None must be used when skipping an argument.\n"
        "Examples:\n"
        '\'["/path/to/file.flac", "HiFi", "eng", 192000]\'\n'
        '\'["/path/to/file.flac", "Linear", "eng", None, None, None, None, 0.15]\'\n'
        '\'["/path/to/file.pcm", "Analog Audio", None, 44100, "s16le", 2]\'\n'
        '\'["/path/to/file.dts", "PCM Surround", "eng", 44100, "s16le", 6, "5.1"]\'\n',
    )

    ffmpeg_opts.add_argument(
        "--metadata",
        nargs=2,
        default=[],
        action="append",
        metavar=("key", "value"),
        help="Add metadata to output file.\n"
        "You can use this option multiple times.\n"
        "Example:\n"
        "--metadata Title foo --metadata Year 2024",
    )

    ffmpeg_opts.add_argument(
        "--metadata-file",
        type=_check_metadata_file_exists,
        default=[],
        action="append",
        metavar="filename",
        help="Add metadata to output file from ffmetadata files.\n"
        "See https://ffmpeg.org/ffmpeg-formats.html#Metadata-1 for details.\n"
        "Note: When using --export-metadata the generated ffmetadata file is also "
        "used.\n"
        "Files defined here are used before any generated metadata and take "
        "priority.\n",
    )

    ffmpeg_opts.add_argument(
        "--field-order",
        type=FieldOrder,
        choices=list(FieldOrder),
        default=FieldOrder.TFF,
        metavar="order",
        help="Set a field order. (default: tff)\n"
        "Available formats:\n  "
        + "\n  ".join(f"{e.name.lower()!s:<5s} {e.value}" for e in FieldOrder),
    )

    ffmpeg_opts.add_argument(
        "--force-anamorphic",
        action="store_true",
        default=False,
        help="Force widescreen aspect ratio.",
    )

    ffmpeg_opts.add_argument(
        "--force-black-level",
        type=_validate_black_levels_opts,
        metavar="R[,G,B]",
        default=None,
        help="Force black levels using the colorlevels filter.\n"
        "Use a comma sperated list of numbers to provide values for colorlevels.\n"
        "If a single number is provided it is used for all 3.",
    )

    ffmpeg_opts.add_argument(
        "--thread-queue-size",
        type=int,
        default=1024,
        metavar="int",
        help="Sets the thread queue size for FFmpeg. (default: 1024)\n"
        "Reduce this if you are having OOM issues as a higher value\n"
        "will allow the decoder to consume more memory.",
    )

    ffmpeg_opts.add_argument(
        "--checksum",
        action="store_true",
        default=False,
        help="Enable SHA256 checksumming on the output streams. (default: no)\n"
        "This will create a .sha256 file next to your output file.\n"
        "This may reduce export FPS slightly. FFmpeg must be used to verify checksums.",
    )


class _ActionListProfiles(argparse.Action):
    """Custom action for listing profiles.

    This exits the application after use.
    """

    def __init__(self, profiles: list[Profile], nargs: int = 0, **kwargs: Any) -> None:
        self._profiles = profiles
        super().__init__(nargs=nargs, **kwargs)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,  # noqa: ARG002
        values: str | Sequence[Any] | None,  # noqa: ARG002
        option_strings: str,  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        for profile in self._profiles:
            sub_profiles: list[SubProfile] = [profile.video_profile]

            logging.getLogger("console").info(
                f"{profile.name}{' (default)' if profile.is_default else ''}"
            )

            if profile.profile_type is not ProfileType.DEFAULT:
                logging.getLogger("console").info(
                    f"  {ansi.dim('Profile Type:')} {profile.profile_type}"
                )

            logging.getLogger("console").info(
                f"  {ansi.dim('Container:')}\t{profile.video_profile.container}\n"
                f"  {ansi.dim('Video Codec:')}\t{profile.video_profile.codec} "
                f"({profile.video_format})"
            )

            if video_opts := profile.video_profile.opts:
                logging.getLogger("console").info(
                    f"  {ansi.dim('Video Opts:')}\t{video_opts}"
                )

            if profile.audio_profile is not None:
                sub_profiles.append(profile.audio_profile)
                logging.getLogger("console").info(
                    f"  {ansi.dim('Audio Codec:')}\t{profile.audio_profile.codec}"
                )
                if profile.audio_profile.opts:
                    logging.getLogger("console").info(
                        f"  {ansi.dim('Audio Opts:')}\t{profile.audio_profile.opts}"
                    )

            if profile.filter_profiles:
                for _profile in profile.filter_profiles:
                    sub_profiles.append(_profile)
                    logging.getLogger("console").info(
                        f"  {ansi.dim('Filter:')}\t{_profile.video_filter}"
                    )

            logging.getLogger("console").info(
                f"  {ansi.dim('Sub Profiles:')}\t"
                f"{', '.join(profile.name for profile in sub_profiles)}"
            )

            logging.getLogger("console").info("")
        parser.exit()


def _check_metadata_file_exists(value: str) -> Path:
    """Return metadata path if it exists."""
    if (path := Path(value)).is_file():
        return path.absolute()

    raise exceptions.FileIOError(f"Metadata file {value} not found.")


def _validate_audio_track_opts(value: str) -> AudioTrackOpt:
    """Return AudioTrackOpt from string."""
    return AudioTrackOpt(Path(value).absolute())


def _validate_audio_track_advanced_opts(value: str) -> AudioTrackOpt:
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


def _validate_black_levels_opts(value: str) -> tuple[int, int, int] | None:
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
