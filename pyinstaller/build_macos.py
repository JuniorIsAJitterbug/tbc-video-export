from __future__ import annotations

import sys

if sys.platform != "darwin":
    raise SystemExit("Must be run on macOS")

import plistlib
from pathlib import Path

import dunamai
import PyInstaller.__main__
import PyInstaller.utils.osx as osxutils
from tbc_video_export.common import consts

version = dunamai.Version.parse(consts.PROJECT_VERSION).base

print(f"Building macOS binary version {version}")

PyInstaller.__main__.run(
    [
        "src/tbc_video_export/__main__.py",
        "--clean",
        "--collect-submodules",
        "application",
        "--icon",
        "assets/icon.icns",
        "--onefile",
        "--windowed",
        "--target-arch",
        "universal2",
        "--name",
        "tbc-video-export",
    ]
)

# set the version string
with Path("dist/tbc-video-export.app/Contents/Info.plist").open(mode="rb+") as file:
    plist = plistlib.load(file)

    plist["CFBundleShortVersionString"] = version
    file.seek(0)
    file.write(plistlib.dumps(plist))
    file.truncate()

# re-sign
osxutils.sign_binary("dist/tbc-video-export.app", deep=True)
