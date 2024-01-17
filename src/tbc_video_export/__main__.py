from __future__ import annotations

import asyncio
import logging
import os
from contextlib import nullcontext

from tbc_video_export.common import FileHelper, exceptions
from tbc_video_export.common.utils import interrupts, log, strings
from tbc_video_export.config.config import Config
from tbc_video_export.opts import opts_parser
from tbc_video_export.process.process_handler import ProcessHandler
from tbc_video_export.program_state import ProgramState


def main() -> None:
    """Entry point for tbc-video-export."""
    asyncio.run(_run())


async def _run() -> None:
    log.setup_logger("console")

    # set to INFO initially, opts will determine level
    logging.getLogger("console").setLevel(logging.INFO)

    asyncio.get_event_loop().set_exception_handler(exceptions.loop_exception_handler)

    try:
        config = Config()
        parser, opts = opts_parser.parse_opts(config)
        log.set_verbosity(opts)

        files = FileHelper(opts, config)
        state = ProgramState(
            opts,
            config,
            files,
        )

        opts_parser.validate_opts(state, parser, opts)

        handler = ProcessHandler(state)

        logging.getLogger("console").info(
            f"{strings.application_header()}\n\n{state}\n"
        )

        if os.name == "nt":
            from tbc_video_export.common.utils import win32

            terminal_ctx = win32.VirtualTerminal()
        else:
            terminal_ctx = nullcontext()

        with interrupts.InterruptHandler(handler), terminal_ctx:
            await handler.run()
    except Exception as e:  # noqa: BLE001
        exceptions.handle_exceptions(e)
    finally:
        logging.shutdown()


if __name__ == "__main__":
    main()
