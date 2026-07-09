from __future__ import annotations

import argparse
import logging
import sys
from typing import TYPE_CHECKING

from tbc_video_export.common import consts
from tbc_video_export.common.enums import (
    HardwareAccelType,
    ToolsetType,
    VideoBitDepthType,
    VideoFormatType,
)
from tbc_video_export.common.toolsets import toolsets
from tbc_video_export.common.utils import ansi
from tbc_video_export.config.config import GetProfileFilter

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from tbc_video_export.config import Config

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class ActionDumpConfig(argparse.Action):
    """Dump configuration and exit action."""

    def __init__(self, config: Config, nargs: int = 0, **kwargs: Any) -> None:
        self._config = config
        super().__init__(nargs=nargs, **kwargs)

    @override
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
        *_: Any,
    ) -> None:
        self._config.dump_default_config(consts.EXPORT_CONFIG_FILE_NAME)
        parser.exit()


class ActionSetVerbosity(argparse.Action):
    """Set verbosity levels based on opts."""

    def __init__(self, nargs: int = 0, **kwargs: Any) -> None:
        super().__init__(nargs=nargs, **kwargs)

    @override
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
        **kwargs: Any,
    ) -> None:
        if option_string in ["--quiet", "-q"]:
            namespace.quiet = True
            namespace.no_progress = True
            namespace.show_process_output = False

        if option_string in ["--debug", "-d"]:
            namespace.debug = True
            namespace.no_progress = True

        if option_string == "--show-process-output":
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

    @override
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
        **kwargs: Any,
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
                data += f"{profile.audio_profile!s}"

            if profile.include_vbi:
                data += f"  {ansi.dim('Include VBI')}\t{profile.include_vbi}\n"

            logging.getLogger("console").info(data)


class ActionSetVideoHardwareAccelType(argparse.Action):
    """Set video format type with alias opts."""

    def __init__(self, nargs: int = 0, **kwargs: Any) -> None:
        super().__init__(nargs=nargs, **kwargs)

    @override
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
        **kwargs: Any,
    ) -> None:
        # no need to check errors here, as option_string can only be
        # VideoBitDepthType values
        namespace.hwaccel_type = HardwareAccelType(str(option_string)[2:].lower())


class ActionSetVideoBitDepthType(argparse.Action):
    """Set video format type with alias opts."""

    def __init__(self, nargs: int = 0, **kwargs: Any) -> None:
        super().__init__(nargs=nargs, **kwargs)

    @override
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
        **kwargs: Any,
    ) -> None:
        # no need to check errors here, as option_string can only be
        # VideoBitDepthType values
        match VideoBitDepthType(str(option_string)[2:].lower()):
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

    @override
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
        **kwargs: Any,
    ) -> None:
        for format_type in VideoFormatType:
            if format_type.name.lower() == str(option_string)[2:].lower():
                namespace.video_format = format_type


class ActionSetProfile(argparse.Action):
    """Set profile with alias opts."""

    def __init__(self, nargs: int = 0, **kwargs: Any) -> None:
        super().__init__(nargs=nargs, **kwargs)

    @override
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
        **kwargs: Any,
    ) -> None:
        # no need to check errors here, as option_string can only be
        # valid profile names
        namespace.profile = str(option_string)[2:].lower()


class ActionSetAudioOverride(argparse.Action):
    """Set audio profile override type with alias opts."""

    def __init__(self, nargs: int = 0, **kwargs: Any) -> None:
        super().__init__(nargs=nargs, **kwargs)

    @override
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
        **kwargs: Any,
    ) -> None:
        namespace.audio_profile = str(option_string)[2:].lower()


class ActionListToolsets(argparse.Action):
    """Custom action for listing toolsets.

    This exits the application after use.
    """

    def __init__(self, nargs: int = 0, **kwargs: Any) -> None:
        super().__init__(nargs=nargs, **kwargs)

    @override
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
        **kwargs: Any,
    ) -> None:
        logger = logging.getLogger("console")
        out_string = ansi.underlined("Toolsets") + "\n\n"
        toolset_strings: list[str] = []

        for toolset_type in ToolsetType:
            details = toolsets[toolset_type]
            toolset_strings.append(
                ansi.bold(f"{toolset_type!s}{' (default)' if details.default else ''}")
                + "\n\n"
                + f"{ansi.dim('Metadata Types')}\n"
                + "\n".join(
                    f"{metadata_type!s}{' (default)' if metadata_type is details.default_metadata_type else ''}"  # noqa: E501
                    for metadata_type in details.metadata_types
                )
                + "\n\n"
                + f"{ansi.dim('Tools')}\n"
                + "\n".join(f"  {tool_name!s}" for tool_name in details.tools.values())
                + "\n"
            )

        out_string += "\n\n".join(toolset_strings)
        logger.info(out_string)
        parser.exit()
