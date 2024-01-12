from __future__ import annotations

import random
import string
from datetime import datetime

from tbc_video_export.common import consts
from tbc_video_export.common.utils import ansi


def random_characters(length: int) -> str:
    """Generate N random characters from ascii and digits."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def current_timestamp() -> str:
    """Return the current timestamp formatted."""
    return formatted_timestamp(datetime.now())


def formatted_timestamp(ts: datetime) -> str:
    """Return a timestamp formatted."""
    return ts.strftime("%H:%M:%S:%f")[:-3]


def application_header() -> str:
    """Return the application header containing the name and version."""
    return f"{ansi.bold(consts.APPLICATION_NAME)} {consts.PROJECT_VERSION}"
