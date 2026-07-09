from __future__ import annotations

import importlib.metadata

_metadata = importlib.metadata.metadata("tbc-video-export")


def get_value_from_metadata(key: str, fail: str = "unknown") -> str:
    """Returns value from pyproject.toml."""
    if key in _metadata:
        return _metadata[key]

    return fail


def get_url_from_metadata(name: str) -> str:
    """Returns a URL from the tool.poetry.urls entry in pyproject.toml."""
    return next(
        (
            url.split(" ")[1]
            for url in _metadata.get_all("Project-URL", "unknown")
            if f"{url}".startswith(name)
        ),
        f"{name}_url",
    )
