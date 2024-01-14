from __future__ import annotations

from collections import abc
from collections.abc import Generator, Sequence
from pathlib import Path
from typing import TypeAlias


class FlatList:
    """List wrapper to allow adding various types into a flat list."""

    def __init__(self, values: _FlatListValues = None) -> None:
        self.data: list[str] = []
        self.append(values)

    def __str__(self) -> str:
        """Return data as a space separated string."""
        return " ".join(self.data)

    def __bool__(self) -> bool:
        """Return True contains data."""
        return len(self.data) > 0

    def append(self, values: _FlatListValues) -> None:
        """Append data to the list."""
        match values:
            case None:
                pass

            case list() | tuple() | abc.Generator():
                for v in values:
                    self.append(v)

            case FlatList():
                self.append(values.data)

            case v if v is not Sequence:
                self.data.append(str(values))

            case _:
                pass


# accepted FlatList values
_FlatListValues: TypeAlias = (
    str
    | Path
    | int
    | float
    | FlatList
    | Generator["_FlatListValues", None, None]
    | Sequence["_FlatListValues"]
    | None
)
