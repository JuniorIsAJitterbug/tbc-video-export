from __future__ import annotations

import argparse

from tbc_video_export.common.enums import FieldOrder
from tbc_video_export.opts import opt_types, opt_validators


def add_ffmpeg_opts(parent: argparse.ArgumentParser) -> None:
    """Add FFmpeg opts to the parent arg parser."""
    # ffmpeg arguments
    ffmpeg_opts = parent.add_argument_group("ffmpeg")

    ffmpeg_opts.add_argument(
        "--ffmpeg-threads",
        type=int,
        metavar="int",
        help=(
            "Specify the number of FFmpeg threads.\n"
            "  - This overrides --threads, and setting to 0 uses process defaults."
            "\n\n"
        ),
    )

    ffmpeg_opts.add_argument(
        "--audio-track",
        dest="audio_track",
        action="append",
        default=[],
        type=opt_validators.validate_audio_track_opts,
        metavar="file_name",
        help="Audio track to mux.\n  - You can use this option multiple times.\n\n",
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
        help=argparse.SUPPRESS,
        # help=(
        #    "Audio track to mux (advanced).\n"
        #    "  - You can use this option multiple times.\n"
        #    "  - Only file_name is required. None must be used when skipping an arg."
        #    "\n\n"
        #    "Examples:\n"
        #    '  \'["/path/file.flac", "HiFi", "eng", 192000]\'\n'
        #    '  \'["/path/file.flac", "Linear", "eng", None, None, None, None, 0.15]\'\n'  # noqa: E501
        #    '  \'["/path/file.pcm", "Analog Audio", None, 44100, "s16le", 2]\'\n'
        #    '  \'["/path/file.dts", "PCM Surround", "eng", 44100, "s16le", 6, "5.1"]\''
        #    "\n\n"
        # ),
    )

    ffmpeg_opts.add_argument(
        "--metadata",
        nargs=2,
        default=[],
        action="append",
        metavar=("key", "value"),
        help=(
            "Add metadata to output the file.\n"
            "  - You can use this option multiple times."
            "\n\n"
            "Example:\n"
            "  --metadata Title foo --metadata Year 2024"
            "\n\n"
        ),
    )

    ffmpeg_opts.add_argument(
        "--metadata-file",
        type=opt_validators.valiate_metadata_file_exists,
        default=[],
        action="append",
        metavar="filename",
        help=(
            "Add metadata to the output of the file using ffmetadata files.\n"
            "  - You can use this option multiple times.\n"
            "  - See https://ffmpeg.org/ffmpeg-formats.html#Metadata-1 for details.\n"
            "  - When using --export-metadata the generated file is also used.\n"
            "  - Files defined here are used before any generated metadata and take\n"
            "    priority."
            "\n\n"
        ),
    )

    ffmpeg_opts.add_argument(
        "--field-order",
        type=opt_types.TypeFieldOrder(parent),
        choices=list(FieldOrder),
        default=FieldOrder.TFF,
        metavar="order",
        help=(
            "Set a field order. (default: tff)"
            "\n\n"
            "Available formats:\n  "
            + "\n  ".join(f"{e.name.lower()!s:<5s} {e.value}" for e in FieldOrder)
            + "\n\n"
        ),
    )

    ffmpeg_opts.add_argument(
        "--force-anamorphic",
        action="store_true",
        default=False,
        help=(
            "Force widescreen aspect ratio.\n"
            "  - This is not allowed when letterbox is used."
            "\n\n"
        ),
    )

    ffmpeg_opts.add_argument(
        "--force-black-level",
        type=opt_validators.validate_black_levels_opts,
        metavar="R[,G,B]",
        default=None,
        help=(
            "Force black levels using the colorlevels filter.\n"
            "  - Use comma-separated numbers.\n"
            "  - If a single number is provided, it is used for all 3."
            "\n\n"
        ),
    )

    ffmpeg_opts.add_argument(
        "--hwaccel-device",
        type=str,
        help=(
            "Hardware acceleration device.\n"
            "  - Specify a hardware device when a supported video profile is selected."
            "\n\n"
        ),
    )

    ffmpeg_opts.add_argument(
        "--no-attach-json",
        action="store_true",
        default=False,
        help="Disable embedding the TBC json in the video file. (default: no).\n\n",
    )

    ffmpeg_opts.add_argument(
        "--thread-queue-size",
        type=int,
        default=1024,
        metavar="int",
        help=(
            "Set the thread queue size for FFmpeg. (default: 1024)\n"
            "  - Reduce this if you are having out-of-memory issues as a higher value\n"
            "    will allow the decoder to consume more memory."
            "\n\n"
        ),
    )

    ffmpeg_opts.add_argument(
        "--checksum",
        action="store_true",
        default=False,
        help=(
            "Enable SHA256 checksumming on the output streams. (default: no)\n"
            "  - This will create a .sha256 file next to your output file.\n"
            "  - This may reduce export FPS slightly.\n"
            "  - FFmpeg must be used to verify checksums."
            "\n\n"
        ),
    )
