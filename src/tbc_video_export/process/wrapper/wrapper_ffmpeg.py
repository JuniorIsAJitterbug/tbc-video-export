from __future__ import annotations

import asyncio
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from tbc_video_export.common import consts, exceptions
from tbc_video_export.common.enums import (
    ExportMode,
    HardwareAccelType,
    PipeType,
    ProcessName,
    TBCType,
    VideoFormatType,
    VideoSystem,
)
from tbc_video_export.common.utils import FlatList, ansi
from tbc_video_export.process.wrapper.wrapper import Wrapper

if TYPE_CHECKING:
    from tbc_video_export.config.profile import Profile, ProfileVideo
    from tbc_video_export.process.wrapper.pipe import Pipe
    from tbc_video_export.process.wrapper.wrapper import WrapperConfig
    from tbc_video_export.program_state import ProgramState


class WrapperFFmpeg(Wrapper):
    """Wrapper for ffmpeg that generates commands for encoding."""

    def __init__(
        self, state: ProgramState, config: WrapperConfig[tuple[Pipe], None]
    ) -> None:
        self._additional_vopts: FlatList = FlatList()
        self._hwaccel_opts: FlatList = FlatList()
        self._hwaccel_filter: str = ""
        super().__init__(state, config)
        self._config = config
        self._parse_hwaccel()

    def post_fn(self) -> None:  # noqa: D102
        pass

    @property
    def command(self) -> FlatList:  # noqa: D102
        return FlatList(
            (
                self.binary,
                self._get_verbosity_opts(),
                self._get_overwrite_opt(),
                self._get_threads_opt(),
                "-nostdin",
                self._get_hwaccel_opts(),
                self._get_color_range_opt(),
                self._get_input_opts(),
                self._get_filter_complex_opts(),
                self._get_map_opts(),
                self._get_timecode_opt(),
                self._get_framerate_opt(),
                self._get_color_range_opt(),
                self._get_color_opts(),
                self._get_codec_opts(),
                self._get_metadata_opts(),
                self._get_output_opt(),
            )
        )

    def _get_verbosity_opts(self) -> FlatList:
        """Return opts for verbosity."""
        verbosity_opts = FlatList("-hide_banner")

        # enable progress reporting if we are not displaying output
        if not self._state.opts.show_process_output:
            verbosity_opts.append(
                (
                    "-loglevel",
                    "error",
                    "-progress",
                    "pipe:2",
                )
            )
        else:
            verbosity_opts.append(("-loglevel", "verbose"))

        return verbosity_opts

    def _get_overwrite_opt(self) -> FlatList | None:
        """Return opts for overwrite enabled."""
        return FlatList(self._state.opts.convert_opt("overwrite", "-y"))

    def _get_threads_opt(self) -> FlatList:
        """Return opts for thread count."""
        # TODO add complex filter threads?
        return FlatList(("-threads", str(self._state.opts.threads)))

    def _parse_hwaccel(self) -> None:
        """Parse hardware acceleration opts."""
        match self._get_profile().video_profile.hardware_accel:
            case HardwareAccelType.VAAPI:
                self._hwaccel_opts.append(
                    ("-hwaccel", "vaapi", "-hwaccel_output_format", "vaapi")
                )

                if (hwaccel_device := self._state.opts.hwaccel_device) is not None:
                    self._hwaccel_opts.append(("-vaapi_device", hwaccel_device))

                self._hwaccel_filter = "hwupload"

            case HardwareAccelType.NVENC:
                if (hwaccel_device := self._state.opts.hwaccel_device) is not None:
                    self._additional_vopts.append(("-gpu", hwaccel_device))

            case HardwareAccelType.QUICKSYNC:
                self._hwaccel_opts.append(
                    (
                        "-hwaccel",
                        "qsv",
                        "-hwaccel_output_format",
                        "qsv",
                    )
                )

                if (hwaccel_device := self._state.opts.hwaccel_device) is not None:
                    self._hwaccel_opts.append(("-qsv_device", hwaccel_device))

            case HardwareAccelType.AMF:
                if self._state.opts.hwaccel_device is not None:
                    raise exceptions.InvalidProfileError(
                        "Unable to set device for AMD AMF encoding due to FFmpeg "
                        "limitiations."
                    )

            case _:
                pass

    def _get_hwaccel_opts(self) -> FlatList:
        return self._hwaccel_opts

    @staticmethod
    def _get_color_range_opt() -> FlatList | None:
        """Return opts for color range."""
        return FlatList(("-color_range", "tv"))

    def _get_thread_queue_size_opt(self) -> FlatList:
        """Return opts for thread queue size."""
        return FlatList(("-thread_queue_size", str(self._state.opts.thread_queue_size)))

    def _get_input_opts(self) -> FlatList:
        """Return opts for all inputs."""
        return FlatList(
            (
                self._get_video_input_opts(),
                self._get_audio_input_opts(),
                self._get_metadata_input_opts(),
            )
        )

    def _get_video_input_opts(self) -> FlatList:
        """Return opts for video input."""
        input_opts = FlatList()

        if self._config.export_mode == ExportMode.LUMA_4FSC:
            input_opts.append(
                (
                    "-f",
                    "rawvideo",
                    "-pix_fmt",
                    "gray16le",
                    "-framerate",
                    self._get_framerate(),
                    "-video_size",
                )
            )

            match self._state.video_system:
                case VideoSystem.PAL:
                    input_opts.append("1135x626")

                case VideoSystem.NTSC:
                    input_opts.append("910x526")

                case VideoSystem.PAL_M:
                    input_opts.append("909x526")

        if self._is_two_step_merge_mode():
            # add the luma file as an input
            input_opts.append(
                (
                    self._get_thread_queue_size_opt(),
                    "-i",
                    self._state.file_helper.output_video_file_luma,
                )
            )

        # pipes
        input_opts.append(
            (self._get_thread_queue_size_opt(), "-i", str(i.in_path))
            for i in self._config.input_pipes
        )

        return input_opts

    def _get_audio_input_opts(self) -> FlatList:
        """Return opts for audio input."""
        input_opts = FlatList()

        # audio
        for track in self._state.opts.audio_track:
            if (offset := track.offset) is not None:
                input_opts.append(("-itsoffset", offset))

            if (sample_format := track.sample_format) is not None:
                input_opts.append(("-f", sample_format))

            if (rate := track.rate) is not None:
                input_opts.append(("-ar", rate))

            if (channels := track.channels) is not None:
                input_opts.append(("-ac", channels))

            input_opts.append(("-i", track.file_name))

            # if the track does not exist, we add a warning to the message log as
            # the file may be generated by ld-process-efm and will exist by the time
            # FFmpeg runs
            # we should perhaps only init a wrapper when it is time to run?
            if not Path(track.file_name).is_file():
                self._state.export.append_message(
                    ansi.error_color(
                        f"FFmpeg track {track.file_name} does not currently exist."
                    )
                )

        return input_opts

    def _get_metadata_input_opts(self) -> FlatList:
        """Return opts for metadata input."""
        input_opts = FlatList()
        if self._state.opts.export_metadata:
            # subtitles
            if self._state.opts.dry_run:
                input_opts.append(("{-i", "[SUBTITLE_FILE]}"))
            elif (cc_file := self._state.file_helper.cc_file).is_file():
                input_opts.append(("-i", cc_file))

            # metadata
            if self._state.opts.dry_run:
                input_opts.append(("{-i", "[METADATA_FILE]}"))
            elif (ffmetadata := self._state.file_helper.ffmetadata_file).is_file():
                input_opts.append(("-i", ffmetadata))

        for ffmetadata in self._state.opts.metadata_file:
            input_opts.append(("-i", ffmetadata))

        return input_opts

    def _get_vbi_crop_filter(self) -> str:
        """Return crop filter for full vertical to VBI crop."""
        match self._state.video_system:
            case VideoSystem.PAL:
                return "crop=iw:ih-12:0:9"

            case VideoSystem.NTSC | VideoSystem.PAL_M:
                return "crop=iw:ih-19:0:17"

    def _get_filters(self) -> tuple[list[str], list[str]]:
        """Return tuple containing video and other filters."""
        video_filters: list[str] = []
        other_filters: list[str] = []

        # add full vertical -> vbi crop
        if self._state.opts.vbi or self._get_profile().include_vbi:
            video_filters.append(self._get_vbi_crop_filter())

        _vf, _of = self._state.config.get_profile_filters(self._get_profile())

        # set video filters
        video_filters += _vf

        if self._state.opts.force_anamorphic or self._state.opts.letterbox:
            video_filters.append(self._get_widescreen_aspect_ratio_filter())

        # override profile colorlevels if set with opt
        if self._state.opts.force_black_level is not None:
            video_filters.append(
                "colorlevels="
                f"rimin={self._state.opts.force_black_level[0]}/255:"
                f"gimin={self._state.opts.force_black_level[1]}/255:"
                f"bimin={self._state.opts.force_black_level[2]}/255"
            )

        if self._state.opts.append_video_filter is not None:
            video_filters.append(self._state.opts.append_video_filter)

        video_filters.append(f"format={self._get_profile_video_format()}")

        if self._state.opts.hwaccel_type is not None and self._hwaccel_filter:
            video_filters.append(self._hwaccel_filter)

        # set other filters
        other_filters += _of

        if self._state.opts.append_other_filter is not None:
            other_filters.append(self._state.opts.append_other_filter)

        return video_filters, other_filters

    def _get_filter_complex_opts(self) -> FlatList:  # noqa: C901, PLR0912
        """Return opts for filter complex."""
        field_filter = f"setfield={self._get_field_order()}"
        video_filters, other_filters = self._get_filters()

        # add setfield to start of filters
        video_filters.insert(0, field_filter)

        video_filters_opts = ",".join(video_filters)

        other_filters_str = ",".join(other_filters)
        other_filters_opts = f",{other_filters_str}" if len(other_filters_str) else ""

        match self._config.export_mode:
            case ExportMode.CHROMA_MERGE:
                # merge Y/C from separate Y+C inputs

                # using mergeplanes 0x001112 with pipe+pipe input works but there
                # seems to be an issue when merging gray16le and 16-bit yuv(??) formats.
                # safer to extract the 2x inputs (file+pipe/pipe+pipe) into y/u/v planes
                # and merge to avoid any issues.

                mergeplanes = (
                    "0x001020"
                    if consts.FFMPEG_USE_OLD_MERGEPLANES
                    else "map1s=1:map2s=2"
                )

                complex_filter = (
                    f"[0:v]format=gray16le[luma];[1:v]format=yuv444p16le[chroma];"
                    f"[luma]extractplanes=y[y];[chroma]extractplanes=u+v[u][v];"
                    f"[y][u][v]mergeplanes={mergeplanes}:format=yuv444p16le,"
                    f"{video_filters_opts}[v_output]"
                    f"{other_filters_opts}"
                )

            case ExportMode.LUMA_EXTRACTED:
                # extract Y from a Y/C input
                complex_filter = (
                    f"[0:v]extractplanes=y,{video_filters_opts}"
                    f"[v_output]"
                    f"{other_filters_opts}"
                )

            case ExportMode.LUMA_4FSC:
                # interleve tbc fields
                complex_filter = (
                    f"[0:v]il=l=i:c=i,{video_filters_opts}"
                    f"[v_output]"
                    f"{other_filters_opts}"
                )

            case _ as mode if mode is ExportMode.LUMA and self._state.opts.two_step:
                # luma step in two-step should not use any filters (excluding setfield)
                complex_filter = f"[0:v]{field_filter}[v_output]"

            case _:
                complex_filter = (
                    f"[0:v]{video_filters_opts}[v_output]{other_filters_opts}"
                )

        return FlatList(("-filter_complex", complex_filter))

    def _get_map_opts(self) -> FlatList:
        """Return FFmpeg video map opts."""
        # video
        input_opts = FlatList(("-map", "[v_output]"))
        input_count = len(self._config.input_pipes)

        # audio
        input_opts.append(
            ("-map", f"{i + input_count}:a")
            for i in range(len(self._state.opts.audio_track))
        )
        input_count += len(self._state.opts.audio_track)

        if self._state.opts.export_metadata:
            # subtitles
            if self._state.opts.dry_run:
                input_opts.append(("{-map", "[SUBTITLE_INDEX]:s}"))
            elif self._state.file_helper.cc_file.is_file():
                input_opts.append(("-map", f"{input_count}:s"))
                input_count += 1

            # metadata
            if self._state.opts.dry_run:
                input_opts.append(("{-map_metadata", "[METADATA_INDEX]}"))
            elif self._state.file_helper.ffmetadata_file.is_file():
                input_opts.append(("-map_metadata", input_count))
                input_count += 1

        for _ in self._state.opts.metadata_file:
            input_opts.append(("-map_metadata", input_count))
            input_count += 1

        return input_opts

    def _get_timecode_opt(self) -> FlatList:
        """Return opts for timecode."""
        return FlatList(("-timecode", self._state.file_helper.tbc_json.timecode))

    def _get_framerate(self) -> str:
        """Return rate based on video system."""
        match self._state.video_system:
            case VideoSystem.PAL:
                return "pal"

            case VideoSystem.NTSC | VideoSystem.PAL_M:
                return "ntsc"

    def _get_framerate_opt(self) -> FlatList:
        """Return opts for rate."""
        return FlatList(
            (
                "-framerate",
                self._get_framerate(),
            )
        )

    def _get_widescreen_aspect_ratio_filter(self) -> str:
        """Return filter for widescreen aspect ratio."""
        match self._state.video_system:
            case VideoSystem.PAL:
                return "setsar=865/779:max=1000"

            case VideoSystem.NTSC | VideoSystem.PAL_M:
                return "setsar=25/22:max=1000"

    def _get_color_opts(self) -> FlatList | None:
        """Return opts for color settings."""
        match self._state.video_system:
            case VideoSystem.PAL | VideoSystem.PAL_M:
                return FlatList(
                    (
                        "-colorspace",
                        "bt470bg",
                        "-color_primaries",
                        "bt470bg",
                        "-color_trc",
                        "bt709",
                    ),
                )
            case VideoSystem.NTSC:
                return FlatList(
                    (
                        "-colorspace",
                        "smpte170m",
                        "-color_primaries",
                        "smpte170m",
                        "-color_trc",
                        "bt709",
                    ),
                )

    def _get_codec_opts(self) -> FlatList:
        """Return opts containing codecs for inputs."""
        codec_opts = FlatList(
            (
                "-c:v",
                self._get_profile().video_profile.codec,
                self._get_profile().video_profile.opts,
                self._additional_vopts,
            )
        )

        if (audio_profile := self._get_profile().audio_profile) is not None:
            codec_opts.append(
                (
                    "-c:a",
                    audio_profile.codec,
                    audio_profile.opts,
                )
            )

            if self._state.opts.export_metadata:
                if self._state.opts.dry_run:
                    codec_opts.append(("{-c:s", self._get_subtitle_format() + "}"))
                elif (
                    self._state.opts.export_metadata
                    and self._state.file_helper.cc_file.is_file()
                ):
                    codec_opts.append(("-c:s", self._get_subtitle_format()))

        return codec_opts

    def _get_metadata_opts(self) -> FlatList:
        """Return opts for metadata."""
        # custom metadata
        metadata_opts = FlatList(
            ("-metadata", f"{data[0]}={data[1]}") for data in self._state.opts.metadata
        )

        # audio
        for idx, track in enumerate(self._state.opts.audio_track):
            if (title := track.title) is not None:
                metadata_opts.append((f"-metadata:s:a:{idx}", f"title={title}"))

            if (language := track.language) is not None:
                metadata_opts.append((f"-metadata:s:a:{idx}", f"language={language}"))

            if (layout := track.layout) is not None:
                metadata_opts.append((f"-channel_layout:a:{idx}", f"{layout}"))

        # attachment
        if self._get_supports_attachments():
            metadata_opts.append(
                (
                    "-attach",
                    self._state.file_helper.tbc_json.file_name,
                    "-metadata:s:t:0",
                    "mimetype=application/json",
                )
            )

        return metadata_opts

    def _get_output_opt(self) -> FlatList:
        """Output opts for ffmpeg."""
        output_file = (
            self._state.file_helper.output_video_file_luma
            if self._is_two_step_luma_mode()
            else self._state.file_helper.output_video_file
        )

        # only set if the user has not manually specified a container
        output_format = (
            self._get_profile().video_profile.output_format
            if not self._state.opts.profile_container
            else None
        )

        if self._state.opts.checksum:
            checksum_output = (
                f"[f={output_format}]{output_file}"
                if output_format is not None
                else output_file
            )

            return FlatList(
                (
                    "-f",
                    "tee",
                    f"[f=streamhash]{output_file}.sha256|{checksum_output}",
                )
            )

        return (
            FlatList(("-f", output_format, output_file))
            if output_format is not None
            else FlatList(output_file)
        )

    def _get_profile(self) -> Profile:
        """Return the profile in state."""
        return self._state.profile

    def _get_video_profile(self) -> ProfileVideo:
        """Return the video profile in state."""
        return self._state.profile.video_profile

    def _get_profile_video_format(self) -> str:
        """Return the video format in state."""
        video_format = self._get_profile().video_profile.video_format

        # if two step, set to gray8/16le
        if self._is_two_step_luma_mode() or self._config.export_mode in (
            ExportMode.LUMA,
            ExportMode.LUMA_4FSC,
            ExportMode.LUMA_EXTRACTED,
        ):
            depth = (
                16
                if self._state.opts.video_bitdepth is None
                else self._state.opts.video_bitdepth
            )

            if (new_format := VideoFormatType.GRAY.value.get(depth)) is not None:
                video_format = new_format

        # check bitdepth override
        if (depth := self._state.opts.video_bitdepth) is not None and (
            new_format := VideoFormatType.get_new_format(video_format, depth)
        ) is not None:
            video_format = new_format

        # if override opts, ensure format for bitdepth and set
        # does not set the luma format when in two-step mode
        if (
            (vf := self._state.opts.video_format) is not None
            and (depth := self._state.opts.video_bitdepth) is not None
            and (new_format := vf.value.get(depth)) is not None
            and not self._is_two_step_luma_mode()
        ):
            video_format = new_format

        return video_format

    def _is_two_step_luma_mode(self) -> bool:
        """Return True if this wrapper is in luma mode while two-step is enabled."""
        return self._state.opts.two_step and self._config.export_mode is ExportMode.LUMA

    def _is_two_step_merge_mode(self) -> bool:
        """Return True if this wrapper is in merge mode while two-step is enabled."""
        return (
            self._state.opts.two_step
            and self._config.export_mode is ExportMode.CHROMA_MERGE
        )

    def _get_supports_attachments(self) -> bool:
        """Return True if attachments are supported by the profile container."""
        return self._state.file_helper.output_container.lower() == "mkv"

    def _get_subtitle_format(self) -> str:
        """Return subtitle format based on the profile container."""
        return (
            "srt"
            if self._state.file_helper.output_container.lower() != "mov"
            else "mov_text"
        )

    def _get_field_order(self) -> str:
        """Return the formatted field order from opts."""
        return self._state.opts.field_order.name.lower()

    @cached_property
    def process_name(self) -> ProcessName:  # noqa: D102
        return ProcessName.FFMPEG

    @cached_property
    def supported_pipe_types(self) -> PipeType:  # noqa: D102
        return PipeType.NULL | PipeType.OS | PipeType.NAMED

    @cached_property
    def stdin(self) -> int | None:  # noqa: D102
        # if ffmpeg has a pipe with a handle, use it
        # we usually use named pipes that do not have handles
        return next(
            (
                pipe.in_handle
                for pipe in self._config.input_pipes
                if pipe.in_handle is not None
            ),
            None,
        )

    @cached_property
    def stdout(self) -> int | None:  # noqa: D102
        # if ffmpeg has a pipe with a handle, use it
        # we usually do not have any out pipes
        return next(
            (
                pipe.in_handle
                for pipe in self._config.input_pipes
                if pipe.in_handle is not None
            ),
            None,
        )

    @cached_property
    def stderr(self) -> int | None:  # noqa: D102
        return asyncio.subprocess.PIPE

    @cached_property
    def log_output(self) -> bool:  # noqa: D102
        # we use built in FFmpeg logging via env
        return False

    @cached_property
    def log_stdout(self) -> bool:  # noqa: D102
        return False

    @cached_property
    def env(self) -> dict[str, str] | None:  # noqa: D102
        if self._state.opts.log_process_output:
            file_name = self._state.file_helper.get_log_file(
                self.process_name, TBCType.NONE
            )

            return {"FFREPORT": f"file='{file_name}'"}
        return None

    @cached_property
    def ignore_error(self) -> bool:  # noqa: D102
        return False

    @cached_property
    def stop_on_last_alive(self) -> bool:  # noqa: D102
        return False
