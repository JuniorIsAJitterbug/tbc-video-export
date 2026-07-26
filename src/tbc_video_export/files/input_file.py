from __future__ import annotations

from functools import cached_property
from pathlib import Path

from tbc_video_export.common import exceptions
from tbc_video_export.common.enums import TBCType


class InputFile:
    """Container for output file data."""

    def __init__(self, input_file: Path) -> None:
        self._input_file = input_file
        self.tbcs = self._set_tbc_files()

    @classmethod
    def from_opt(cls, value: str) -> InputFile:
        """Return InFile from an input opt."""
        return InputFile(Path(value))

    @cached_property
    def path(self) -> Path:
        """Return absolute path to input file without a file extension."""
        return self._input_file.absolute()

    @cached_property
    def dir(self) -> Path:
        """Return absolute path to directory containing input file."""
        return self.path.parent

    @cached_property
    def name(self) -> str:
        """Return name of input file."""
        return self.path.stem

    @cached_property
    def is_combined_ld(self) -> bool:
        """Returns True if the TBC is for LaserDisc.

        This only checks if the TBC type is combined and an EFM file is
        located. There may be a more reliable way of doing this.
        """
        return TBCType.COMBINED in self.tbcs and self.efm_file is not None

    @property
    def efm_file(self) -> Path | None:
        """Returns absolute path to EFM file if it exists."""
        if (file := self.path.with_suffix(".efm")).is_file():
            return file
        return None

    @property
    def tbc_types(self) -> TBCType:
        """Returns all TBC types found."""
        types = TBCType.NONE

        for t in self.tbcs:
            types |= t

        # remove none if others set
        if types is not TBCType.NONE:
            types &= ~TBCType.NONE

        return types

    @cached_property
    def tbc_luma(self) -> Path:
        """Return the absolute path to the luma (or combined) TBC."""
        if TBCType.LUMA in self.tbcs:
            return self.tbcs[TBCType.LUMA]

        if TBCType.COMBINED in self.tbcs:
            return self.tbcs[TBCType.COMBINED]

        raise exceptions.TBCError("Unable to find luma TBC.")

    def _set_tbc_files(self) -> dict[TBCType, Path]:
        """Create a dict containing the absolute path to the TBC files based on type."""
        tbcs: dict[TBCType, Path] = {}

        # input files
        tbc = self.path.with_suffix(".tbc")
        tbc_chroma = tbc.with_stem(f"{self.name}_chroma")

        if (tbc_chroma := Path(tbc_chroma)).is_file():
            tbcs[TBCType.CHROMA] = tbc_chroma

        if (tbc := Path(tbc)).is_file():
            if TBCType.CHROMA in tbcs:
                tbcs[TBCType.LUMA] = tbc
            else:
                tbcs[TBCType.COMBINED] = tbc

        # ensure tbcs exist
        if len(tbcs) == 0:
            raise exceptions.TBCError("TBC not found at location.")

        # if for some reason we found a _chroma.tbc but no .tbc
        if TBCType.CHROMA in tbcs and TBCType.LUMA not in tbcs:
            raise exceptions.TBCError("Location contains chroma TBC but no luma TBC.")

        return tbcs
