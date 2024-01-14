from __future__ import annotations

import logging
from dataclasses import dataclass

from tbc_video_export.common.enums import ProcessStatus


@dataclass
class ProcessState:
    """Process state class."""

    status = ProcessStatus.NONE
    returncode = -1
    status_index = -1

    def set_has_run(self) -> None:
        """Set the has run flag."""
        self.status |= ProcessStatus.HAS_RUN

    def set_running(self) -> None:
        """Set the running flag and removes the stopped flag."""
        self.status |= ProcessStatus.RUNNING
        self.status &= ~ProcessStatus.STOPPED

    def set_stopped(self) -> None:
        """Set the stopped flag and removes the running flag."""
        self.status |= ProcessStatus.STOPPED
        self.status &= ~ProcessStatus.RUNNING
        logging.getLogger("console").debug("Setting STOPPED")

    def set_success(self) -> None:
        """Set the success flag and removes the error flag."""
        self.status |= ProcessStatus.SUCCESS
        self.status &= ~ProcessStatus.ERROR
        logging.getLogger("console").debug("Setting SUCCESS")

    def set_error(self) -> None:
        """Set the error flag and removes the success flag."""
        self.status |= ProcessStatus.ERROR
        self.status &= ~ProcessStatus.SUCCESS
        logging.getLogger("console").debug("Setting ERROR")

    @property
    def has_run(self) -> bool:
        """Returns True if the process has run."""
        return ProcessStatus.HAS_RUN in self.status

    @property
    def is_successful(self) -> bool:
        """Returns True if the process is successful."""
        return ProcessStatus.SUCCESS in self.status

    @property
    def is_errored(self) -> bool:
        """Returns True if the process has errored.."""
        return ProcessStatus.ERROR in self.status

    @property
    def is_running(self) -> bool:
        """Returns True if the process is running."""
        return ProcessStatus.RUNNING in self.status

    @property
    def is_stopped(self) -> bool:
        """Returns True if the process is stopped."""
        return ProcessStatus.STOPPED in self.status
