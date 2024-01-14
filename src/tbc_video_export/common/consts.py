from __future__ import annotations

import importlib.metadata
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final

_metadata = importlib.metadata.metadata("tbc-video-export")

APPLICATION_NAME: Final = _metadata["Name"]
PROJECT_VERSION: Final = _metadata["Version"]
PROJECT_SUMMARY: Final = _metadata["Summary"]
PROJECT_URL: Final = _metadata["Home-Page"]
PROJECT_URL_ISSUES: Final = next(
    (
        url.split(" ")[1]
        for url in _metadata.get_all("Project-URL")
        if str(url).startswith("Issues")
    ),
    "issues_url",
)

PROJECT_URL_DISCORD: Final = next(
    (
        url.split(" ")[1]
        for url in _metadata.get_all("Project-URL")
        if str(url).startswith("Discord")
    ),
    "discord_url",
)

CURRENT_TIMESTAMP: Final = datetime.now().strftime("%y-%m-%d_%H%M%S%f")[:-3]
EXPORT_CONFIG_FILE_NAME: Final = Path(f"{APPLICATION_NAME}.json")

PIPE_BUFFER_SIZE: Final = 4 * 1024 * 1024  # 4MB

MINIMUM_TERMINAL_HEIGHT: Final = 30
MINIMUM_TERMINAL_WIDTH: Final = 120

TWO_STEP_OUT_FILE_LUMA_SUFFIX: Final = "luma"

FFMPEG_VIDEO_MAP: Final = "[v_out]"


# Windows 10 conhost uses unicode-less fonts by default :'(
# SUCCESS_SYMBOL = "✓"
# ERROR_SYMBOL = "🗙"
# RUNNING_SYMBOLS: tuple[str, ...] = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")

SUCCESS_SYMBOL: Final = "●"
ERROR_SYMBOL: Final = "○"
RUNNING_SYMBOLS: Final[tuple[str, ...]] = ("/", "-", "\\", "|")

# for NT ANSI enabling
NT_STD_OUTPUT_HANDLE: Final = -11
NT_ENABLE_PROCESSED_OUTPUT: Final = 0x1
NT_ENABLE_WRAP_AT_EOL_OUTPUT: Final = 0x2
NT_ENABLE_VIRTUAL_TERMINAL_PROCESSING: Final = 0x4

# for NT named pipes
NT_NAMED_PIPE_MAX_INSTANCES: Final = 1
NT_NAMED_PIPE_TIMEOUT: Final = 0
NT_NAMED_PIPE_BUFFER_SIZE: Final = 65536

# for NT proc snapshots
NT_TH32CS_SNAPPROCESS: Final = 0x2
