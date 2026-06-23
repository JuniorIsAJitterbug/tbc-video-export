#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = "<=3.14"
# dependencies = [
#   "tbc-video-export",
#   "dunamai (>=1.19.0,<2.0.0)",
#   "pyinstaller-versionfile (>=2.1.1,<4.0.0)",
#   "pyinstaller (>=6.3.0,<7.0.0)",
# ]
# [tool.uv.sources]
# tbc-video-export = { path = "../", editable = true }
# ///

from __future__ import annotations

import os

if os.name != "nt":
    raise SystemExit("Must be run on Windows")

import logging
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Final

import dunamai
import PyInstaller.__main__
from pyinstaller_versionfile import create_versionfile

from tbc_video_export.common import consts

PROJECT_VERSION: Final = dunamai.Version.parse(consts.PROJECT_VERSION).base
PATH_ENTRY: Final = Path(f"src/{'tbc-video-export'.replace('-', '_')}/__main__.py")
PATH_EXE: Final = Path("tbc-video-export.exe")
PATH_ICON: Final = Path("assets/icon.ico")

logger: Final = logging.getLogger(__name__)
logger.info(f"Building Windows binary, version {PROJECT_VERSION}")


@contextmanager
def create_version_file(file_dir: str | Path):  # noqa: D103
    file_path = Path(file_dir).joinpath("versionfile.txt")

    logger.debug(f"Creating version file {file_path}")

    try:
        create_versionfile(
            output_file=str(file_path),
            version=PROJECT_VERSION,
            product_name=consts.APPLICATION_NAME,
            original_filename=str(PATH_EXE),
            legal_copyright=consts.PROJECT_LICENSE,
            file_description=consts.PROJECT_SUMMARY,
            company_name=consts.PROJECT_URL,
        )

        yield file_path
    finally:
        file_path.unlink(True)


with tempfile.TemporaryDirectory() as appdir, create_version_file(appdir) as file_path:
    PyInstaller.__main__.run(
        [
            str(PATH_ENTRY),
            "--clean",
            "--collect-submodules",
            "application",
            "--icon",
            str(PATH_ICON),
            "--version-file",
            str(file_path),
            "--onefile",
            "--name",
            consts.APPLICATION_NAME,
        ]
    )
