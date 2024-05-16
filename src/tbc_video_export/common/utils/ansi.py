from __future__ import annotations

import logging
import os
import platform
from contextlib import contextmanager
from functools import cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any


@contextmanager
def create_terminal_buffer() -> Generator[None, Any, Any]:
    """Handle entering and exiting the alternative buffer."""
    try:
        # enter alternative buffer and hide cursor
        logging.getLogger("progress").info(
            f"{enable_alternative_buffer()}{hide_cursor()}"
        )

        yield
    finally:
        # exit alternative buffer and restore cursor
        logging.getLogger("progress").info(
            f"{disable_alternative_buffer()}{show_cursor()}"
        )


@cache
def has_ansi_support() -> bool:
    """Check for ANSI support in the terminal."""
    # logging.getLogger("console").debug("Activating ANSI support ")

    if os.name == "nt":
        # check if Windows >= 10.0.14393 for ansi console support.
        # This includes Windows 10 and Windows 11.
        return (
            platform.release() == "10"
            and platform.version() >= "10.0.14393"
            and os.isatty(0)
        )

    return os.isatty(0)


# style wrappers


@cache
def default_color(text: str) -> str:
    """Return text wrapped with the default color."""
    return f"{_default_color()}{text}{_reset_color()}"


@cache
def error_color(text: str) -> str:
    """Return text wrapped with error color."""
    return f"{_error_color()}{text}{_reset_color()}"


@cache
def success_color(text: str) -> str:
    """Return text wrapped with success color."""
    return f"{_success_color()}{text}{_reset_color()}"


@cache
def progress_color(text: str) -> str:
    """Return text wrapped with progress color."""
    return f"{_progress_color()}{text}{_reset_color()}"


@cache
def bold(text: str) -> str:
    """Return text wrapped with bold style."""
    return f"{_bold()}{text}{_reset_bold()}"


@cache
def italic(text: str) -> str:
    """Return text wrapped with italic style."""
    return f"{_italic()}{text}{_reset_italic()}"


@cache
def dim(text: str) -> str:
    """Return text wrapped with dim color."""
    return f"{_dim_color()}{text}{_reset_color()}"


@cache
def dim_style(text: str) -> str:
    """Return text wrapped with dim style."""
    return f"{_dim()}{text}{_reset_dim()}"


@cache
def underlined(text: str) -> str:
    """Return text wrapped with underlined style."""
    return f"{_underlined()}{text}{_reset_underlined()}"


# Erase Functions


@cache
def erase_from_cursor() -> str:
    """Return erase from cursor (to end of screen) escape code."""
    return "\x1B[0J"


@cache
def erase_line() -> str:
    """Return erase current line escape code."""
    return "\x1B[0K"


@cache
def erase_screen() -> str:
    """Return erase screen escape code."""
    return "\x1B[2J"


# Cursor Controls


@cache
def move_to_home() -> str:
    """Return move to home (0, 0) escape code."""
    return "\x1B[H"


@cache
def go_up_lines(count: int) -> str:
    """Return escape code to go up N lines."""
    return f"\x1B[{count}A"


# Screen Modes


@cache
def enable_alternative_buffer() -> str:
    """Return enable alternative buffer escape code."""
    return "\x1B[?1049h"


@cache
def disable_alternative_buffer() -> str:
    """Return disable alternative buffer escape code."""
    return "\x1B[?1049l"


@cache
def show_cursor() -> str:
    """Return show cursor escape code."""
    return "\x1B[?25h"


@cache
def hide_cursor() -> str:
    """Return hide cursor escape code."""
    return "\x1B[?25l"


# Color codes
def _default_color() -> str:
    """Return default color escape code."""
    return "\x1B[38;5;255m" if has_ansi_support() else ""  # white (255)


def _dim_color() -> str:
    """Return dim color escape code."""
    return "\x1B[38;5;245m" if has_ansi_support() else ""  # grey (240)


def _error_color() -> str:
    """Return error color escape code."""
    return "\x1B[0;31m" if has_ansi_support() else ""  # red


def _success_color() -> str:
    """Return success color escape code."""
    return "\x1B[0;32m" if has_ansi_support() else ""  # green


def _progress_color() -> str:
    """Return progress color escape code."""
    return "\x1B[0;36m" if has_ansi_support() else ""  # cyan


def _reset_color() -> str:
    """Return color reset escape code."""
    return "\x1B[0;39m" if has_ansi_support() else ""


# Colors / Graphics Mode


def _bold() -> str:
    """Return bold escape code."""
    return "\x1B[1m" if has_ansi_support() else ""


def _reset_bold() -> str:
    """Return end bold escape code."""
    return "\x1B[22m" if has_ansi_support() else ""


def _italic() -> str:
    """Return italic escape code."""
    return "\x1B[23m" if has_ansi_support() else ""


def _reset_italic() -> str:
    """Return end italic escape code."""
    return "\x1B[23m" if has_ansi_support() else ""


def _dim() -> str:
    """Return dim escape code."""
    return "\x1B[2m" if has_ansi_support() else ""


def _reset_dim() -> str:
    """Return end dim escape code."""
    return "\x1B[22m" if has_ansi_support() else ""


def _underlined() -> str:
    """Return underlined escape code."""
    return "\x1B[4m" if has_ansi_support() else ""


def _reset_underlined() -> str:
    """Return end underlined escape code."""
    return "\x1B[24m" if has_ansi_support() else ""
