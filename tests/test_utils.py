from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from unittest import mock

import pytest
from tbc_video_export.common.utils import ansi
from tbc_video_export.common.utils.flatlist import FlatList

if TYPE_CHECKING:
    from pytest import LogCaptureFixture


class TestUtils:
    """Tests for utils."""

    @pytest.fixture(autouse=True)
    def clear_cache(self) -> None:  # noqa: D102
        ansi.has_ansi_support.cache_clear()

    def test_ansi_support_posix(self) -> None:  # noqa: D102
        with (
            mock.patch("os.name", "posix"),
            mock.patch("os.isatty") as os_isatty,
        ):
            os_isatty.return_value = True
            assert ansi.has_ansi_support()

            ansi.has_ansi_support.cache_clear()

            os_isatty.return_value = False
            assert not ansi.has_ansi_support()

    def test_ansi_support_nt_11(self) -> None:  # noqa: D102
        with (
            mock.patch("os.name", "nt"),
            mock.patch("platform.release", mock.Mock(return_value="10")),
            mock.patch("platform.version", mock.Mock(return_value="10.0.22000")),
            mock.patch("os.isatty") as os_isatty,
        ):
            os_isatty.return_value = True
            assert ansi.has_ansi_support()

            ansi.has_ansi_support.cache_clear()

            os_isatty.return_value = False
            assert not ansi.has_ansi_support()

    def test_ansi_support_nt_10(self) -> None:  # noqa: D102
        with (
            mock.patch("os.name", "nt"),
            mock.patch("platform.release", mock.Mock(return_value="10")),
            mock.patch("platform.version", mock.Mock(return_value="10.0.14393")),
            mock.patch("os.isatty") as os_isatty,
        ):
            os_isatty.return_value = True
            assert ansi.has_ansi_support()

            ansi.has_ansi_support.cache_clear()

            os_isatty.return_value = False
            assert not ansi.has_ansi_support()

    def test_ansi_support_nt_10_old(self) -> None:  # noqa: D102
        with (
            mock.patch("os.name", "nt"),
            mock.patch("platform.release", mock.Mock(return_value="10")),
            mock.patch("platform.version", mock.Mock(return_value="10.0.14392")),
            mock.patch("os.isatty") as os_isatty,
        ):
            os_isatty.return_value = True
            assert not ansi.has_ansi_support()

            ansi.has_ansi_support.cache_clear()

            os_isatty.return_value = False
            assert not ansi.has_ansi_support()

    def test_terminal_buffer(self, caplog: LogCaptureFixture) -> None:  # noqa: D102
        with caplog.at_level(logging.INFO, logger="progress"):
            with ansi.create_terminal_buffer():
                assert caplog.record_tuples == [
                    ("progress", logging.INFO, "\x1b[?1049h\x1b[?25l")
                ]

                caplog.clear()

            assert caplog.record_tuples == [
                ("progress", logging.INFO, "\x1b[?1049l\x1b[?25h")
            ]

    def test_ansi_codes(self, force_ansi_support_on: None) -> None:  # noqa: D102, ARG002
        assert ansi.default_color("test") == "\x1b[38;5;255mtest\x1b[0;39m"
        assert ansi.error_color("test") == "\x1b[0;31mtest\x1b[0;39m"
        assert ansi.success_color("test") == "\x1b[0;32mtest\x1b[0;39m"
        assert ansi.progress_color("test") == "\x1b[0;36mtest\x1b[0;39m"
        assert ansi.dim("test") == "\x1b[38;5;245mtest\x1b[0;39m"

        assert ansi.bold("test") == "\x1b[1mtest\x1b[22m"
        assert ansi.italic("test") == "\x1b[23mtest\x1b[23m"
        assert ansi.dim_style("test") == "\x1b[2mtest\x1b[22m"
        assert ansi.underlined("test") == "\x1b[4mtest\x1b[24m"

        assert ansi.enable_alternative_buffer() == "\x1b[?1049h"
        assert ansi.disable_alternative_buffer() == "\x1b[?1049l"
        assert ansi.erase_from_cursor() == "\x1b[0J"
        assert ansi.erase_line() == "\x1b[0K"
        assert ansi.erase_screen() == "\x1b[2J"

        assert ansi.move_to_home() == "\x1b[H"
        assert ansi.go_up_lines(3) == "\x1b[3A"
        assert ansi.go_up_lines(9) == "\x1b[9A"
        assert ansi.show_cursor() == "\x1b[?25h"
        assert ansi.hide_cursor() == "\x1b[?25l"

    def test_ansi_off(self, force_ansi_support_off: None) -> None:  # noqa: D102, ARG002
        ansi.default_color.cache_clear()
        assert ansi.default_color("test") == "test"

    def test_flatlist(self) -> None:  # noqa :D102
        data = FlatList()

        assert not data

        data.append("1")
        data.append(["2", "3"])
        data.append(("4", "5"))
        data.append(d for d in ["6", "7"])
        data.append(FlatList(["8", "9"]))
        data.append([10, 11] + [12])

        assert str(data) == "1 2 3 4 5 6 7 8 9 10 11 12"
        assert data.data == [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "11",
            "12",
        ]

        assert data
