from __future__ import annotations

import argparse
import logging
from typing import TYPE_CHECKING

from tbc_video_export.common import consts
from tbc_video_export.common.enums import ProfileType
from tbc_video_export.common.utils import ansi

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from tbc_video_export.config import Config, SubProfile


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
        option_strings: str,  # noqa: ARG002
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
        option_strings: str,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        if option_strings in {"--quiet", "-q"}:
            namespace.quiet = True
            namespace.no_progress = True
            namespace.show_process_output = False

        if option_strings in ("--debug"):
            namespace.debug = True
            namespace.no_progress = True

        if option_strings in ("--show-process-output"):
            namespace.show_process_output = True
            namespace.no_progress = True


class ActionListProfiles(argparse.Action):
    """Custom action for listing profiles.

    This exits the application after use.
    """

    def __init__(self, config: Config, nargs: int = 0, **kwargs: Any) -> None:
        self._profiles = config.profiles
        self._profiles_filters = config.filter_profiles
        super().__init__(nargs=nargs, **kwargs)

    def __call__(  # noqa: D102
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,  # noqa: ARG002
        values: str | Sequence[Any] | None,  # noqa: ARG002
        option_strings: str,  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        logging.getLogger("console").info(ansi.underlined("Profiles\n"))

        for profile in self._profiles:
            sub_profiles: list[SubProfile] = [profile.video_profile]

            logging.getLogger("console").info(
                f"{profile.name}{' (default)' if profile.is_default else ''}"
            )

            if profile.profile_type is not ProfileType.DEFAULT:
                logging.getLogger("console").info(
                    f"  {ansi.dim('Profile Type:')} {profile.profile_type}"
                )

            output_format = (
                f" ({profile.video_profile.output_format})"
                if profile.video_profile.output_format is not None
                else ""
            )

            logging.getLogger("console").info(
                f"  {ansi.dim('Container:')}\t{profile.video_profile.container}"
                f"{output_format}\n"
                f"  {ansi.dim('Video Codec:')}\t{profile.video_profile.codec} "
                f"({profile.video_format})"
            )

            if video_opts := profile.video_profile.opts:
                logging.getLogger("console").info(
                    f"  {ansi.dim('Video Opts:')}\t{video_opts}"
                )

            if profile.audio_profile is not None:
                sub_profiles.append(profile.audio_profile)
                logging.getLogger("console").info(
                    f"  {ansi.dim('Audio Codec:')}\t{profile.audio_profile.codec}"
                )
                if profile.audio_profile.opts:
                    logging.getLogger("console").info(
                        f"  {ansi.dim('Audio Opts:')}\t{profile.audio_profile.opts}"
                    )

            if profile.include_vbi:
                logging.getLogger("console").info(
                    f"  {ansi.dim('Include VBI:')}\t{profile.include_vbi}"
                )

            if profile.filter_profiles:
                for _profile in profile.filter_profiles:
                    sub_profiles.append(_profile)
                    logging.getLogger("console").info(
                        f"  {ansi.dim('Filter:')}\t{_profile.video_filter}"
                    )

            logging.getLogger("console").info(
                f"  {ansi.dim('Sub Profiles:')}\t"
                f"{', '.join(profile.name for profile in sub_profiles)}"
            )

            logging.getLogger("console").info("")

        logging.getLogger("console").info(ansi.underlined("Filter Profiles\n"))

        for profile in self._profiles_filters:
            logging.getLogger("console").info(profile.name)

            logging.getLogger("console").info(
                f"  {ansi.dim('Description:')} {profile.description}"
            )

            profile_filter = (
                profile.video_filter
                if profile.video_filter is not None
                else profile.other_filter
            )

            logging.getLogger("console").info(
                f"  {ansi.dim('Filter:')} {profile_filter}"
            )

            logging.getLogger("console").info("")

        parser.exit()
