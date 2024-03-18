from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from tbc_video_export.common import consts
from tbc_video_export.common.enums import (
    HardwareAccelType,
    VideoBitDepthType,
    VideoFormatType,
)
from tbc_video_export.opts import opt_actions, opt_types

if TYPE_CHECKING:
    from tbc_video_export.config import Config


def add_profile_opts(config: Config, parent: argparse.ArgumentParser) -> None:  # noqa: C901
    """Add profile opts to the parent arg parser."""
    # chroma/combined profiles
    profile_default = config.get_default_profile().name

    # ffmpeg arguments
    profile_opts = parent.add_argument_group("profile")

    profile_opts.add_argument(
        "--profile",
        type=str,
        choices=config.get_profile_names(),
        default=profile_default,
        metavar="profile_name",
        help="Specify an FFmpeg profile to use. "
        f"(default: {profile_default})\n"
        "See --list-profiles to see the available profiles.\n"
        "Note: These are also accessible directly, e.g. --x264"
        "\n\n",
    )

    profile_opts.add_argument(
        "--list-profiles",
        action=opt_actions.ActionListProfiles,
        config=config,
        help="Show available profiles.\n\n"
        f"You can view this in the browser here:\n"
        f"{consts.PROJECT_URL_WIKI_PROFILES}\n\n",
    )

    profile_opts.add_argument(
        "--profile-container",
        "--container",
        type=str,
        metavar="profile_container",
        help="Override an FFmpeg profile to use a specific container. Compatibility \n"
        "with profile is not guaranteed."
        "\n\n",
    )

    profile_opts.add_argument(
        "--profile-add-filter",
        "--add-filter",
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

    profile_opts.add_argument(
        "--append-video-filter",
        "--append-vf",
        type=str,
        metavar="filter",
        help="Add a custom filter to the video segment of the complex filter.\n"
        "Compatibility with profile is not guaranteed.\n"
        "Use --dry-run to ensure your filter looks correct before encoding.\n\n"
        "Examples:\n"
        '--append-video-filter "scale=3480x2160:flags=lanczos,setdar=4/3"'
        "\n\n",
    )

    profile_opts.add_argument(
        "--append-other-filter",
        "--append-of",
        type=str,
        metavar="filter",
        help="Add a custom filter to the end of the complex filter.\n"
        "Compatibility with profile is not guaranteed.\n"
        "Use --dry-run to ensure your filter looks correct before encoding.\n\n"
        "Examples:\n"
        '--append-other-filter "[2:a]loudnorm=i=-14"'
        "\n\n",
    )

    # add aliases
    # hw accel aliases
    hwaccel_opts = parent.add_argument_group("hwaccel opts aliases")
    for hwaccel in HardwareAccelType:
        hwaccel_opts.add_argument(
            f"--{hwaccel.value}",
            dest="hwaccel_type",
            action=opt_actions.ActionSetVideoHardwareAccelType,
            help=argparse.SUPPRESS,
        )

    # video bit depth alias
    video_bitdepth_opts = parent.add_argument_group("video bitdepth aliases")
    for bitdepth in VideoBitDepthType:
        video_bitdepth_opts.add_argument(
            f"--{bitdepth.value}",
            dest="video_bitdepth",
            action=opt_actions.ActionSetVideoBitDepthType,
            help=argparse.SUPPRESS,
        )

    # video format aliases
    video_format_opts = parent.add_argument_group("video format aliases")

    for video_format in VideoFormatType:
        video_format_opts.add_argument(
            f"--{video_format.name.lower()}",
            dest="video_format",
            action=opt_actions.ActionSetVideoFormatType,
            help=argparse.SUPPRESS,
        )

    # profile aliases
    profile_opts = parent.add_argument_group("profile alises")

    for profile_name in config.get_profile_names():
        profile_opts.add_argument(
            f"--{profile_name}",
            default=profile_default,
            dest="profile_name",
            action=opt_actions.ActionSetProfile,
            help=argparse.SUPPRESS,
        )

    # audio profile aliases
    audio_type_opts = parent.add_argument_group("audio profile alises")

    for audio_type in config.get_audio_profile_names():
        audio_type_opts.add_argument(
            f"--{audio_type.replace('_', '-')}",
            type=str,
            action=opt_actions.ActionSetAudioOverride,
            help=argparse.SUPPRESS,
        )
