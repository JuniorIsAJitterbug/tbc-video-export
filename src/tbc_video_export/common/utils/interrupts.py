from __future__ import annotations

import asyncio
import signal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    from tbc_video_export.process.process_handler import ProcessHandler


class InterruptHandler:
    """Interrupt handler context.

    Creates a context that creates a signal handler and releases it on exit.
    """

    def __init__(
        self, process_handler: ProcessHandler, signal: signal.Signals = signal.SIGINT
    ):
        self._process_handler = process_handler
        self._signal = signal
        self._released = False

        self._tasks: set[asyncio.Task[Any]] = set()

    def __enter__(self):
        """Enter the interrupt context.

        This creates a signal handler while in the conext.
        """
        self._original_handler = signal.getsignal(self._signal)
        signal.signal(self._signal, self._signal_handler)

        return self

    def __exit__(self, *_: object):
        """Exit the interrupt context.

        This releases the signal handler.
        """
        self._release_signal()

    def _signal_handler(self, *_: Any) -> None:
        """Triggered on signal.

        Creates a task to stop the application and release the signal.
        """
        self._tasks.add(asyncio.create_task(self._process_handler.stop(True)))
        self._release_signal()

        asyncio.gather(*self._tasks)

    def _release_signal(self) -> None:
        """Set the signal to the original handler."""
        if self._released:
            return

        signal.signal(self._signal, self._original_handler)
        self._released = True
