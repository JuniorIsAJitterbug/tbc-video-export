from __future__ import annotations

import logging
import unittest
from functools import partial

from path import Path
from tbc_video_export.common.file_helper import FileHelper
from tbc_video_export.common.utils import log
from tbc_video_export.config import Config as ProgramConfig
from tbc_video_export.opts import opts_parser


class TestVerbosityOpts(unittest.TestCase):
    """Tests for ld-tools wrappers."""

    def setUp(self) -> None:  # noqa: D102
        log.setup_logger("console")

        # set to INFO initially, opts will determine level
        logging.getLogger("console").setLevel(logging.INFO)

        self.path = Path.joinpath(Path(__file__).parent, "files", "pal_svideo")

        self.config = ProgramConfig()
        self.parse_opts = partial(opts_parser.parse_opts, self.config)

    def test_quiet_mode(self) -> None:  # noqa: D102
        opts = self.parse_opts([self.path, "pal_svideo", "-q"])
        self.files = FileHelper(opts, self.config)
        log.set_verbosity(opts)

        self.assertEqual(opts.quiet, True)
        self.assertEqual(opts.show_process_output, False)
        self.assertEqual(opts.no_progress, True)
        self.assertEqual(logging.getLogger("console").level, logging.ERROR)

    def test_debug_mode(self) -> None:  # noqa: D102
        opts = self.parse_opts(
            [self.path, "pal_svideo", "-d", "--no-progress", "--no-debug-log"]
        )
        self.files = FileHelper(opts, self.config)
        log.set_verbosity(opts)

        self.assertEqual(opts.debug, True)
        self.assertEqual(opts.no_progress, True)
        self.assertEqual(logging.getLogger("console").level, logging.DEBUG)
        # self.assertGreater(len(logging.getLogger("console").handlers), 1)

    def test_show_process_output(self) -> None:  # noqa: D102
        opts = self.parse_opts([self.path, "pal_svideo", "--show-process-output"])
        self.files = FileHelper(opts, self.config)
        log.set_verbosity(opts)

        self.assertTrue(opts.show_process_output, True)
        self.assertTrue(opts.no_progress, True)
