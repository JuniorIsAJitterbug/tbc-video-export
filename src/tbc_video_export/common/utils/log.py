from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tbc_video_export.common import consts
from tbc_video_export.common.utils import ansi

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from tbc_video_export.opts.opts import Opts


class ColorFormatter(logging.Formatter):
    """Formatter class for logging."""

    def format(self, record: logging.LogRecord):  # noqa: A003
        """Return colored formatter based on log level."""
        match record.levelno:
            case logging.DEBUG:
                formatter = logging.Formatter(ansi.dim_style("%(message)s"))

            case logging.INFO:
                formatter = logging.Formatter(ansi.default_color("%(message)s"))

            case logging.WARNING:
                formatter = logging.Formatter(ansi.default_color("%(message)s"))

            case logging.ERROR:
                formatter = logging.Formatter(ansi.error_color("%(message)s"))

            case logging.CRITICAL:
                formatter = logging.Formatter(ansi.error_color("%(message)s"))

            case _:
                formatter = logging.Formatter("%(message)s")

        return formatter.format(record)

    def formatException(self, ei: Any) -> str:  # noqa: N802
        """Return colored exception formatter."""
        return ansi.error_color(super().formatException(ei))


def setup_logger(
    name: str,
    enable_console: bool = True,
    filename: str | None = None,
    terminator: str = "\n",
) -> logging.Logger:
    """Set up logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if enable_console:
        add_console_handler(logger, terminator=terminator)

    if filename is not None:
        add_debug_file_handler(logger, filename)

    return logger


def add_debug_file_handler(logger: logging.Logger, filename: str | Path) -> None:
    """Add a file handler to a logger."""
    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(file_handler)


def add_console_handler(
    logger: logging.Logger, level: int = logging.DEBUG, terminator: str = "\n"
) -> None:
    """Add a console handler to a logger."""
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(ColorFormatter())
    console_handler.terminator = terminator
    logger.addHandler(console_handler)


def set_verbosity(opts: Opts) -> None:
    """Set verbosity and handlers based on opts."""
    if opts.quiet:
        logging.getLogger("console").setLevel(logging.ERROR)
        opts.no_progress = True
        opts.show_process_output = False
    elif opts.debug:
        # remove existing handlers and set base level
        logging.getLogger("console").handlers.clear()
        logging.getLogger("console").setLevel(logging.DEBUG)

        if opts.no_progress:
            # add new console handler with DEBUG level
            add_console_handler(logging.getLogger("console"))
        else:
            # re-add console handler with INFO level
            add_console_handler(logging.getLogger("console"), level=logging.INFO)

        if not opts.no_debug_log:
            add_debug_file_handler(
                logging.getLogger("console"),
                f"{consts.CURRENT_TIMESTAMP}_debug.log",
            )

    if opts.show_process_output:
        opts.no_progress = True
