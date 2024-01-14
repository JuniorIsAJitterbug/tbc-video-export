from __future__ import annotations

import os

import dunamai

if os.name != "nt":
    raise SystemExit("Must be run on Windows")

import importlib.metadata

import PyInstaller.__main__
from pyinstaller_versionfile import (  # pyright: ignore[reportMissingTypeStubs]
    create_versionfile,  # pyright: ignore[reportUnknownVariableType]
)

full_ver = importlib.metadata.version("tbc-video-export")
is_final = dunamai.Version.parse(full_ver).stage == ""
version = f"{dunamai.Version.parse(full_ver).base}{'' if is_final else '.99'}"

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
