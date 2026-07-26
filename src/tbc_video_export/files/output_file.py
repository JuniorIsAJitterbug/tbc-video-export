from __future__ import annotations

from functools import cached_property
from pathlib import Path


class OutputFile:
    """Container for output file data."""

    def __init__(self, output_file: Path) -> None:
        self._output_file = output_file

    @classmethod
    def from_opt(cls, value: str) -> OutputFile:
        """Return OutputFile from an input opt."""
        return OutputFile(Path(value))

    @cached_property
    def path(self) -> Path:
        """Return absolute path to output file without a file extension."""
        return self._output_file.absolute()

    @cached_property
    def dir(self) -> Path:
        """Return absolute path to directory containing output file."""
        return self.path.parent

    @cached_property
    def name(self) -> str:
        """Return name of output file."""
        return self.path.stem

    @property
    def ffmetadata_file(self) -> Path:
        """Returns absolute path to metadata file."""
        return self.path.with_suffix(".ffmetadata")

    @property
    def cc_file(self) -> Path:
        """Returns absolute path to subtitle file ."""
        return self.path.with_suffix(".scc")
