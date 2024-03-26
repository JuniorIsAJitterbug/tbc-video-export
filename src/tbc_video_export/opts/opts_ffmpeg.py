from __future__ import annotations

from typing import TYPE_CHECKING

from tbc_video_export.common import consts
from tbc_video_export.common.enums import FieldOrder, ProfileType
from tbc_video_export.opts import opt_actions, opt_types, opt_validators

if TYPE_CHECKING:
    import argparse

    from tbc_video_export.config import Config


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
        "See --list-profiles to see the available profiles."
        "\n\n",
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
        help="Specify an FFmpeg profile to use for Luma. "
        f"(default: {luma_profile_default})\n"
        "See --list-profiles to see the available profiles."
        "\n\n",
    )

    ffmpeg_opts.add_argument(
        "--profile-container",
        type=str,
        metavar="profile_container",
        help="Override an FFmpeg profile to use a specific container. Compatibility \n"
        "with profile is not guaranteed."
        "\n\n",
    )

    ffmpeg_opts.add_argument(
        "--profile-add-filter",
        dest="profile_additional_filters",
        action="append",
        default=[],
        type=opt_types.TypeAdditionalFilter(config),
        metavar="filter_name",
        help="Use an additional filter profile when encoding. Compatibility \n"
        "with profile is not guaranteed.\n"
        "You can use this option muiltiple times."
        "\n\n",
    )

    ffmpeg_opts.add_argument(
        "--list-profiles",
        action=opt_actions.ActionListProfiles,
        config=config,
        help="Show available profiles.\n\n"
        f"You can view this in the browser here:\n"
        f"{consts.PROJECT_URL_WIKI_PROFILES}\n\n",
    )

    ffmpeg_opts.add_argument(
        "--append-video-filter",
        type=str,
        metavar="filter",
        help="Add a custom filter to the video segment of the complex filter.\n"
        "Compatibility with profile is not guaranteed.\n"
        "Use --dry-run to ensure your filter looks correct before encoding.\n\n"
        "Examples:\n"
        '--append-video-filter "scale=3480x2160:flags=lanczos,setdar=4/3"'
        "\n\n",
    )

    ffmpeg_opts.add_argument(
        "--append-other-filter",
        type=str,
        metavar="filter",
        help="Add a custom filter to the end of the complex filter.\n"
        "Compatibility with profile is not guaranteed.\n"
        "Use --dry-run to ensure your filter looks correct before encoding.\n\n"
        "Examples:\n"
        '--append-other-filter "[2:a]loudnorm=i=-14"'
        "\n\n",
    )

    ffmpeg_opts.add_argument(
        "--audio-track",
        dest="audio_track",
        action="append",
        default=[],
        type=opt_validators.validate_audio_track_opts,
        metavar="file_name",
        help="Audio track to mux.\nYou can use this option multiple times.\n\n",
    )

    ffmpeg_opts.add_argument(
        "--audio-track-advanced",
        dest="audio_track",
        action="append",
        default=[],
        type=opt_validators.validate_audio_track_advanced_opts,
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
        "Only file_name is required. None must be used when skipping an argument.\n\n"
        "Examples:\n"
        '\'["/path/to/file.flac", "HiFi", "eng", 192000]\'\n'
        '\'["/path/to/file.flac", "Linear", "eng", None, None, None, None, 0.15]\'\n'
        '\'["/path/to/file.pcm", "Analog Audio", None, 44100, "s16le", 2]\'\n'
        '\'["/path/to/file.dts", "PCM Surround", "eng", 44100, "s16le", 6, "5.1"]\'\n'
        "\n\n",
    )

    ffmpeg_opts.add_argument(
        "--metadata",
        nargs=2,
        default=[],
        action="append",
        metavar=("key", "value"),
        help="Add metadata to output the file.\n"
        "You can use this option multiple times.\n"
        "Example:\n\n"
        "--metadata Title foo --metadata Year 2024"
        "\n\n",
    )

    ffmpeg_opts.add_argument(
        "--metadata-file",
        type=opt_validators.valiate_metadata_file_exists,
        default=[],
        action="append",
        metavar="filename",
        help="Add metadata to the output of the file using ffmetadata files.\n"
        "You can use this option multiple times.\n\n"
        "See https://ffmpeg.org/ffmpeg-formats.html#Metadata-1 for details.\n\n"
        "Note: When using --export-metadata the generated ffmetadata file is also "
        "used.\n"
        "Files defined here are used before any generated metadata and take "
        "priority.\n"
        "\n\n",
    )

    ffmpeg_opts.add_argument(
        "--field-order",
        type=opt_types.TypeFieldOrder(parent),
        choices=list(FieldOrder),
        default=FieldOrder.TFF,
        metavar="order",
        help="Set a field order. (default: tff)\n"
        "Available formats:\n\n  "
        + "\n  ".join(f"{e.name.lower()!s:<5s} {e.value}" for e in FieldOrder)
        + "\n\n",
    )

    ffmpeg_opts.add_argument(
        "--force-anamorphic",
        action="store_true",
        default=False,
        help="Force widescreen aspect ratio.\n\n",
    )

    ffmpeg_opts.add_argument(
        "--force-black-level",
        type=opt_validators.validate_black_levels_opts,
        metavar="R[,G,B]",
        default=None,
        help="Force black levels using the colorlevels filter.\n"
        "Use a comma-separated list of numbers to provide values for colorlevels.\n"
        "If a single number is provided, it is used for all 3."
        "\n\n",
    )

    ffmpeg_opts.add_argument(
        "--thread-queue-size",
        type=int,
        default=1024,
        metavar="int",
        help="Set the thread queue size for FFmpeg. (default: 1024)\n"
        "Reduce this if you are having out-of-memory issues as a higher value\n"
        "will allow the decoder to consume more memory."
        "\n\n",
    )

    ffmpeg_opts.add_argument(
        "--checksum",
        action="store_true",
        default=False,
        help="Enable SHA256 checksumming on the output streams. (default: no)\n"
        "This will create a .sha256 file next to your output file.\n"
        "This may reduce export FPS slightly. FFmpeg must be used to verify checksums."
        "\n\n",
    )
