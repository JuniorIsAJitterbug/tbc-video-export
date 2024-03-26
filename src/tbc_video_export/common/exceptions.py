from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tbc_video_export.common import consts
from tbc_video_export.common.utils import ansi

if TYPE_CHECKING:
    import asyncio
    from pathlib import Path
    from typing import Any


def _print_exception(e: BaseException) -> None:
    """Print formatted exception with exception name and message."""
    if len(message := getattr(e, "message", str(e))) > 1:
        logging.getLogger("console").exception(
            ansi.error_color(f"{e.__class__.__name__}: {message}"),
            exc_info=False,
        )


def handle_exceptions(e: BaseException | None):
    """Handle exceptions for the application.

    Provides formatted and custom error messages for exceptions.
    """
    match e:
        case (
            TBCError()
            | TBCTypeError()
            | FileIOError()
            | InvalidOptsError()
            | PipeError()
            | PipeNTError()
            | ProcessError()
        ):
            _print_exception(e)
        case InvalidProfileError():
            _print_exception(e)
            logging.getLogger("console").critical(f"\nError parsing {e.config_path}.")
            logging.getLogger("console").critical(
                "If you have upgraded this config file may not be compatible.\n"
                "Try moving or deleting the file and trying again."
            )
        case SampleRequiredError():
            logging.getLogger("console").critical(
                f"Unable to export file due to unsupported options: {e}\n"
                f"Please provide a capture sample via GitHub or Discord for this to be "
                f"fixed in future releases.\n\n"
                f"{consts.PROJECT_URL_ISSUES}\n{consts.PROJECT_URL_DISCORD}"
            )

        case KeyboardInterrupt():
            logging.getLogger("console").critical("User has cancelled the export.")

        case None:
            pass

        case _:
            _print_exception(e)


def loop_exception_handler(loop: asyncio.AbstractEventLoop, context: dict[str, Any]):  # noqa: ARG001
    """Loop exception handler."""
    handle_exceptions(context.get("exception"))


class TBCError(Exception):
    """TBC errors."""


class TBCTypeError(Exception):
    """TBC type errors."""


class FileIOError(Exception):
    """General file i/o errors."""


class SampleRequiredError(Exception):
    """Unsupported option due to lack of sample error."""


class InvalidProfileError(Exception):
    """General profile errors."""

    def __init__(self, message: str, config_path: Path | None = None) -> None:
        super().__init__(message)
        self.config_path = config_path if config_path is not None else "[internal]"


class InvalidFilterProfileError(Exception):
    """Filter profile errors."""


class InvalidOptsError(Exception):
    """Invalid program opts."""


class InvalidChromaDecoderError(Exception):
    """Chroma decoder errors."""


class PipeError(Exception):
    """General pipe errors."""


class PipeNTError(Exception):
    """NT-related pipe errors."""


class ProcessError(Exception):
    """General process errors."""
