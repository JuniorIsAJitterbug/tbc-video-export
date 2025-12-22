from __future__ import annotations

import argparse
import logging
from typing import TYPE_CHECKING

from tbc_video_export.common import consts
from tbc_video_export.common.enums import (
    HardwareAccelType,
    VideoBitDepthType,
    VideoFormatType,
)
from tbc_video_export.common.utils import ansi
from tbc_video_export.config.config import GetProfileFilter

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from tbc_video_export.config import Config


class ActionDumpConfig(argparse.Action):
    """Dump configuraiton and exit action."""

    def __init__(self, config: Config, nargs: int = 0, **kwargs: Any) -> None:
        self._config = config
        super().__init__(nargs=nargs, **kwargs)

    def __call__(  # noqa: D102
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,  # noqa: ARG002
        values: str | Sequence[Any] | None,  # noqa: ARG002
        option_strings: str | None = None,  # noqa: ARG002
        *_: Any,
    ) -> None:
        self._config.dump_default_config(consts.EXPORT_CONFIG_FILE_NAME)
        parser.exit()


class ActionSetVerbosity(argparse.Action):
    """Set verbosity levels based on opts."""

    def __init__(self, nargs: int = 0, **kwargs: Any) -> None:
        super().__init__(nargs=nargs, **kwargs)

    def __call__(  # noqa: D102
        self,
        parser: argparse.ArgumentParser,  # noqa: ARG002
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,  # noqa: ARG002
        option_strings: str | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        if option_strings in ["--quiet", "-q"]:
            namespace.quiet = True
            namespace.no_progress = True
            namespace.show_process_output = False

        if option_strings in ["--debug", "-d"]:
            namespace.debug = True
            namespace.no_progress = True

        if option_strings in ["--show-process-output"]:
            namespace.show_process_output = True
            namespace.no_progress = True


class ActionListProfiles(argparse.Action):
    """Custom action for listing profiles.

    This exits the application after use.
    """

    def __init__(self, config: Config, nargs: int = 0, **kwargs: Any) -> None:
        self._config = config
        self._profile_names = config.get_profile_names()
        self._profiles_filters = config.filter_profiles
        super().__init__(nargs=nargs, **kwargs)

    def __call__(  # noqa: D102
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,  # noqa: ARG002
        values: str | Sequence[Any] | None,  # noqa: ARG002
        option_strings: str | None = None,  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        self._print_profiles()
        parser.exit()

    def _print_profiles(self) -> None:
        logging.getLogger("console").info(ansi.underlined("Profiles\n"))

        for profile_name in self._profile_names:
            profile = self._config.get_profile(GetProfileFilter(profile_name))

            # skip deprecated
            if profile.deprecated:
                continue

            video_profiles = self._config.get_video_profiles_for_profile(profile_name)

            data = (
                f"--{ansi.bold(profile.name)} "
                f"{'(default)' if profile.is_default else ''}\n"
            )

            for vp in video_profiles:
                data += f"{vp}\n"

            if profile.audio_profile is not None:
                data += str(profile.audio_profile)

            if profile.include_vbi:
                data += f"  {ansi.dim('Include VBI')}\t{profile.include_vbi}\n"

            logging.getLogger("console").info(data)


class ActionSetVideoHardwareAccelType(argparse.Action):
    """Set video format type with alias opts."""

    def __init__(self, nargs: int = 0, **kwargs: Any) -> None:
        super().__init__(nargs=nargs, **kwargs)

    def __call__(  # noqa: D102
        self,
        parser: argparse.ArgumentParser,  # noqa: ARG002
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,  # noqa: ARG002
        option_strings: str | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        # no need to check errors here, as option_strings can only be
        # VideoBitDepthType values
        namespace.hwaccel_type = HardwareAccelType(str(option_strings)[2:].lower())


class ActionSetVideoBitDepthType(argparse.Action):
    """Set video format type with alias opts."""

    def __init__(self, nargs: int = 0, **kwargs: Any) -> None:
        super().__init__(nargs=nargs, **kwargs)

    def __call__(  # noqa: D102
        self,
        parser: argparse.ArgumentParser,  # noqa: ARG002
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,  # noqa: ARG002
        option_strings: str | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        # no need to check errors here, as option_strings can only be
        # VideoBitDepthType values
        match VideoBitDepthType(str(option_strings)[2:].lower()):
            case VideoBitDepthType.BIT8:
                namespace.video_bitdepth = 8

            case VideoBitDepthType.BIT10:
                namespace.video_bitdepth = 10

            case VideoBitDepthType.BIT16:
                namespace.video_bitdepth = 16


class ActionSetVideoFormatType(argparse.Action):
    """Set video format type with alias opts."""

    def __init__(self, nargs: int = 0, **kwargs: Any) -> None:
        super().__init__(nargs=nargs, **kwargs)

    def __call__(  # noqa: D102
        self,
        parser: argparse.ArgumentParser,  # noqa: ARG002
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,  # noqa: ARG002
        option_strings: str | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        for format_type in VideoFormatType:
            if format_type.name.lower() == str(option_strings)[2:].lower():
                namespace.video_format = format_type


class ActionSetProfile(argparse.Action):
    """Set profile with alias opts."""

    def __init__(self, nargs: int = 0, **kwargs: Any) -> None:
        super().__init__(nargs=nargs, **kwargs)

    def __call__(  # noqa: D102
        self,
        parser: argparse.ArgumentParser,  # noqa: ARG002
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,  # noqa: ARG002
        option_strings: str | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        # no need to check errors here, as option_strings can only be
        # valid profile names
        namespace.profile = str(option_strings)[2:].lower()


class ActionSetAudioOverride(argparse.Action):
    """Set audio profile override type with alias opts."""

    def __init__(self, nargs: int = 0, **kwargs: Any) -> None:
        super().__init__(nargs=nargs, **kwargs)

    def __call__(  # noqa: D102
        self,
        parser: argparse.ArgumentParser,  # noqa: ARG002
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,  # noqa: ARG002
        option_strings: str | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        namespace.audio_profile = str(option_strings)[2:].lower()
