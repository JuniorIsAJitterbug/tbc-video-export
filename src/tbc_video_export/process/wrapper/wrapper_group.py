from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import (
    ExportMode,
    FlagHelper,
    PipeType,
    ProcessName,
    TBCType,
)
from tbc_video_export.process.wrapper import Wrapper, WrapperConfig
from tbc_video_export.process.wrapper.pipe import (
    ConsumablePipe,
    Pipe,
    PipeFactory,
    PipeFactoryConfig,
)
from tbc_video_export.process.wrapper.wrapper_ffmpeg import WrapperFFmpeg
from tbc_video_export.process.wrapper.wrapper_ld_chroma_decoder import (
    WrapperLDChromaDecoder,
)
from tbc_video_export.process.wrapper.wrapper_ld_dropout_correct import (
    WrapperLDDropoutCorrect,
)
from tbc_video_export.process.wrapper.wrapper_ld_export_metadata import (
    WrapperLDExportMetadata,
)
from tbc_video_export.process.wrapper.wrapper_ld_process_efm import WrapperLDProcessEFM
from tbc_video_export.process.wrapper.wrapper_ld_process_vbi import WrapperLDProcessVBI

if TYPE_CHECKING:
    from tbc_video_export.program_state import ProgramState


class WrapperGroup:
    """Create a group of wrappers.

    This is based on requested procs, tbc type and export mode.
    These groups are used to run procs in "order", as some procs must run before others.
    """

    def __init__(
        self,
        state: ProgramState,
        export_mode: ExportMode,
        tbc_types: TBCType,
        process_names: ProcessName,
    ) -> None:
        self._state = state
        self._export_mode = export_mode
        self._tbc_types = tbc_types
        self._process_names = process_names

        self.wrappers: list[Wrapper] = []
        self.consumable_pipes: list[ConsumablePipe] = []

        self._create_pipe_config = partial(
            PipeFactoryConfig,
            async_nt_pipes=self._state.opts.async_nt_pipes,
            force_dummy=self._state.dry_run,
        )

        logging.getLogger("console").debug(
            f"Creating wrappers for {FlagHelper.get_flags_str(process_names, '+')}"
        )

        self._create_standalone_wrappers()
        self._create_decoder_wrappers()
        self._create_ffmpeg_wrapper()

    @property
    def export_mode(self) -> ExportMode:
        """Return export mode for the wrapper group."""
        return self._export_mode

    def _create_standalone_wrappers(
        self,
    ) -> None:
        """Create standalone wrappers that do not rely on other procs or pipes."""
        wrapper_config = WrapperConfig[None, None](
            self._export_mode, TBCType.NONE, None, None
        )

        if ProcessName.LD_PROCESS_VBI in self._process_names:
            self.wrappers.append(WrapperLDProcessVBI(self._state, wrapper_config))

        if ProcessName.LD_PROCESS_EFM in self._process_names:
            self.wrappers.append(WrapperLDProcessEFM(self._state, wrapper_config))

        if ProcessName.LD_EXPORT_METADATA in self._process_names:
            self.wrappers.append(WrapperLDExportMetadata(self._state, wrapper_config))

    def _create_decoder_wrappers(self) -> None:
        """Create decoder wrappers.

        This optionally includes dropout correction and decoding for every tbc type.
        """
        # do not add dropout-correct & decoder on 4fsc mode
        if self._export_mode == ExportMode.LUMA_4FSC:
            return

        for tbc_type in FlagHelper.get_flags(self._tbc_types):
            create_pipe_config = partial(self._create_pipe_config, tbc_type=tbc_type)

            if ProcessName.LD_DROPOUT_CORRECT in self._process_names:
                # create dropout correction -> decoder pipe
                self.consumable_pipes.append(
                    ConsumablePipe(
                        tbc_type,
                        ProcessName.LD_CHROMA_DECODER,
                        pipe := PipeFactory.create(
                            create_pipe_config(
                                PipeType.OS, ProcessName.LD_DROPOUT_CORRECT
                            )
                        ),
                    )
                )

                # create dropout correct wrapper
                self.wrappers.append(
                    WrapperLDDropoutCorrect(
                        self._state,
                        WrapperConfig[None, Pipe](
                            self._export_mode, tbc_type, None, pipe
                        ),
                    )
                )

            if ProcessName.LD_CHROMA_DECODER in self._process_names:
                if not self._get_pipes_for_consumer(
                    ProcessName.LD_CHROMA_DECODER, tbc_type
                ):
                    # if no pipes have been created for chroma-decoder, create a
                    # dummy pipe with the tbc file name
                    self.consumable_pipes.append(
                        ConsumablePipe(
                            tbc_type,
                            ProcessName.LD_CHROMA_DECODER,
                            PipeFactory.create_dummy_pipe(
                                self._state.file_helper.tbc_luma
                            ),
                        )
                    )

                # create decoder -> ffmpeg pipe
                self.consumable_pipes.append(
                    ConsumablePipe(
                        tbc_type,
                        ProcessName.FFMPEG,
                        pipe := PipeFactory.create(
                            create_pipe_config(
                                PipeType.OS
                                if self._state.opts.two_step
                                else PipeType.NAMED,
                                ProcessName.LD_CHROMA_DECODER,
                            )
                        ),
                    )
                )

                # create decoder wrapper
                self.wrappers.append(
                    WrapperLDChromaDecoder(
                        self._state,
                        WrapperConfig[Pipe, Pipe](
                            self._export_mode,
                            tbc_type,
                            self._get_pipe_for_consumer(
                                ProcessName.LD_CHROMA_DECODER, tbc_type
                            ),
                            pipe,
                        ),
                    )
                )

    def _create_ffmpeg_wrapper(self) -> None:
        """Create wrapper for ffmpeg process."""
        if ProcessName.FFMPEG in self._process_names:
            # check if any pipes created for ffmpeg, if not create
            # a dummy pipe  using the tbc file name
            if not self._get_pipes_for_consumer(ProcessName.FFMPEG, self._tbc_types):
                self.consumable_pipes.append(
                    ConsumablePipe(
                        self._tbc_types,
                        ProcessName.FFMPEG,
                        PipeFactory.create_dummy_pipe(self._state.file_helper.tbc_luma),
                    )
                )

            # create ffmpeg wrapper
            self.wrappers.append(
                WrapperFFmpeg(
                    self._state,
                    WrapperConfig[tuple[Pipe], None](
                        self._export_mode,
                        self._tbc_types,
                        self._get_pipes_for_consumer(
                            ProcessName.FFMPEG, self._tbc_types
                        ),
                        None,
                    ),
                )
            )

    def _get_pipes_for_consumer(
        self, consumer_name: ProcessName, tbc_types: TBCType
    ) -> tuple[Pipe, ...]:
        """Get pipes created for a consumer/wrapper."""
        pipes = tuple(
            group.pipe
            for group in self.consumable_pipes
            if group.consumer == consumer_name and group.tbc_type in tbc_types
        )
        # ensure we do not have multiple os stdio pipes
        if sum(1 for pipe in pipes if pipe.pipe_type is PipeType.OS) > 1:
            raise exceptions.PipeError(
                f"Multiple {PipeType.OS} pipes are not supported."
            )

        return pipes

    def _get_pipe_for_consumer(
        self, consumer_name: ProcessName, tbc_types: TBCType
    ) -> Pipe:
        """Get single pipe created for a consumer/wrapper."""
        return next(iter(self._get_pipes_for_consumer(consumer_name, tbc_types)))
