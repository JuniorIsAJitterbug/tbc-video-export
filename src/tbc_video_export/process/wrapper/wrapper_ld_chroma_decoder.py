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
                self._get_padding_opt(),
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
        decoder = (
            self._state.decoder_chroma
            if self.tbc_type is not TBCType.LUMA
            else self._state.decoder_luma
        )

        match self._state.video_system:
            case VideoSystem.PAL | VideoSystem.PAL_M:
                if decoder not in {
                    ChromaDecoder.MONO,
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
                    ChromaDecoder.MONO,
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

    def _get_active_line_opts(self) -> FlatList | None:
        """Return active line opts."""
        video_system_data = self._state.video_system_data
        opts = self._state.opts

        # return user values if set
        if self._state.opts.contains_active_line_opts():
            return FlatList(
                (
                    opts.convert_opt("first_active_field_line", "--ffll"),
                    opts.convert_opt("last_active_field_line", "--lfll"),
                    opts.convert_opt("first_active_frame_line", "--ffrl"),
                    opts.convert_opt("last_active_frame_line", "--lfrl"),
                ),
            )

        # return static active line values if non default export mode
        if self._state.decoder_line_preset != video_system_data.active_lines["default"]:
            active_lines = self._state.decoder_line_preset

            return FlatList(
                (
                    "--ffll",
                    active_lines.first_field,
                    "--lfll",
                    active_lines.last_field,
                    "--ffrl",
                    active_lines.first_frame,
                    "--lfrl",
                    active_lines.last_frame,
                )
            )

        return None

    def _get_padding_opt(self) -> FlatList | None:
        """Return padding opt."""
        opts = self._state.opts

        if opts.output_padding is not None:
            return FlatList(self._state.opts.convert_opt("output_padding", "--pad"))

        if (padding := self._state.decoder_line_preset.padding) is not None:
            return FlatList(("--pad", padding))

        return None

    def _get_misc_opts(self) -> FlatList:
        """Return ld-chroma-decoder opts."""
        decoder_opts = FlatList()

        thread_count = self._state.opts.threads

        if (t := self._state.opts.decoder_threads) is not None:
            thread_count = t

        if thread_count != 0:
            decoder_opts.append(("-t", thread_count))

        decoder_opts.append(
            (
                self._state.opts.convert_opt("start", "-s"),
                self._state.opts.convert_opt("length", "-l"),
                self._state.opts.convert_opt("reverse", "-r"),
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
