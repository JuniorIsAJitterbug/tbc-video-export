from __future__ import annotations

import os

if os.name != "nt":
    raise SystemExit("Must be run on Windows")

import dunamai
import PyInstaller.__main__
from pyinstaller_versionfile import (  # pyright: ignore[reportMissingTypeStubs]
    create_versionfile,  # pyright: ignore[reportUnknownVariableType]
)
from tbc_video_export.common import consts

# use .99 as the 4th integer if non-final release
is_final = dunamai.Version.parse(consts.PROJECT_VERSION).stage == ""
version = (
    f"{dunamai.Version.parse(consts.PROJECT_VERSION).base}{'' if is_final else '.99'}"
)

print(f"Building Windows binary version {version}")

create_versionfile(
    output_file="build\\versionfile.txt",
    version=version,
    product_name="tbc-video-export",
    original_filename="tbc-video-export.exe",
    legal_copyright="Jitterbug",
    file_description=(
        "Cross platform tool for exporting S-Video & CVBS type TBC files "
        "to standard video files."
    ),
    company_name="JuniorIsAJitterbug",
)

PyInstaller.__main__.run(
    [
        "src\\tbc_video_export\\__main__.py",
        "--clean",
        "--collect-submodules",
        "application",
        "--icon",
        "assets\\icon.ico",
        "--version-file",
        "build\\versionfile.txt",
        "--onefile",
        "--name",
        "tbc-video-export",
    ]
)
