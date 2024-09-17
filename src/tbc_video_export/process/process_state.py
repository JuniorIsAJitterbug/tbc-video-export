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

    @property
    def has_run(self) -> bool:
        """Returns True if the process has run."""
        return ProcessStatus.HAS_RUN in self.status

    @has_run.setter
    def has_run(self, has_run: bool):
        if has_run:
            logging.getLogger("console").debug("Setting HAS_RUN")

            self.status |= ProcessStatus.HAS_RUN
            self.status &= ~ProcessStatus.NONE
        else:
            logging.getLogger("console").debug("Unsetting HAS_RUN")

            self.status &= ~(ProcessStatus.HAS_RUN | ProcessStatus.NONE)

    @property
    def running(self) -> bool:
        """Returns True if the process is running."""
        return ProcessStatus.RUNNING in self.status

    @running.setter
    def running(self, running: bool):
        """Set running state."""
        if running:
            logging.getLogger("console").debug("Setting RUNNING")

            self.status |= ProcessStatus.RUNNING
            self.status &= ~(ProcessStatus.ENDED | ProcessStatus.NONE)
            self.has_run = True
        else:
            logging.getLogger("console").debug("Unsetting RUNNING")

            self.status &= ~(ProcessStatus.RUNNING | ProcessStatus.NONE)

    @property
    def ended(self) -> bool:
        """Returns True if the process has ended."""
        return ProcessStatus.ENDED in self.status

    @ended.setter
    def ended(self, ended: bool):
        """Set the ended flag."""
        if ended:
            logging.getLogger("console").debug("Setting ENDED")

            self.status |= ProcessStatus.ENDED
            self.status &= ~(ProcessStatus.RUNNING | ProcessStatus.NONE)
            self.has_run = True
        else:
            logging.getLogger("console").debug("Unsetting ENDED")

            self.status &= ~(ProcessStatus.ENDED | ProcessStatus.NONE)

    @property
    def success(self) -> bool:
        """Returns True if the process is successful."""
        return ProcessStatus.SUCCESS in self.status

    @success.setter
    def success(self, success: bool):
        """Set the success flag and removes the error flag."""
        if success:
            logging.getLogger("console").debug("Setting SUCCESS")

            self.status |= ProcessStatus.SUCCESS
            self.status &= ~(ProcessStatus.ERROR | ProcessStatus.NONE)
        else:
            logging.getLogger("console").debug("Unsetting SUCCESS")

            self.status &= ~(ProcessStatus.SUCCESS | ProcessStatus.NONE)

    @property
    def errored(self) -> bool:
        """Returns True if the process has errored.."""
        return ProcessStatus.ERROR in self.status

    @errored.setter
    def errored(self, errored: bool):
        """Set the error flag and removes the success flag."""
        if errored:
            logging.getLogger("console").debug("Setting ERROR")

            self.status |= ProcessStatus.ERROR
            self.status &= ~(ProcessStatus.SUCCESS | ProcessStatus.NONE)
        else:
            logging.getLogger("console").debug("Unsetting ERROR")

            self.status &= ~(ProcessStatus.ERROR | ProcessStatus.NONE)
