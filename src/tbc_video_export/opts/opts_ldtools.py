from __future__ import annotations

import argparse

from tbc_video_export.common.enums import ChromaDecoder


def add_ldtool_opts(parent: argparse.ArgumentParser) -> None:
    """Add ldtool opts to the parent argparser."""
    # decoder
    decoder_opts = parent.add_argument_group("decoder")

    decoder_opts.add_argument(
        "-s",
        "--start",
        type=int,
        metavar="int",
        help="Specify the start frame number.",
    )

    decoder_opts.add_argument(
        "-l",
        "--length",
        type=int,
        metavar="int",
        help="Specify the number of frames to process.",
    )

    decoder_opts.add_argument(
        "--reverse",
        action="store_true",
        default=False,
        help="Reverse the field order to second/first.",
    )

    decoder_opts.add_argument(
        "--output-padding",
        type=int,
        metavar="int",
        help="Pad the output frame to a multiple of this many pixels.",
    )

    decoder_vbi_opts = decoder_opts.add_mutually_exclusive_group()

    decoder_vbi_opts.add_argument(
        "--vbi",
        action="store_true",
        default=False,
        help="Adjust FFLL/LFLL/FFRL/LFRL for full vertical export.",
    )

    decoder_vbi_opts.add_argument(
        "--letterbox",
        action="store_true",
        default=False,
        help="Adjust FFLL/LFLL/FFRL/LFRL for letterbox crop.",
    )

    decoder_opts.add_argument(
        "--first-active-field-line",
        "--ffll",
        type=int,
        metavar="int",
        help="The first visible line of a field.\n"
        "  Range 1-259 for NTSC (default: 20)\n"
        "        2-308 for PAL  (default: 22)",
    )

    decoder_opts.add_argument(
        "--last-active-field-line",
        "--lfll",
        type=int,
        metavar="int",
        help="The last visible line of a field.\n"
        "  Range 1-259 for NTSC (default: 259)\n"
        "        2-308 for PAL  (default: 308)",
    )

    decoder_opts.add_argument(
        "--first-active-frame-line",
        "--ffrl",
        type=int,
        metavar="int",
        help="The first visible line of a field.\n"
        "  Range 1-525 for NTSC (default: 40)\n"
        "        1-620 for PAL  (default: 44)",
    )

    decoder_opts.add_argument(
        "--last-active-frame-line",
        "--lfrl",
        type=int,
        metavar="int",
        help="The last visible line of a field.\n"
        "  Range 1-525 for NTSC (default: 525)\n"
        "        1-620 for PAL  (default: 620)",
    )

    decoder_opts.add_argument(
        "--chroma-decoder",
        type=ChromaDecoder,
        choices=list(ChromaDecoder),
        metavar="decoder",
        help="Chroma decoder to use.\n"
        "Available decoders:\n"
        f"  {ChromaDecoder.MONO} (default for LUMA)\n"
        f"  {ChromaDecoder.PAL2D}\n"
        f"  {ChromaDecoder.TRANSFORM2D} (default for PAL/PAL-M)\n"
        f"  {ChromaDecoder.TRANSFORM3D} (default for PAL LD/CVBS)\n"
        f"  {ChromaDecoder.NTSC1D}\n"
        f"  {ChromaDecoder.NTSC2D} (default for NTSC)\n"
        f"  {ChromaDecoder.NTSC3D} (default for NTSC CVBS)\n"
        f"  {ChromaDecoder.NTSC3DNOADAPT}",
    )

    decoder_opts.add_argument(
        "--chroma-gain",
        type=float,
        metavar="float",
        help="Gain factor applied to chroma components.",
    )

    decoder_opts.add_argument(
        "--chroma-phase",
        type=float,
        metavar="float",
        help="Phase rotation applied to chroma components (degrees).",
    )

    decoder_opts.add_argument(
        "--luma-nr",
        type=float,
        metavar="float",
        help="Luma noise reduction level in dB.",
    )

    decoder_opts.add_argument(
        "--transform-threshold",
        type=float,
        metavar="float",
        help="Transform: Uniform similarity threshold in 'threshold' mode.",
    )

    decoder_opts.add_argument(
        "--transform-thresholds",
        type=str,
        metavar="file_name",
        help="Transform: File containing per-bin similarity thresholds in "
        "'threshold' mode.",
    )

    # decoder (ntsc)
    ntsc_decoder_opts = parent.add_argument_group("decoder (ntsc)")
    ntsc_decoder_opts.add_argument(
        "--chroma-nr",
        type=float,
        metavar="float",
        help="Chroma noise reduction level in dB.",
    )

    ntsc_decoder_opts.add_argument(
        "--ntsc-phase-comp",
        action=argparse.BooleanOptionalAction,
        help="Enable or disable adjusting phase per-line using burst phase.\n"
        "Enabled by default on S-Video and Composite.\n"
        "Disabled by default on Composite (LD).",
    )

    ntsc_decoder_opts.add_argument(
        "--oftest",
        action="store_true",
        default=False,
        help="Overlay the adaptive filter map (only used for testing).",
    )

    # decoder (pal)
    pal_decoder_opts = parent.add_argument_group("decoder (pal)")
    pal_decoder_opts.add_argument(
        "--simple-pal",
        action="store_true",
        default=False,
        help="Transform: Use 1D UV filter.",
    )

    # dropout-correct
    dropout_correct_opts = parent.add_argument_group("dropout correction")

    dropout_correct_opts.add_argument(
        "--no-dropout-correct",
        action="store_true",
        default=False,
        help="Disable dropout correction. (default: no)\n"
        "This will run ld-chroma-decoder without dropout correction.",
    )

    # process-vbi
    process_vbi = parent.add_argument_group("process vbi")
    process_vbi.add_argument(
        "--process-vbi",
        action="store_true",
        default=False,
        help="Run ld-process-vbi before export. (default: no)\n"
        "Note: The generated JSON file will be used for decoding.",
    )

    process_vbi.add_argument(
        "--process-vbi-keep-going",
        action="store_true",
        default=False,
        help="Keep going on error. (default: no)",
    )

    # process-efm (EXPTERIMENTAL)
    process_efm = parent.add_argument_group("process efm (EXPERIMENTAL)")
    process_efm.add_argument(
        "--process-efm",
        action="store_true",
        default=False,
        help="Run ld-process-efm before export. (default: no)",
    )

    process_efm.add_argument(
        "--process-efm-keep-going",
        action="store_true",
        default=False,
        help="Keep going on error. (default: no)",
    )

    process_efm.add_argument(
        "--process-efm-dts",
        action="store_true",
        default=False,
        help="Audio is DTS rather than PCM. (default: no)",
    )

    # export-metadata
    export_metadata = parent.add_argument_group("export metadata")

    export_metadata.add_argument(
        "--export-metadata",
        action="store_true",
        default=False,
        help="Run ld-export-metadata before export. (default: no)\n"
        "Note: The generated subtitles and ffmetadata will be used when encoding.",
    )

    export_metadata.add_argument(
        "--export-metadata-keep-going",
        action="store_true",
        default=False,
        help="Keep going on error. (default: no)",
    )
