from __future__ import annotations

import os
import sys
from functools import cache
from pathlib import Path
from shutil import which

from tbc_video_export.common import exceptions


@cache
def get_runtime_directory() -> Path:
    """Return the runtime directory.

    When the script is built to a single executable using PyInstaller __file__ is
    somewhere in TEMP, so the executable location must be used instead.
    """
    return (
        Path(sys.executable)
        if getattr(sys, "frozen", False)
        else Path(os.path.realpath(sys.argv[0]))
    )


@cache
def find_binary(name: str) -> Path:
    """Return the path of a binary if found.

    This searches in the same location as the script, the current dir
    and in PATH.
    """
    # check if binary exists in the same dir as script
    script_path = get_runtime_directory().with_name(name).absolute()

    if Path(script_path).is_file():
        return script_path

    # check if binary exists in PATH or current dir
    if which(name):
        return Path(name)

    raise exceptions.FileIOError(f"{name} not in PATH or script dir.")
