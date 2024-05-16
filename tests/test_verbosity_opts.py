from __future__ import annotations

import logging
from functools import partial
from pathlib import Path

import pytest
from tbc_video_export.common.file_helper import FileHelper
from tbc_video_export.common.utils import log
from tbc_video_export.config import Config as ProgramConfig
from tbc_video_export.opts import opts_parser


class TestVerbosityOpts:
    """Tests for ld-tools wrappers."""

    @pytest.fixture(autouse=True)
    def init(self) -> None:  # noqa: D102
        log.setup_logger("console")

        # set to INFO initially, opts will determine level
        logging.getLogger("console").setLevel(logging.INFO)

        self.path = Path.joinpath(Path(__file__).parent, "files", "pal_svideo")

        self.config = ProgramConfig()
        self.parse_opts = partial(opts_parser.parse_opts, self.config)

    @pytest.fixture
    def test_quiet_mode(self) -> None:  # noqa: D102
        _, opts = self.parse_opts([str(self.path), "pal_svideo", "-q"])
        self.files = FileHelper(opts, self.config)
        log.set_verbosity(opts)

        assert opts.quiet
        assert not opts.show_process_output
        assert opts.no_progress
        assert logging.getLogger("console").level == logging.ERROR

    def test_debug_mode(self) -> None:  # noqa: D102
        _, opts = self.parse_opts(
            [str(self.path), "pal_svideo", "-d", "--no-progress", "--no-debug-log"]
        )
        self.files = FileHelper(opts, self.config)
        log.set_verbosity(opts)

        assert opts.debug
        assert opts.no_progress
        assert logging.getLogger("console").level == logging.DEBUG

    def test_show_process_output(self) -> None:  # noqa: D102
        _, opts = self.parse_opts(
            [str(self.path), "pal_svideo", "--show-process-output"]
        )
        self.files = FileHelper(opts, self.config)
        log.set_verbosity(opts)

        assert opts.show_process_output
        assert opts.no_progress
