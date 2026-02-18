from __future__ import annotations

import asyncio
import logging
import os
import sys
from contextlib import nullcontext

from tbc_video_export.common import FileHelper, exceptions
from tbc_video_export.common.utils import interrupts, log, strings
from tbc_video_export.config.config import Config
from tbc_video_export.opts import opt_validators, opts_parser
from tbc_video_export.process.process_handler import ProcessHandler
from tbc_video_export.program_state import ProgramState


def main(argv: list[str] = sys.argv[1:]) -> None:
    """Entry point for tbc-video-export."""
    asyncio.run(_run(argv))


async def _run(argv: list[str]) -> None:
    log.setup_logger("console")

    # set to INFO initially, opts will determine level
    logging.getLogger("console").setLevel(logging.INFO)

    asyncio.get_event_loop().set_exception_handler(exceptions.loop_exception_handler)

    try:
        pre_opts, args = opts_parser.parse_pre_opts(argv)
        config = Config(pre_opts.config_file)
        parser, opts = opts_parser.parse_opts(config, args, pre_opts)

        log.set_verbosity(opts)

        files = FileHelper(opts, config)
        state = ProgramState(
            opts,
            config,
            files,
        )

        opt_validators.validate_opts(state, parser, opts)

        handler = ProcessHandler(state)

        if os.name == "nt":
            from tbc_video_export.common.utils import win32

            terminal_ctx = win32.VirtualTerminal()
        else:
            terminal_ctx = nullcontext()

        with interrupts.InterruptHandler(handler), terminal_ctx:
            logging.getLogger("console").info(
                f"{strings.application_header()}\n\n{state}\n"
            )

            await handler.run()

            if not handler.completed_successfully:
                sys.exit(1)
    except Exception as e:  # noqa: BLE001
        exceptions.handle_exceptions(e)
    finally:
        logging.shutdown()


if __name__ == "__main__":
    main()
