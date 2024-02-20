from __future__ import annotations

import argparse
import logging
import os
from typing import TYPE_CHECKING

from tbc_video_export.common import consts
from tbc_video_export.common.enums import ProfileType, VideoSystem
from tbc_video_export.common.utils import ansi
from tbc_video_export.opts import opts_ffmpeg, opts_ldtools
from tbc_video_export.opts.opts import Opts

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from tbc_video_export.config import Config
    from tbc_video_export.program_state import ProgramState


def parse_opts(
    config: Config, args: list[str] | None = None
) -> tuple[argparse.ArgumentParser, Opts]:
    """Parse program opts."""
    parser = argparse.ArgumentParser(
        prog=consts.APPLICATION_NAME,
        description=consts.PROJECT_SUMMARY,
        formatter_class=argparse.RawTextHelpFormatter,
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
        type=_TypeVideoSystem(parser),
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
        action=_ActionDumpConfig,
        config=config,
        default=False,
        help=f"Dump the default configuration json to "
        f"{consts.EXPORT_CONFIG_FILE_NAME}."
        "\n\n",
    )

    # verbosity
    verbosity_opts = parser.add_argument_group("verbosity")
    verbosity_logger = verbosity_opts.add_mutually_exclusive_group()

    verbosity_logger.add_argument(
        "-q",
        "--quiet",
        action=_ActionSetVerbosity,
        help="Only show ERROR messages. (default: no)\n\n",
    )

    verbosity_logger.add_argument(
        "-d",
        "--debug",
        action=_ActionSetVerbosity,
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
        action=_ActionSetVerbosity,
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

    opts_ffmpeg.add_ffmpeg_opts(config, parser)

    opts = parser.parse_intermixed_args(args, namespace=Opts())
    return (parser, opts)


def validate_opts(
    state: ProgramState, parser: argparse.ArgumentParser, opts: Opts
) -> None:
    """Validate any nonsensical opt combinations."""
    _validate_line_opts(parser, opts)
    _validate_video_system(state, parser, opts)
    _validate_ansi_support(opts)
    _validate_luma_only_opts(state, parser, opts)


def _validate_line_opts(parser: argparse.ArgumentParser, opts: Opts) -> None:
    # check custom field/frame line opts
    field_frame_opts = [
        "first_active_field_line",
        "last_active_field_line",
        "first_active_frame_line",
        "last_active_frame_line",
    ]

    if any(getattr(opts, x) is not None for x in field_frame_opts):
        if opts.vbi or opts.letterbox:
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


class _ActionDumpConfig(argparse.Action):
    def __init__(self, config: Config, nargs: int = 0, **kwargs: Any) -> None:
        self._config = config
        super().__init__(nargs=nargs, **kwargs)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,  # noqa: ARG002
        values: str | Sequence[Any] | None,  # noqa: ARG002
        option_strings: str,  # noqa: ARG002
        *_: Any,
    ) -> None:
        self._config.dump_default_config(consts.EXPORT_CONFIG_FILE_NAME)
        parser.exit()


class _ActionSetVerbosity(argparse.Action):
    def __init__(self, nargs: int = 0, **kwargs: Any) -> None:
        super().__init__(nargs=nargs, **kwargs)

    def __call__(
        self,
        parser: argparse.ArgumentParser,  # noqa: ARG002
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,  # noqa: ARG002
        option_strings: str,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        if option_strings in {"--quiet", "-q"}:
            namespace.quiet = True
            namespace.no_progress = True
            namespace.show_process_output = False

        if option_strings in ("--debug"):
            namespace.debug = True

        if option_strings in ("--show-process-output"):
            namespace.show_process_output = True
            namespace.no_progress = True


class _TypeVideoSystem:
    """Return ChromaDecoder value if it exists."""

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self._parser = parser

    def __call__(self, value: str) -> VideoSystem:
        try:
            return VideoSystem[value.replace("-", "_").upper()]
        except KeyError:
            self._parser.error(
                f"argument --video-system: invalid VideoSystem value: '{value}', "
                f"check --help for available options."
            )
