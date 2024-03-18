from __future__ import annotations

import argparse
import os
from itertools import chain
from typing import TYPE_CHECKING

from tbc_video_export.common import consts
from tbc_video_export.common.enums import (
    VideoBitDepthType,
    VideoFormatType,
    VideoSystem,
)
from tbc_video_export.opts import (
    opt_actions,
    opt_types,
    opts_ffmpeg,
    opts_ldtools,
    opts_profile,
)
from tbc_video_export.opts.opts import Opts

if TYPE_CHECKING:
    from tbc_video_export.config import Config


def parse_opts(
    config: Config, args: list[str] | None = None
) -> tuple[argparse.ArgumentParser, Opts]:
    """Parse program opts."""
    parser = argparse.ArgumentParser(
        prog=consts.APPLICATION_NAME,
        description=consts.PROJECT_SUMMARY,
        formatter_class=argparse.RawTextHelpFormatter,
        usage=f"{consts.APPLICATION_NAME} [options] input_file [output_file]\n\n"
        f"See --help or {consts.PROJECT_URL_WIKI_COMMANDLIST}\n"
        "---",
        epilog=f"Output/profile customization:\n{_get_opt_aliases()}",
    )

    if (cpu_count := os.cpu_count()) is None:
        cpu_count = 2

    # general
    general_opts = parser.add_argument_group("general")
    general_opts.add_argument("input_file", type=str, help="Path to the TBC file.\n\n")
    general_opts.add_argument(
        "output_file",
        type=str,
        nargs="?",
        help="Path to export to. (default: input_file.X)\n"
        "If no argument is provided, the output file will be placed in the same "
        "directory as the input_file.\n"
        "Do not specify a file extension, as this is set by the profile."
        "\n\n",
    )

    general_opts.add_argument(
        "--version",
        action="version",
        version=consts.PROJECT_VERSION,
        help="Show the program's version number and exit.\n\n",
    )

    general_opts.add_argument(
        "-t",
        "--threads",
        type=int,
        default=int(cpu_count / 2),
        metavar="int",
        help="Specify the number of concurrent threads.\n\n",
    )

    general_opts.add_argument(
        "--appimage",
        type=str,
        metavar="appimage file",
        help="Run the tools from an AppImage file.\n\n",
    )

    general_opts.add_argument(
        "--two-step",
        action="store_true",
        default=False,
        help="Enables two-step mode. (default: no)\n"
        "Enabling this will export Luma to a file before merging with Chroma.\n"
        "If you have issues using named pipes, this may be useful as a fallback.\n"
        "This is generally not required, will take longer, and will require more disk "
        "space.\n"
        "Used exclusively with export modes that merge luma and chroma."
        "\n\n",
    )

    # hidden, used for tests
    general_opts.add_argument(
        "--async-nt-pipes", action="store_true", help=argparse.SUPPRESS
    )

    general_opts.add_argument(
        "--video-system",
        type=opt_types.TypeVideoSystem(parser),
        choices=list(VideoSystem),
        metavar="format",
        help="Force a video system format. (default: from input.tbc.json)\n"
        "Available formats:\n\n  " + "\n  ".join(str(e) for e in VideoSystem) + "\n\n",
    )

    general_opts.add_argument(
        "--input-tbc-json",
        type=str,
        metavar="tbc_json_file",
        help="Specify a .tbc.json file.\n"
        "This is generally not needed and should be auto-detected.\n",
    )

    general_opts.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Set to overwrite existing video files. (default: no)\n\n",
    )

    general_opts.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would be run without running. (default: no)\n"
        "This is useful for debugging and validating opts."
        "\n\n",
    )

    general_opts.add_argument(
        "--dump-default-config",
        action=opt_actions.ActionDumpConfig,
        config=config,
        default=False,
        help=f"Dump the default configuration json to "
        f"{consts.EXPORT_CONFIG_FILE_NAME}.\n\n"
        f"For help on creating a custom profile, see:\n"
        f"{consts.PROJECT_URL_WIKI_PROFILES}"
        "\n\n",
    )

    # verbosity
    verbosity_opts = parser.add_argument_group("verbosity")
    verbosity_logger = verbosity_opts.add_mutually_exclusive_group()

    verbosity_logger.add_argument(
        "-q",
        "--quiet",
        action=opt_actions.ActionSetVerbosity,
        help="Only show ERROR messages. (default: no)\n\n",
    )

    verbosity_logger.add_argument(
        "-d",
        "--debug",
        action=opt_actions.ActionSetVerbosity,
        help="Do not suppress INFO, WARNING, or DEBUG messages. (default: no)\n"
        "If progress is enabled, this will not log to the console.\n"
        "Useful for debugging issues.\n"
        "End-users do not need this unless providing logs to developers."
        "\n\n",
    )

    # hidden, used for tests
    verbosity_opts.add_argument(
        "--no-debug-log", action="store_true", help=argparse.SUPPRESS
    )

    verbosity_opts.add_argument(
        "--no-progress",
        action="store_true",
        default=False,
        help="Hide the real-time progress display. (default: no)\n\n",
    )

    verbosity_opts.add_argument(
        "--show-process-output",
        action=opt_actions.ActionSetVerbosity,
        help="Show process output. (default: no)\nThis sets --no-progress.\n\n",
    )

    verbosity_opts.add_argument(
        "--log-process-output",
        action="store_true",
        default=False,
        help="Log process output. (default: no)\n"
        "This will log all process output to separate files."
        "\n\n",
    )

    opts_ldtools.add_ldtool_opts(parser)

    # luma
    luma_opts = parser.add_argument_group("luma")

    luma_opts.add_argument(
        "--luma-only",
        action="store_true",
        default=False,
        help="Only output a luma video. (default: no)\n"
        "For Y/C-separated TBCs, this is direct.\n"
        "For combined TBCs, filtering is applied to strip the color carrier signal out."
        "\n\n",
    )

    luma_opts.add_argument(
        "--luma-4fsc",
        action="store_true",
        default=False,
        help="This uses luma data from the TBC to produce a full signal frame export. "
        "(default: no)\n"
        "For combined TBCs, this does not filter out the chroma and thus has \n"
        "crosshatching."
        "\n\n",
    )

    opts_ffmpeg.add_ffmpeg_opts(parser)
    opts_profile.add_profile_opts(config, parser)

    opts = parser.parse_intermixed_args(args, namespace=Opts())
    return (parser, opts)


def _get_opt_aliases() -> str:
    pix_fmts = ", ".join(
        sorted(
            set(
                chain(
                    *((f"--{v}" for _, v in d.value.items()) for d in VideoFormatType)
                )
            )
        )
    )
    out_str = f"  Pixel Formats:\n    {pix_fmts}\n\n"

    bitdepths = ", ".join([f"--{t.value}" for t in VideoBitDepthType])
    out_str += f"  Bit Depths:\n    {bitdepths}\n\n"

    return out_str
