from __future__ import annotations

import importlib.metadata

_metadata = importlib.metadata.metadata("tbc-video-export")


def get_url_from_metadata(name: str) -> str:
    """Returns a URL from the tool.poetry.urls entry in pyproject.toml."""
    return next(
        (
            url.split(" ")[1]
            for url in _metadata.get_all("Project-URL")  # pyright: ignore[reportOptionalIterable]
            if str(url).startswith(name)
        ),
        f"{name}_url",
    )
