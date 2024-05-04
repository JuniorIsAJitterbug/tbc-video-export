from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING

from tbc_video_export.common import consts
from tbc_video_export.common.enums import ProcessName
from tbc_video_export.common.utils import ansi, log, strings

if TYPE_CHECKING:
    from tbc_video_export.process.parser.parser import Parser
    from tbc_video_export.process.process import Process
    from tbc_video_export.process.process_state import ProcessState
    from tbc_video_export.program_state import ProgramState as ProgramState


class ProgressHandler:
    """Handle the progress output.

    This requires ANSI escape code support in the terminal.
    """

    def __init__(
        self,
        state: ProgramState,
        procs: list[Process],
    ) -> None:
        self._state = state
        self._procs = procs
        self._state_str = str(self._state)

        self._col_w: dict[str, int] = {
            "sender": 22,
            "status": 2,
            "proc_name": 19,
            "tbc_type": 11,
            "errors": 3,
            "fps": 4,
            "tracked_name": 6,
            "tracked_value": 7,
            "size": 7,
            "duration": 12,
            "bitrate": 16,
        }

        log.setup_logger("progress", terminator="")

    async def print_progress_coroutine(self, interval: float = 0.1) -> None:
        """Print current progress.

        This loops through the process handles at the set interval.
        """
        with ansi.create_terminal_buffer():
            while not all(proc.state.is_stopped for proc in self._procs):
                self._print_progress()
                await asyncio.sleep(interval)

        # final print without headers
        self._print_progress(True)

    def _print_progress(self, final_print: bool = False) -> None:
        """Print progress lines.

        This will include the program header and state information unless final_print
        is set.
        """
        # number of procs that are running
        max_line_length = os.get_terminal_size().columns
        output_line = ""

        if not final_print:
            # reset terminal
            output_line += f"{ansi.move_to_home()}{ansi.erase_screen()}"

            # add header + state
            output_line += f"{strings.application_header()}\n\n{self._state_str}\n\n"

        # get new progress lines
        output_line += "".join(f"{self._progress(proc)}\n" for proc in self._procs)

        # add log and file data
        output_line += (
            f"{self._get_last_messages_line(max_line_length)}"
            f"{self._get_output_file_line()}"
        )

        if not final_print:
            output_line += f"\n{self._get_exit_help_line()}"

        logging.getLogger("progress").info(output_line)

    def _get_output_file_line(self) -> str:
        """Return a string containing stats on the finale output file."""
        return (
            f"\n"
            f"{ansi.dim('Size:')} "
            f"{self._state.export.size:>{self._col_w['size']}.2f} GB\t"
            f"{ansi.dim('Duration:')} "
            f"{self._state.export.duration[:-3]:>{self._col_w['duration']}s}\t"
            f"{ansi.dim('Bitrate:')} "
            f"{self._state.export.bitrate:>{self._col_w['bitrate']}s}"
            f"\n"
        )

    def _get_last_messages_line(self, max_line_length: int) -> str:
        """Get the last N lines sent from the procs.

        The amount of lines returned is based on the terminal height. We assume a
        minimum height of at least 30 and increase/decrease the number of log lines
        based on that.
        """
        terminal_height = os.get_terminal_size().lines
        extra_lines = terminal_height - consts.MINIMUM_TERMINAL_HEIGHT
        max_message_lines = 5 + extra_lines

        if max_message_lines > 0:
            messages = self._state.export.messages[-max_message_lines:]

            fixed_log_lines: list[str] = []

            # get the last N log lines, padding out the list if they do not exist
            for message in messages + [None] * (max_message_lines - len(messages)):
                if message is not None:
                    sender = (
                        f"[{message.process}]"
                        if message.process is not ProcessName.NONE
                        else f"[{consts.APPLICATION_NAME}]"
                    )

                    formatted_line = (
                        f"[{strings.formatted_timestamp(message.timestamp)}] "
                        f"{sender:<{self._col_w['sender']}s}{message.message}"
                    )

                    fixed_log_lines.append(
                        f"{formatted_line[:max_line_length - 3]}...\n"
                        if len(formatted_line) > max_line_length
                        else f"{formatted_line}\n"
                    )

            return "\n" + "".join(fixed_log_lines) + "\n"
        return ""

    def _progress(self, process: Process) -> str:
        """Get formatted progress string."""
        return (
            (
                self._status_icon(process.state)
                + self._formatted_process(process)
                + self._formatted_current(process.output_parser)
                + self._formatted_errors(process.output_parser)
                + self._formatted_fps(process.output_parser)
            )
            if process.state.is_running
            or any((process.state.is_errored, process.state.is_successful))
            else self._status_icon(process.state)
            + ansi.dim(self._formatted_process(process))
        )

    def _status_icon(self, process_state: ProcessState) -> str:
        """Get the status icon for the process.

        If the process is not in a success or error state, this will cycle through the
        list of running symbols to create an animation.
        """
        process_state.status_index = (
            process_state.status_index + 1
            if process_state.status_index < len(consts.RUNNING_SYMBOLS) - 1
            else 0
        )

        match process_state:
            case _ as state if state.is_successful:
                return ansi.success_color(
                    f"{consts.SUCCESS_SYMBOL:<{self._col_w['status']}s}"
                )

            case _ as state if state.is_errored:
                return ansi.error_color(
                    f"{consts.ERROR_SYMBOL:<{self._col_w['status']}s}"
                )

            case _ as state if state.is_running:
                return ansi.progress_color(
                    f"{consts.RUNNING_SYMBOLS[process_state.status_index]:<{self._col_w['status']}s}"
                )

            case _:
                return f"{' ' * self._col_w['status']}"

    def _formatted_process(self, process: Process) -> str:
        """Get formatted processs string."""
        value = f"{process.wrapper.process_name:<{self._col_w['proc_name']}s}"

        value += (
            f"{f'({process.wrapper.tbc_type})':<{self._col_w['tbc_type']}s}"
            if not process.output_parser.hide_tbc_type
            else (" " * self._col_w["tbc_type"])
        ) + " "

        return value

    def _formatted_errors(self, output: Parser) -> str:
        """Get formatted error string."""
        return f"{ansi.dim('errors:')} {output.error_count:>{self._col_w['errors']}d}  "

    def _formatted_fps(self, output: Parser) -> str:
        """Get formatted fps string."""
        return (
            f"{ansi.dim('fps:')} {output.current_fps:>{self._col_w['fps']}.0f}  "
            if output.current_fps > 0.0
            else ""
        )

    def _formatted_current(self, output: Parser) -> str:
        """Get formatted current string."""
        if output.tracked_value_name:
            value = ansi.dim(
                f"{output.tracked_value_name:>{self._col_w['tracked_name']}s}:"
            )

            value += f"{output.tracked_value:>{self._col_w['tracked_value']}d}"

            value += (
                f"/{output.tracked_value_total:<{self._col_w['tracked_value']}d}"
                if output.tracked_value_total > 0
                else (" " * (self._col_w["tracked_value"] + 1))
            ) + "  "
        else:
            value = " " * (
                self._col_w["tracked_name"] + (self._col_w["tracked_value"] * 2) + 4
            )

        return value

    @staticmethod
    def _get_exit_help_line() -> str:
        """Return line explaining how to exit the encode."""
        return ansi.dim("Press Ctrl+C to cancel the export.")
