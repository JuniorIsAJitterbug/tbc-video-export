from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic

from tbc_video_export.process.wrapper.pipe import (
    PipeInputGeneric,
    PipeOutputGeneric,
)

if TYPE_CHECKING:
    from tbc_video_export.common.enums import ExportMode, TBCType


@dataclass
class WrapperConfig(Generic[PipeInputGeneric, PipeOutputGeneric]):
    """Wrapper config class."""

    export_mode: ExportMode
    tbc_type: TBCType
    input_pipes: PipeInputGeneric
    output_pipes: PipeOutputGeneric
