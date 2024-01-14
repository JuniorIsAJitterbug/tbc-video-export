from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from tbc_video_export.common import consts

if TYPE_CHECKING:
    from types import TracebackType
    from typing import ClassVar

assert os.name == "nt"

import win32api  # noqa: E402
import win32con  # noqa: E402

GetLastError = cast(Callable[[], int], win32api.GetLastError)  # pyright: ignore [reportUnknownMemberType]

# stubs for nt fns
kernel32 = ctypes.windll.kernel32
CreateToolhelp32Snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot
Process32First = ctypes.windll.kernel32.Process32First
Process32Next = ctypes.windll.kernel32.Process32Next
CloseHandle = ctypes.windll.kernel32.CloseHandle
GetStdHandle = kernel32.GetStdHandle


class VirtualTerminal:
    """Context for enabling/disabling Virtual Terminal Processing on NT."""

    def __init__(self) -> None:
        self._original_console_mode: ctypes.wintypes.DWORD | None = None

    def __enter__(self) -> VirtualTerminal:
        """Enter Virtual Terminal context."""
        logging.getLogger("console").debug("Entering VirtualTerminal context")

        # store original config
        self._original_console_mode = _get_console_mode()

        # enables Virtual terminal Processing aka ANSI sequence support
        # this should work on all terminals unless Legacy Console mode is enabled
        if self._original_console_mode is not None:
            _set_console_mode(
                self._original_console_mode.value
                | consts.NT_ENABLE_VIRTUAL_TERMINAL_PROCESSING
            )

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit Virtual Terminal context."""
        logging.getLogger("console").debug("Leaving VirtualTerminal context")

        if self._original_console_mode is not None:
            _set_console_mode(self._original_console_mode)

        # Await user input if launched via explorer
        if _get_grandparent_name() == "explorer.exe":
            input("Press any key to exit.")


@staticmethod
def _get_grandparent_name() -> str | None:
    """Get name of grandparent process."""
    ppid = os.getppid()

    # get grandparent pid
    if (parent := _get_pid_data(ppid)) is not None and (
        gparent := _get_pid_data(parent.ppid)
    ) is not None:
        return gparent.exe_file
    return None


@staticmethod
def _get_pid_data(pid: int) -> _PidData | None:
    """Loops through procs and returns data for pid if found."""
    process_snapshot: ctypes.wintypes.HANDLE | None = None
    pe32 = _PROCESSENTRY32()
    pe32.dwSize = ctypes.sizeof(_PROCESSENTRY32)

    try:
        # create snapshot of procs
        process_snapshot = CreateToolhelp32Snapshot(consts.NT_TH32CS_SNAPPROCESS, 0)
        # get parent pid of parent
        if Process32First(process_snapshot, ctypes.byref(pe32)) == win32con.FALSE:
            logging.getLogger("console").debug(
                f"Process32First failed: {GetLastError()}"
            )
            return None

        # attempt to find pid in snapshot
        while Process32Next(process_snapshot, ctypes.byref(pe32)) != win32con.FALSE:
            if pe32.th32ProcessID == pid:
                return _PidData(
                    pe32.th32ProcessID,
                    pe32.th32ParentProcessID,
                    pe32.szExeFile.decode(),
                )

        logging.getLogger("console").debug(f"Process32Next failed: {GetLastError()}")
    finally:
        # return None
        if process_snapshot is not None:
            CloseHandle(process_snapshot)


@staticmethod
def _get_stdout_handle() -> int:
    """Return handle for STDOUT."""
    return GetStdHandle(consts.NT_STD_OUTPUT_HANDLE)


@staticmethod
def _set_console_mode(mode: int | ctypes.wintypes.DWORD) -> None:
    """Set the console mode."""
    if not kernel32.SetConsoleMode(_get_stdout_handle(), mode):
        logging.getLogger("console").debug(f"SetConsoleMode failed: {GetLastError()}")


@staticmethod
def _get_console_mode() -> ctypes.wintypes.DWORD | None:
    """Get the current console mode."""
    mode = ctypes.wintypes.DWORD()

    if not kernel32.GetConsoleMode(_get_stdout_handle(), ctypes.byref(mode)):
        logging.getLogger("console").debug(f"GetConsoleMode failed: {GetLastError()}")
        return None

    return mode


@dataclass
class _PidData:
    pid: int
    ppid: int
    exe_file: str


class _PROCESSENTRY32(ctypes.Structure):
    _fields_: ClassVar = [
        ("dwSize", ctypes.c_ulong),
        ("cntUsage", ctypes.c_ulong),
        ("th32ProcessID", ctypes.c_ulong),
        ("th32DefaultHeapID", ctypes.wintypes.LPARAM),
        ("th32ModuleID", ctypes.c_ulong),
        ("cntThreads", ctypes.c_ulong),
        ("th32ParentProcessID", ctypes.c_ulong),
        ("pcPriClassBase", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("szExeFile", ctypes.c_char * 260),
    ]
