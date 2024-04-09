from __future__ import annotations

import argparse

from tbc_video_export.common.enums import ChromaDecoder
from tbc_video_export.opts import opt_types


def add_ldtool_opts(parent: argparse.ArgumentParser) -> None:
    """Add ldtool opts to the parent argparser."""
    # decoder
    decoder_opts = parent.add_argument_group("decoder")

    decoder_opts.add_argument(
        "-s",
        "--start",
        type=int,
        metavar="int",
        help="Specify the start frame number.\n\n",
    )

    decoder_opts.add_argument(
        "-l",
        "--length",
        type=int,
        metavar="int",
        help="Specify the number of frames to process.\n\n",
    )

    decoder_opts.add_argument(
        "--reverse",
        action="store_true",
        default=False,
        help="Reverse the field order to second/first.\n\n",
    )

    decoder_opts.add_argument(
        "--output-padding",
        type=int,
        metavar="int",
        help="Pad the output frame to a multiple of these many pixels.\n\n",
    )

    decoder_lines_opts = decoder_opts.add_mutually_exclusive_group()

    decoder_lines_opts.add_argument(
        "--vbi",
        action="store_true",
        default=False,
        help="Show the VBI segment in the output video.\n"
        "This uses full-vertical and applies a crop filter.\n\n",
    )

    decoder_lines_opts.add_argument(
        "--full-vertical",
        action="store_true",
        default=False,
        help="Adjust FFLL/LFLL/FFRL/LFRL for full vertical export.\n\n",
    )

    decoder_lines_opts.add_argument(
        "--letterbox",
        action="store_true",
        default=False,
        help="Adjust FFLL/LFLL/FFRL/LFRL for letterbox crop.\n\n",
    )

    decoder_opts.add_argument(
        "--first-active-field-line",
        "--ffll",
        type=int,
        metavar="int",
        help="The first visible line of a field.\n\n"
        "  Range 1-259 for NTSC (default: 20)\n"
        "        2-308 for PAL  (default: 22)"
        "\n\n",
    )

    decoder_opts.add_argument(
        "--last-active-field-line",
        "--lfll",
        type=int,
        metavar="int",
        help="The last visible line of a field.\n\n"
        "  Range 1-259 for NTSC (default: 259)\n"
        "        2-308 for PAL  (default: 308)"
        "\n\n",
    )

    decoder_opts.add_argument(
        "--first-active-frame-line",
        "--ffrl",
        type=int,
        metavar="int",
        help="The first visible line of a field.\n\n"
        "  Range 1-525 for NTSC (default: 40)\n"
        "        1-620 for PAL  (default: 44)"
        "\n\n",
    )

    decoder_opts.add_argument(
        "--last-active-frame-line",
        "--lfrl",
        type=int,
        metavar="int",
        help="The last visible line of a field.\n\n"
        "  Range 1-525 for NTSC (default: 525)\n"
        "        1-620 for PAL  (default: 620)"
        "\n\n",
    )

    decoder_opts.add_argument(
        "--chroma-decoder",
        type=opt_types.TypeChromaDecoder(parent),
        choices=list(ChromaDecoder),
        metavar="decoder",
        help="Set the chroma decoder to be used.\n"
        "Available decoders:\n\n"
        f"  {ChromaDecoder.MONO} (default for LUMA)\n\n"
        f"  {ChromaDecoder.PAL2D}\n"
        f"  {ChromaDecoder.TRANSFORM2D} (default for PAL/PAL-M S-Video)\n"
        f"  {ChromaDecoder.TRANSFORM3D} (default for PAL/PAL-M CVBS)\n\n"
        f"  {ChromaDecoder.NTSC1D}\n"
        f"  {ChromaDecoder.NTSC2D} (default for NTSC S-Video and CVBS)\n"
        f"  {ChromaDecoder.NTSC3D} (default for NTSC CVBS LD)\n"
        f"  {ChromaDecoder.NTSC3DNOADAPT}"
        "\n\n",
    )

    decoder_opts.add_argument(
        "--chroma-decoder-luma",
        type=opt_types.TypeChromaDecoder(parent),
        choices=list(ChromaDecoder),
        metavar="decoder",
        help="Set the chroma decoder to be used for luma.\n"
        "You likely do not need to touch this.\n"
        "Available decoders:\n\n"
        f"  {ChromaDecoder.MONO} (default)\n\n"
        f"  {ChromaDecoder.PAL2D}\n"
        f"  {ChromaDecoder.TRANSFORM2D}\n"
        f"  {ChromaDecoder.TRANSFORM3D}\n\n"
        f"  {ChromaDecoder.NTSC1D}\n"
        f"  {ChromaDecoder.NTSC2D}\n"
        f"  {ChromaDecoder.NTSC3D}\n"
        f"  {ChromaDecoder.NTSC3DNOADAPT}"
        "\n\n",
    )

    decoder_opts.add_argument(
        "--chroma-gain",
        type=float,
        metavar="float",
        help="Gain factor applied to chroma components.\n"
        "This does not apply to the luma decoder for Y/C-separated TBCs.\n"
        "\n\n",
    )

    decoder_opts.add_argument(
        "--chroma-phase",
        type=float,
        metavar="float",
        help="Phase rotation applied to chroma components in degrees.\n"
        "This does not apply to the luma decoder for Y/C-separated TBCs.\n"
        "\n\n",
    )

    decoder_opts.add_argument(
        "--luma-nr",
        type=float,
        metavar="float",
        help="Luma noise reduction level in dB.\n"
        "This does not apply to the chroma decoder for Y/C-separated TBCs.\n"
        "You likely do not need to use this and should instead apply any\n"
        "noise reduction in post.\n"
        "\n\n",
    )

    decoder_opts.add_argument(
        "--transform-threshold",
        type=float,
        metavar="float",
        help="Transform: Uniform similarity threshold in 'threshold' mode.\n\n",
    )

    decoder_opts.add_argument(
        "--transform-thresholds",
        type=str,
        metavar="file_name",
        help="Transform: File containing per-bin similarity thresholds in "
        "'threshold' mode."
        "\n\n",
    )

    # decoder (ntsc)
    ntsc_decoder_opts = parent.add_argument_group("decoder (NTSC)")
    ntsc_decoder_opts.add_argument(
        "--chroma-nr",
        type=float,
        metavar="float",
        help="Chroma noise reduction level in dB.\n"
        "This does not apply to the luma decoder for Y/C-separated TBCs.\n"
        "You likely do not need to use this and should instead apply any\n"
        "noise reduction in post.\n"
        "\n\n",
    )

    ntsc_decoder_opts.add_argument(
        "--ntsc-phase-comp",
        action=argparse.BooleanOptionalAction,
        help="Enable or disable adjusting phase per line using burst phase.\n"
        "S-Video and CVBS have this option enabled by default.\n"
        "CVBS LD has this option disabled by default."
        "\n\n",
    )

    ntsc_decoder_opts.add_argument(
        "--oftest",
        action="store_true",
        default=False,
        help="Overlay the adaptive filter map (only used for testing).\n\n",
    )

    # decoder (pal)
    pal_decoder_opts = parent.add_argument_group("decoder (PAL)")
    pal_decoder_opts.add_argument(
        "--simple-pal",
        action="store_true",
        default=False,
        help="Transform: Use 1D UV filter.\n\n",
    )

    # dropout-correct
    dropout_correct_opts = parent.add_argument_group("dropout correction")

    dropout_correct_opts.add_argument(
        "--no-dropout-correct",
        action="store_true",
        default=False,
        help="Disable dropout correction. (default: no)\n"
        "This will run ld-chroma-decoder without dropout correction."
        "\n\n",
    )

    # process-vbi
    process_vbi = parent.add_argument_group("process vbi")
    process_vbi.add_argument(
        "--process-vbi",
        action="store_true",
        default=False,
        help="Run ld-process-vbi before exporting. (default: no)\n\n"
        "Note: The generated JSON file will be used for decoding."
        "\n\n",
    )

    process_vbi.add_argument(
        "--process-vbi-keep-going",
        action="store_true",
        default=False,
        help="Keep going on errors. (default: no)\n\n",
    )

    # process-efm (EXPTERIMENTAL)
    process_efm = parent.add_argument_group("process efm (EXPERIMENTAL)")
    process_efm.add_argument(
        "--process-efm",
        action="store_true",
        default=False,
        help="Run ld-process-efm before exporting. (default: no)\n\n",
    )

    process_efm.add_argument(
        "--process-efm-keep-going",
        action="store_true",
        default=False,
        help="Keep going on errors. (default: no)\n\n",
    )

    process_efm.add_argument(
        "--process-efm-dts",
        action="store_true",
        default=False,
        help="Audio is DTS rather than PCM. (default: no)\n\n",
    )

    # export-metadata
    export_metadata = parent.add_argument_group("export metadata")

    export_metadata.add_argument(
        "--export-metadata",
        action="store_true",
        default=False,
        help="Run ld-export-metadata before exporting. (default: no)\n\n"
        "Note: The generated subtitles and ffmetadata will be muxed when encoding."
        "\n\n",
    )

    export_metadata.add_argument(
        "--export-metadata-keep-going",
        action="store_true",
        default=False,
        help="Keep going on errors. (default: no)\n\n",
    )
