from __future__ import annotations

import asyncio
from functools import cached_property
from typing import TYPE_CHECKING

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import (
    ChromaDecoder,
    PipeType,
    ProcessName,
    TBCType,
    VideoSystem,
    VideoSystemLines,
)
from tbc_video_export.common.utils import FlatList
from tbc_video_export.process.wrapper.wrapper import Wrapper

if TYPE_CHECKING:
    from tbc_video_export.process.wrapper.pipe import Pipe
    from tbc_video_export.process.wrapper.wrapper_config import WrapperConfig
    from tbc_video_export.program_state import ProgramState


class WrapperLDChromaDecoder(Wrapper):
    """Wrapper for ld-tools-decoder."""

    def __init__(self, state: ProgramState, config: WrapperConfig[Pipe, Pipe]) -> None:
        super().__init__(state, config)
        self._config = config

    def post_fn(self) -> None:  # noqa: D102
        pass

    @property
    def command(self) -> FlatList:  # noqa: D102
        return FlatList(
            (
                self.binary,
                self._get_gain_nr_opts(),
                "-p",
                "y4m",
                self._get_decoder_opts(),
                self._get_active_line_opts(),
                self._get_misc_opts(),
                "--input-json",
                self._state.file_helper.tbc_json.file_name,
                self._config.input_pipes.in_path,
                self._config.output_pipes.out_path,
            )
        )

    def _get_gain_nr_opts(self) -> FlatList:
        """Return ld-chroma-decoder opts."""
        gain_nr_opts = FlatList()

        if self._config.tbc_type in (TBCType.LUMA, TBCType.COMBINED):
            gain_nr_opts.append(self._state.opts.convert_opt("luma_nr", "--luma-nr"))

        if self._config.tbc_type in (TBCType.CHROMA, TBCType.COMBINED):
            gain_nr_opts.append(
                (
                    self._state.opts.convert_opt("chroma_gain", "--chroma-gain"),
                    self._state.opts.convert_opt("chroma_nr", "--chroma-nr"),
                    self._state.opts.convert_opt("chroma_phase", "--chroma-phase"),
                )
            )

        # set defaults for separated TBC
        if self._config.tbc_type is TBCType.LUMA:
            # chroma-gain not used by mono decoder, set anyway
            gain_nr_opts.append(("--chroma-gain", "0"))

        if self._config.tbc_type is TBCType.CHROMA:
            gain_nr_opts.append(("--luma-nr", "0"))

        return gain_nr_opts

    def _get_decoder_opts(self) -> FlatList:
        """Return decoder to use."""
        # validate decoders for video system
        if self.tbc_type is not TBCType.LUMA:
            decoder = self._state.decoder_chroma

            match self._state.video_system:
                case VideoSystem.PAL | VideoSystem.PAL_M:
                    if decoder not in {
                        ChromaDecoder.PAL2D,
                        ChromaDecoder.TRANSFORM2D,
                        ChromaDecoder.TRANSFORM3D,
                    }:
                        raise exceptions.InvalidChromaDecoderError(
                            f"{decoder} is not a valid decoder for "
                            f"{self._state.video_system}."
                        )

                case VideoSystem.NTSC:
                    if decoder not in {
                        ChromaDecoder.NTSC1D,
                        ChromaDecoder.NTSC2D,
                        ChromaDecoder.NTSC3D,
                        ChromaDecoder.NTSC3DNOADAPT,
                    }:
                        raise exceptions.InvalidChromaDecoderError(
                            f"{decoder} is not a valid decoder for "
                            f"{self._state.video_system}."
                        )

        return FlatList(
            (
                "-f",
                self._state.decoder_luma.value
                if self.tbc_type is TBCType.LUMA
                else self._state.decoder_chroma.value,
            )
        )

    def _get_active_line_opts(self) -> FlatList:
        """Return active line opts."""
        values: tuple[int, ...] | None = None

        if (
            self._state.opts.full_vertical
            or self._state.opts.vbi
            or self._state.profile.include_vbi
        ):
            match self._state.video_system:
                case VideoSystem.PAL:
                    values = VideoSystemLines.PAL_FULL_VERTICAL.value

                case VideoSystem.NTSC | VideoSystem.PAL_M:
                    values = VideoSystemLines.NTSC_FULL_VERTICAL.value

        if self._state.opts.letterbox:
            match self._state.video_system:
                case VideoSystem.PAL:
                    values = VideoSystemLines.PAL_LETTERBOX.value

                case VideoSystem.NTSC:
                    values = VideoSystemLines.NTSC_LETTERBOX.value

                case VideoSystem.PAL_M:
                    raise exceptions.SampleRequiredError(
                        f"{str(self._state.video_system).upper()} letterbox"
                    )

        if values is not None:
            return FlatList(
                (
                    "--ffll",
                    values[0],
                    "--lfll",
                    values[1],
                    "--ffrl",
                    values[2],
                    "--lfrl",
                    values[3],
                )
            )

        # use default/user values
        return FlatList(
            (
                self._state.opts.convert_opt("first_active_field_line", "--ffll"),
                self._state.opts.convert_opt("last_active_field_line", "--lfll"),
                self._state.opts.convert_opt("first_active_frame_line", "--ffrl"),
                self._state.opts.convert_opt("last_active_frame_line", "--lfrl"),
            ),
        )

    def _get_misc_opts(self) -> FlatList:
        """Return ld-chroma-decoder opts."""
        decoder_opts = FlatList()

        decoder_opts.append(
            (
                self._state.opts.convert_opt("start", "-s"),
                self._state.opts.convert_opt("length", "-l"),
                self._state.opts.convert_opt("reverse", "-r"),
                self._state.opts.convert_opt("threads", "-t"),
                self._state.opts.convert_opt("output_padding", "--pad"),
                self._state.opts.convert_opt("oftest", "-o"),
                self._state.opts.convert_opt("simple_pal", "--simple-pal"),
                self._state.opts.convert_opt(
                    "transform_threshold", "--transform-threshold"
                ),
                self._state.opts.convert_opt(
                    "transform_thresholds", "--transform-thresholds"
                ),
            ),
        )

        if self._state.video_system is VideoSystem.NTSC:
            # True unless ld detected
            add_phase_check = not self._state.file_helper.is_combined_ld

            # override if user has set
            if self._state.opts.ntsc_phase_comp is not None:
                add_phase_check = self._state.opts.ntsc_phase_comp

            if add_phase_check:
                decoder_opts.append("--ntsc-phase-comp")

        return decoder_opts

    @cached_property
    def process_name(self) -> ProcessName:  # noqa: D102
        return ProcessName.LD_CHROMA_DECODER

    @cached_property
    def supported_pipe_types(self) -> PipeType:  # noqa: D102
        return PipeType.NULL | PipeType.OS | PipeType.NAMED

    @cached_property
    def stdin(self) -> int | None:  # noqa: D102
        return self._config.input_pipes.in_handle

    @cached_property
    def stdout(self) -> int | None:  # noqa: D102
        return self._config.output_pipes.out_handle

    @cached_property
    def stderr(self) -> int | None:  # noqa: D102
        return asyncio.subprocess.PIPE

    @cached_property
    def log_output(self) -> bool:  # noqa: D102
        return True

    @cached_property
    def log_stdout(self) -> bool:  # noqa: D102
        return False

    @cached_property
    def env(self) -> dict[str, str] | None:  # noqa: D102
        return None

    @cached_property
    def ignore_error(self) -> bool:  # noqa: D102
        return False

    @cached_property
    def stop_on_last_alive(self) -> bool:  # noqa: D102
        return False
