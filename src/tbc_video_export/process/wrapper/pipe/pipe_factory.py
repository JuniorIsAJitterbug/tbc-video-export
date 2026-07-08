from __future__ import annotations

import os
from dataclasses import astuple, dataclass
from importlib import import_module
from typing import TYPE_CHECKING

from tbc_video_export.common.enums import PipeType
from tbc_video_export.process.wrapper.pipe.pipe_dummy import PipeDummy
from tbc_video_export.process.wrapper.pipe.pipe_os import PipeOS

if TYPE_CHECKING:
    from pathlib import Path

    from tbc_video_export.common.enums import TBCType, ToolType
    from tbc_video_export.process.wrapper.pipe.pipe import Pipe


@dataclass
class PipeFactoryConfig:
    """Config class for PipeFactory creation."""

    pipe_type: PipeType
    tool_type: ToolType
    tbc_type: TBCType
    force_dummy: bool = False
    async_nt_pipes: bool = False


class PipeFactory:
    """Factory class for Pipes."""

    @classmethod
    def create(cls, config: PipeFactoryConfig) -> Pipe:
        """Create a pipe based on PipeType."""
        pipe_type, process_type, tbc_type, force_dummy, async_nt_pipes = astuple(config)

        match pipe_type:
            # if pipe type is NULL or force null
            case pipe_type if pipe_type is PipeType.NULL or force_dummy:
                # set some readable strings for dry-runs
                in_name = f"[PIPE_IN_{str(process_type).upper()}_{tbc_type}]"
                out_name = f"[PIPE_OUT_{str(process_type).upper()}_{tbc_type}]"
                return cls.create_dummy_pipe(in_name, out_name)

            case PipeType.NAMED:
                if os.name == "posix":
                    return import_module(
                        "tbc_video_export.process.wrapper.pipe.pipe_named_posix"
                    ).PipeNamedPosix(process_type, tbc_type)

                if os.name == "nt":
                    if async_nt_pipes:
                        return import_module(
                            "tbc_video_export.process.wrapper.pipe.pipe_named_nt_async"
                        ).PipeNamedNTAsync(process_type, tbc_type)

                    return import_module(
                        "tbc_video_export.process.wrapper.pipe.pipe_named_nt"
                    ).PipeNamedNT(process_type, tbc_type)

                raise NotImplementedError(f"Named pipes not implemented for {os.name}")

            case PipeType.OS:
                return PipeOS(process_type, tbc_type)

            case _:
                raise NotImplementedError(f"Could not create pipe of type {pipe_type}.")

    @classmethod
    def create_dummy_pipe(
        cls, stdin_str: Path | str = "PIPE_IN", stdout_str: Path | str = "PIPE_OUT"
    ) -> Pipe:
        """Force create a null pipe."""
        return PipeDummy(stdin_str, stdout_str)
