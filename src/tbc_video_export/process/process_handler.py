from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack
from datetime import datetime
from functools import partial
from itertools import chain
from typing import TYPE_CHECKING

from tbc_video_export.common.enums import ExportMode, FlagHelper, ProcessName, TBCType
from tbc_video_export.common.utils import ansi, strings
from tbc_video_export.process.process import Process
from tbc_video_export.process.progress_handler import ProgressHandler
from tbc_video_export.process.wrapper import WrapperGroup

if TYPE_CHECKING:
    from typing import Any

    from tbc_video_export.process.process_state import ProcessState
    from tbc_video_export.program_state import ProgramState


class ProcessHandler:
    """Handles the creation and running of processes."""

    def __init__(self, state: ProgramState) -> None:
        self._state = state

        self._tasks: set[asyncio.Task[None]] = set()
        self._proc_tasks: set[asyncio.Task[ProcessState]] = set()
        self._procs: dict[WrapperGroup, list[Process]] = {}

        self._progress_handler: ProgressHandler | None = None

        self._start_time = datetime.now()
        self._has_run = False

        self._stop_event = asyncio.Event()
        self._user_cancellation_event = asyncio.Event()
        self._proc_error_event = asyncio.Event()

    async def run(self) -> None:
        """Start the procs."""
        self._create_wrapper_groups()

        if self._state.dry_run:
            self._print_wrappers()
            return

        await self._task_dispatcher()
        self._stop_event.set()

        await asyncio.gather(*self._tasks)

        while pending := [task for task in self._tasks if not task.done()]:
            await asyncio.wait(pending)

        if self._has_run:
            self._print_completion_message()

    async def stop(self, cancelled_by_user: bool = False) -> None:
        """Stop process handler.

        This will wait for tasks to finish.
        """
        logging.getLogger("console").debug("Stop called on Handler")

        await asyncio.wait(self._tasks)

        if cancelled_by_user:
            self._user_cancellation_event.set()

        self._stop_event.set()

    def _create_wrapper_groups(self) -> None:
        """Create wrappers and runs processes based off export mode."""
        procs: ProcessName = ProcessName.NONE
        export_mode = self._state.current_export_mode
        tbc_types = self._state.tbc_types

        create_group = partial(WrapperGroup, self._state)

        # group 1 (vbi)
        # run process vbi
        if self._state.opts.process_vbi:
            procs |= ProcessName.LD_PROCESS_VBI

            self._procs[create_group(export_mode, TBCType.NONE, procs)] = []

        procs = ProcessName.NONE

        # group 2 (standalone)
        # run export metadata & process efm
        if self._state.opts.export_metadata:
            procs |= ProcessName.LD_EXPORT_METADATA

        if self._state.opts.process_efm:
            procs |= ProcessName.LD_PROCESS_EFM

        if procs != ProcessName.NONE:
            self._procs[create_group(export_mode, TBCType.NONE, procs)] = []

        procs = ProcessName.NONE

        # group 3 (decoding/encoding)
        if export_mode != ExportMode.LUMA_4FSC:
            if not self._state.opts.no_dropout_correct:
                procs |= ProcessName.LD_DROPOUT_CORRECT

            procs |= ProcessName.LD_CHROMA_DECODER

        # we always want ffmpeg
        procs |= ProcessName.FFMPEG

        # check for luma only
        if export_mode == ExportMode.LUMA:
            # remove chroma if luma only
            tbc_types &= ~TBCType.CHROMA

        # two step enabled, create 2 separate groups for luma/chroma
        if self._state.opts.two_step and export_mode is ExportMode.CHROMA_MERGE:
            self._procs[create_group(ExportMode.LUMA, TBCType.LUMA, procs)] = []
            self._procs[create_group(export_mode, TBCType.CHROMA, procs)] = []
        else:
            self._procs[create_group(export_mode, tbc_types, procs)] = []

    async def _task_dispatcher(self) -> Any:
        """Create the tasks and pipes."""
        # check output location is valid
        self._state.file_helper.check_output_dir()
        self._state.file_helper.check_output_file()

        for group in self._procs:
            # add the procs to the groups
            self._procs[group] = [
                Process(self._state, self._stop_event, wrapper)
                for wrapper in group.wrappers
            ]

        # create progress handler task if enabled
        if not self._state.opts.no_progress:
            self._progress_handler = ProgressHandler(
                self._state, list(chain.from_iterable(self._procs.values()))
            )

            self._tasks.add(
                asyncio.create_task(self._progress_handler.print_progress_coroutine())
            )

        self._has_run = True
        await self._run_procs()

    async def _run_procs(self) -> None:
        """Run all procs.

        This will loop through process groups and run all of the procs in a group
        before moving to the next group.
        """
        for group, procs in self._procs.items():
            async with AsyncExitStack() as pipe_stack:
                # add required pipes to stack
                for pipe_group in group.consumable_pipes:
                    await pipe_stack.enter_async_context(pipe_group.pipe)

                self._state.current_export_mode = group.export_mode

                # start task killer for group
                self._tasks.add(asyncio.create_task(self._proc_killer(procs)))

                for proc in procs:
                    self._proc_tasks.add(asyncio.create_task(proc.run()))

                # check the return values of procs as they finish and ensure they
                # are valid
                for proc_state in asyncio.as_completed(self._proc_tasks):
                    if not (await proc_state).is_successful:
                        logging.getLogger("console").debug(
                            "Process not successful, exiting"
                        )

                        # process wants to exit
                        await self._exit_all()
                        return

    async def _proc_killer(self, procs: list[Process]) -> None:
        """Proc killing task.

        This watches proc states and kills if if the only remaining are flagged with
        stop_on_last_alive.

        Some procs (ld-dropout-correct) do not support certain arguments (-s/-l) will
        run until finished. This is solved on POSIX systems by closing the pipe once the
        consumer is finished, but this does not work on NT systems. This ensures they do
        not keep running.
        """
        while not self._proc_error_event.is_set() and not self._stop_event.is_set():
            await asyncio.sleep(0.1)

            running = [proc for proc in procs if proc.state.is_running]
            has_run_count = sum(1 for proc in procs if proc.state.has_run)

            if not len(running):
                break

            if not has_run_count:
                continue

            if has_run_count == len(procs) and all(
                proc.wrapper.stop_on_last_alive for proc in running
            ):
                for proc in running:
                    logging.getLogger("console").debug(
                        f"Killing {proc.wrapper.process_name}:{proc.wrapper.tbc_type} "
                        f"as all other procs have ended"
                    )
                    await proc.stop()

                break

    def _print_wrappers(self) -> None:
        """Print wrapper details."""
        for idx, group in enumerate(self._procs):
            logging.getLogger("console").info(ansi.dim(f"Step {idx + 1}"))

            for wrapper in group.wrappers:
                # create a string showing ENV items
                env_variables = (
                    "".join(f"{k}={v} " for k, v in wrapper.env.items())
                    if wrapper.env is not None
                    else ""
                )

                tbc_tbc_str = (
                    f"({FlagHelper.get_flags_str(wrapper.tbc_type, '+')})"
                    if wrapper.tbc_type is not TBCType.NONE
                    else ""
                )

                logging.getLogger("console").info(
                    ansi.dim(f"{wrapper.process_name} {tbc_tbc_str}\n")
                    + f"{env_variables}{wrapper.command}\n"
                )

                # proc the post-fn command to show changes on the output
                wrapper.post_fn()

    def _print_completion_message(self) -> None:
        """Print completion message based on success/failure."""
        message_suffix = (
            f" at {strings.current_timestamp()[:-4]} "
            f"after {str(datetime.now() - self._start_time)[:-3]}"
        )

        # add concealments if they were returned
        if (concealments := self._state.export.concealments) is not None:
            message_suffix += f" with {concealments} dropout concealments"

        if self._proc_error_event.is_set():
            logging.getLogger("console").error(f"Export failed{message_suffix}.")

            if self._user_cancellation_event.is_set():
                logging.getLogger("console").error("Export cancelled by user.")
        else:
            logging.getLogger("console").info(
                ansi.success_color(f"\nExport finished{message_suffix}.")
            )

    async def _exit_all(self) -> None:
        """Exit all running procs."""
        self._proc_error_event.set()

        # exit running procs
        for proc in chain.from_iterable(self._procs.values()):
            if proc.state.is_running:
                logging.getLogger("console").debug(
                    f"Stopping {proc.wrapper.process_name}"
                )

                await proc.stop()
