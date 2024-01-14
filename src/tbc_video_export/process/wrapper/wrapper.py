from __future__ import annotations

from abc import ABC, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import FlagHelper, PipeType
from tbc_video_export.common.utils import FlatList
from tbc_video_export.process.wrapper.pipe import (
    Pipe,
    PipeInputGeneric,
    PipeOutputGeneric,
)

if TYPE_CHECKING:
    from tbc_video_export.common.enums import ProcessName, TBCType
    from tbc_video_export.process.wrapper.wrapper_config import WrapperConfig
    from tbc_video_export.program_state import ProgramState


class Wrapper(ABC):
    """Abstract Wrapper class."""

    def __init__(
        self,
        state: ProgramState,
        config: WrapperConfig[PipeInputGeneric, PipeOutputGeneric],
    ) -> None:
        self._state = state
        self._config = config

        # trigger any wrapper exceptions early
        _ = self.command
        self._check_pipes()

    @property
    def binary(self) -> FlatList:
        """Return wrapped binary name."""
        return FlatList(self._state.file_helper.get_tool(self.process_name))

    @cached_property
    def tbc_type(self) -> TBCType:
        """Return TBC type for the wrapper instance."""
        return self._config.tbc_type

    @cached_property
    def pipes(self) -> tuple[Pipe, ...]:
        """Return pipes for wrapper."""
        pipes: tuple[Pipe, ...] = ()
        in_pipe = self._config.input_pipes
        out_pipe = self._config.output_pipes

        if isinstance(in_pipe, tuple):
            pipes += in_pipe
        elif isinstance(in_pipe, Pipe):
            pipes = (*pipes, in_pipe)

        if isinstance(out_pipe, tuple):
            pipes += out_pipe
        elif isinstance(out_pipe, Pipe):
            pipes = (*pipes, out_pipe)

        return pipes

    @abstractmethod
    def post_fn(self) -> None:
        """Post-process function.

        This will run after the process has finished running.
        """

    @property
    @abstractmethod
    def command(self) -> FlatList:
        """Return wrapped process arguments."""

    @cached_property
    @abstractmethod
    def process_name(self) -> ProcessName:
        """Return process name."""

    @cached_property
    @abstractmethod
    def supported_pipe_types(self) -> PipeType:
        """Supported pipe types of the wrapped process."""

    @cached_property
    @abstractmethod
    def stdin(self) -> int | None:
        """Return process stdin."""

    @cached_property
    @abstractmethod
    def stdout(self) -> int | None:
        """Return process stdout."""

    @cached_property
    @abstractmethod
    def stderr(self) -> int | None:
        """Return process stderr."""

    @cached_property
    @abstractmethod
    def log_output(self) -> bool:
        """Log output of process to file."""

    @cached_property
    @abstractmethod
    def log_stdout(self) -> bool:
        """Log stdout instead of stderr."""

    @cached_property
    @abstractmethod
    def env(self) -> dict[str, str] | None:
        """List of env args to run the process with."""

    @cached_property
    @abstractmethod
    def ignore_error(self) -> bool:
        """Ignore errors from process."""

    @cached_property
    @abstractmethod
    def stop_on_last_alive(self) -> bool:
        """Stop process of this type if it"s the last remaining."""

    def _check_pipes(self) -> None:
        """Ensure pipes are valid for wrapper."""
        # ensure all pipes are supported
        if sum(
            1
            for pipe in self.pipes
            if pipe.pipe_type not in FlagHelper.get_flags(self.supported_pipe_types)
        ):
            pipes_str = ""

            for pipe in self.pipes:
                pipes_str += str(pipe)

            raise exceptions.PipeError(
                f"{self.process_name} unable to use pipe types.\n{pipes_str}"
            )
