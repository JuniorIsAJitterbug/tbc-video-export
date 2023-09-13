#!/usr/bin/env python3

# Script for exporting TBC files to video
# - JuniorIsAJitterbug

import argparse
import json
import os
import subprocess
import pathlib
from enum import Enum
from shutil import which


class VideoSystem(Enum):
    PAL = 'pal'
    NTSC = 'ntsc'

    def __str__(self):
        return self.value


class ChromaDecoder(Enum):
    PAL2D = 'pal2d'
    TRANSFORM2D = 'transform2d'
    TRANSFORM3D = 'transform3d'
    NTSC1D = 'ntsc1d'
    NTSC2D = 'ntsc2d'
    NTSC3D = 'ntsc3d'
    NTSC3DNOADAPT = 'ntsc3dnoadapt'

    def __str__(self):
        return self.value


class InputFiles:
    def __init__(self, file, input_json):
        self.name = pathlib.Path(file).stem
        self.tbc = self.name + '.tbc'
        self.tbc_chroma = self.name + '_chroma.tbc'

        if input_json is not None:
            self.tbc_json = input_json
        else:
            self.tbc_json = self.name + '.tbc.json'

        self.video_luma = None
        self.video = None

    def check_files_exist(self):
        files = [self.tbc, self.tbc_chroma, self.tbc_json]

        for file in files:
            if not os.path.isfile(file):
                raise Exception('missing required tbc file ' + file)


class DecoderSettings:
    def __init__(self, program_opts, video_system):
        self.program_opts = program_opts
        self.video_system = video_system

    def convert_opt(self, program_opts, program_opt_name, target_opt_name):
        """Converts a program opt to a subprocess opt."""
        rt = []
        value = getattr(program_opts, program_opt_name)

        if value is not None:
            if type(value) is bool:
                # only appends opt on true, fine for current use
                if value is True:
                    rt.append([target_opt_name])
            else:
                rt.append([target_opt_name, str(value)])

        return rt

    def get_opts(self):
        """Generate ld-chroma-decoder opts."""
        decoder_opts = []

        if self.video_system is VideoSystem.PAL:
            if self.program_opts.chroma_decoder is None:
                # chroma decoder unset, use transform2d
                decoder_opts.append(['-f', ChromaDecoder.TRANSFORM2D.value])

            # vbi is set, use preset line values
            if self.program_opts.vbi:
                decoder_opts.append(['--ffll', '2'])
                decoder_opts.append(['--lfll', '308'])
                decoder_opts.append(['--ffrl', '2'])
                decoder_opts.append(['--lfrl', '620'])
        elif self.video_system is VideoSystem.NTSC:
            if self.program_opts.chroma_decoder is None:
                # chroma decoder unset, use ntsc2d
                decoder_opts.append(['-f', ChromaDecoder.NTSC2D.value])

            decoder_opts.append(['--ntsc-phase-comp'])

            # vbi is set, use preset line values
            if self.program_opts.vbi:
                decoder_opts.append(['--ffll', '1'])
                decoder_opts.append(['--lfll', '259'])
                decoder_opts.append(['--ffrl', '2'])
                decoder_opts.append(['--lfrl', '525'])

        if self.program_opts.chroma_decoder is not None:
            decoder_opts.append(self.convert_opt(self.program_opts, 'chroma_decoder', '-f'))

        if not self.program_opts.vbi:
            decoder_opts.append(self.convert_opt(self.program_opts, 'ffll', '--ffll'))
            decoder_opts.append(self.convert_opt(self.program_opts, 'lfll', '--lfll'))
            decoder_opts.append(self.convert_opt(self.program_opts, 'ffrl', '--ffrl'))
            decoder_opts.append(self.convert_opt(self.program_opts, 'lfrl', '--lfrl'))

        decoder_opts.append(self.convert_opt(self.program_opts, 'start', '-s'))
        decoder_opts.append(self.convert_opt(self.program_opts, 'length', '-l'))
        decoder_opts.append(self.convert_opt(self.program_opts, 'reverse', '-r'))
        decoder_opts.append(self.convert_opt(self.program_opts, 'threads', '-t'))
        decoder_opts.append(self.convert_opt(self.program_opts, 'quiet', '-q'))
        decoder_opts.append(self.convert_opt(self.program_opts, 'pad', '--pad'))
        decoder_opts.append(self.convert_opt(self.program_opts, 'offset', '-o'))
        decoder_opts.append(self.convert_opt(self.program_opts, 'simple_pal', '--simple-pal'))
        decoder_opts.append(self.convert_opt(self.program_opts, 'show_ffts', '--show-ffts'))
        decoder_opts.append(self.convert_opt(self.program_opts, 'transform_threshold',
                            '--transform-threshold'))
        decoder_opts.append(self.convert_opt(self.program_opts, 'transform_thresholds',
                            '--transform-thresholds'))

        return decoder_opts

    def get_luma_opts(self):
        """Generate ld-chroma-decoder opts for luma."""
        decoder_opts = []
        decoder_opts.append(self.convert_opt(self.program_opts, 'luma_nr', '--luma-nr'))

        # ignore program opts for these
        decoder_opts.append(['--chroma-nr', '0'])
        decoder_opts.append(['--chroma-gain', '0'])
        decoder_opts.append(['--chroma-phase', '1'])

        return decoder_opts

    def get_chroma_opts(self):
        """Generate ld-chroma-decoder opts for luma."""
        decoder_opts = []

        # set default chroma gain if unset
        if self.program_opts.chroma_gain is None:
            if self.video_system is VideoSystem.PAL:
                decoder_opts.append(['--chroma-gain', '1.5'])
            elif self.video_system is VideoSystem.NTSC:
                decoder_opts.append(['--chroma-gain', '2.0'])
        else:
            decoder_opts.append(self.convert_opt(
                self.program_opts, 'chroma_gain', '--chroma-gain'))

        decoder_opts.append(self.convert_opt(self.program_opts, 'chroma_nr', '--chroma-nr'))
        decoder_opts.append(self.convert_opt(self.program_opts, 'chroma_phase', '--chroma-phase'))

        # ignore program opts for these
        decoder_opts.append(['--luma-nr', '0'])

        return decoder_opts


class FFmpegProfile:
    def __init__(self, profiles, name):
        self.name = name
        self.profile = profiles.profiles[name]

    def get_video_opts(self):
        """Return FFmpeg video opts from profile."""
        rt = []

        if not all(key in self.profile for key in ('v_codec', 'v_format', 'container')):
            raise Exception('profile is missing required data')

        rt.append(['-c:v', self.profile['v_codec']])

        if 'v_opts' in self.profile:
            rt.append(self.profile['v_opts'])

        rt.append(['-pixel_format', self.profile['v_format']])

        return rt

    def get_audio_opts(self):
        """Return FFmpeg audio opts from profile."""
        rt = []

        if 'a_codec' in self.profile:
            rt.append(['-c:a', self.profile['a_codec']])

        if 'a_opts' in self.profile:
            rt.append(self.profile['a_opts'])

        return rt

    def get_video_format(self):
        return self.profile['v_format']

    def get_container(self):
        return self.profile['container']


class FFmpegProfiles:
    def __init__(self, file_name):
        self.names = []
        self.names_luma = []
        self.profiles = []

        # profiles ending in _luma are considered luma profiles
        try:
            with open(file_name, 'r') as file:
                data = json.load(file)
                self.names = [name for name in data['ffmpeg_profiles'].keys() if '_luma' not in name]
                self.names_luma = [name for name in data['ffmpeg_profiles'].keys() if '_luma' in name]
                self.profiles = data['ffmpeg_profiles']
        except:
            raise Exception(file_name + ' is not a valid json file')

    def get_profile(self, name):
        return FFmpegProfile(self, name)


class FFmpegSettings:
    def __init__(self, program_opts, profile, profile_luma, tbc_json, video_system):
        self.program_opts = program_opts
        self.profile = profile
        self.profile_luma = profile_luma
        self.tbc_json = tbc_json
        self.video_system = video_system

    def get_rate_opt(self):
        """Returns FFmpeg opts for rate."""
        ffmpeg_opts = []

        if self.video_system == VideoSystem.PAL:
            ffmpeg_opts.append(['-r', '25'])
        elif self.video_system == VideoSystem.NTSC:
            ffmpeg_opts.append(['-r', '30'])

        return ffmpeg_opts

    def get_aspect_ratio_opt(self):
        """Returns FFmpeg opts for aspect ratio."""
        with open(self.tbc_json, 'r') as file:
            data = json.load(file)

        if (('isWidescreen' in data['videoParameters'] and data['videoParameters']['isWidescreen'])
                or self.program_opts.ffmpeg_force_animorphic):
            return ['-aspect', '16:9']

        return ['-aspect', '4:3']

    def get_color_opts(self):
        """Returns FFmpeg opts for color settings."""
        ffmpeg_opts = []

        if self.video_system == VideoSystem.PAL:
            ffmpeg_opts.append(['-colorspace', 'bt470bg'])
            ffmpeg_opts.append(['-color_primaries', 'bt470bg'])
            ffmpeg_opts.append(['-color_trc', 'gamma28'])
        elif self.video_system == VideoSystem.NTSC:
            ffmpeg_opts.append(['-colorspace', 'smpte170m'])
            ffmpeg_opts.append(['-color_primaries', 'smpte170m'])
            ffmpeg_opts.append(['-color_trc', 'smpte170m'])

        return ffmpeg_opts

    def get_audio_map_opts(self, video_inputs):
        """Returns FFmpeg opts for audio mapping."""
        ffmpeg_opts = []

        audio_inputs = self.program_opts.ffmpeg_audio_file

        if audio_inputs is not None:
            for idx, audio_input in enumerate(audio_inputs):
                ffmpeg_opts.append(['-map', str(idx + video_inputs) + ':a'])

        return ffmpeg_opts

    def get_metadata_opts(self):
        """Returns FFmpeg opts for metadata."""
        ffmpeg_opts = []

        metadata = self.program_opts.ffmpeg_metadata
        audio_titles = self.program_opts.ffmpeg_audio_title
        audio_languages = self.program_opts.ffmpeg_audio_language

        # add video metadata
        if metadata is not None:
            for data in metadata:
                ffmpeg_opts.append(['-metadata', data])

        # add audio metadata
        if audio_titles is not None:
            for idx, title in enumerate(audio_titles):
                ffmpeg_opts.append(['-metadata:s:a:' + str(idx), 'title=\"' + title + '\"'])

        if audio_languages is not None:
            for idx, language in enumerate(audio_languages):
                ffmpeg_opts.append(['-metadata:s:a:' + str(idx), 'language=\"' + language + '\"'])

        return ffmpeg_opts

    def get_audio_opts(self):
        """Returns FFmpeg opts for audio inputs."""
        ffmpeg_opts = []
        input_opts = []

        tracks = self.program_opts.ffmpeg_audio_file

        if tracks is not None:
            for idx, track in enumerate(tracks):
                input_opts.append(['-i', track])

            ffmpeg_opts.append(input_opts)
            ffmpeg_opts.append(self.profile.get_audio_opts())

        return ffmpeg_opts

    def get_overwrite_opt(self):
        if self.program_opts.ffmpeg_overwrite:
            return '-y'

    def get_color_range_opt(self):
        return ['-color_range', 'tv']

    def get_thread_queue_size_opt(self):
        return ['-thread_queue_size', str(self.program_opts.ffmpeg_thread_queue_size)]


class TBCVideoExport:
    def __init__(self):
        self.check_paths()
        self.ffmpeg_profiles = FFmpegProfiles(self.get_profile_file())
        self.program_opts = self.parse_opts(self.ffmpeg_profiles)

        self.files = InputFiles(self.program_opts.input, self.program_opts.input_json)
        self.files.check_files_exist()

        self.video_system = self.get_video_system(self.files.tbc_json)

        self.ffmpeg_profile = self.ffmpeg_profiles.get_profile(self.program_opts.ffmpeg_profile)
        self.ffmpeg_profile_luma = self.ffmpeg_profiles.get_profile(self.program_opts.ffmpeg_profile_luma)

        self.decoder_settings = DecoderSettings(self.program_opts, self.video_system)
        self.ffmpeg_settings = FFmpegSettings(self.program_opts, self.ffmpeg_profile,
                                              self.ffmpeg_profile_luma, self.files.tbc_json, self.video_system)

    def run(self):
        self.generate_luma(self.program_opts.blackandwhite)

        if self.program_opts.blackandwhite is not True:
            self.generate_chroma()

    def parse_opts(self, ffmpeg_profiles):
        parser = argparse.ArgumentParser(
            description='vhs-decode video generation script',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        global_opts = parser.add_argument_group('global')
        decoder_opts = parser.add_argument_group('decoder')
        ffmpeg_opts = parser.add_argument_group('ffmpeg')

        # general / global arguments
        global_opts.add_argument('input',
                                 help='Name of the input, without extension.',
                                 type=str)

        global_opts.add_argument('--what-if',
                                 help='Show what commands would be ran without running them.',
                                 action='store_true',
                                 default=False)

        global_opts.add_argument('-t', '--threads',
                                 help='Specify the number of concurrent threads.',
                                 type=int,
                                 default=os.cpu_count())

        global_opts.add_argument('-v', '--videosystem',
                                 help='Video system format.',
                                 type=VideoSystem,
                                 choices=list(VideoSystem),
                                 default=VideoSystem.PAL)

        # decoder arguments
        decoder_opts.add_argument('-s', '--start',
                                  help='Specify the start frame number.',
                                  type=int)

        decoder_opts.add_argument('-l', '--length',
                                  help='Specify the number of frames to process.',
                                  type=int)

        decoder_opts.add_argument('-r', '--reverse',
                                  help='Reverse the field order to second/first',
                                  action='store_true',
                                  default=False)

        decoder_opts.add_argument('-q', '--quiet',
                                  help='Suppress info and warning messages.',
                                  action='store_true',
                                  default=False)

        decoder_opts.add_argument('--input-json',
                                  help='Use a different .tbc.json file.',
                                  type=str)

        decoder_opts.add_argument('-b', '--blackandwhite',
                                  help='Only output a luma video.',
                                  action='store_true',
                                  default=False)

        decoder_opts.add_argument('--pad', '--output-padding',
                                  help='Pad the output frame to a multiple of this many pixels.',
                                  type=int)

        decoder_opts.add_argument('--vbi',
                                  help='Adjust FFLL/LFLL/FFRL/LFRL for full vertical export',
                                  action='store_true',
                                  default=False)

        decoder_opts.add_argument('--ffll', '--first_active_field_line',
                                  help='The first visible line of a field.'
                                  'Range 1-259 for NTSC (default: 20),'
                                  '      2-308 for PAL  (default: 22)',
                                  type=int)

        decoder_opts.add_argument('--lfll', '--last_active_field_line',
                                  help='The last visible line of a field.'
                                  'Range 1-259 for NTSC (default: 259),'
                                  '      2-308 for PAL  (default: 308)',
                                  type=int)

        decoder_opts.add_argument('--ffrl', '--first_active_frame_line',
                                  help='The first visible line of a field.'
                                  'Range 1-525 for NTSC (default: 40),'
                                  '      1-620 for PAL  (default: 44)',
                                  type=int)

        decoder_opts.add_argument('--lfrl', '--last_active_frame_line',
                                  help='The last visible line of a field.'
                                  'Range 1-525 for NTSC (default: 525),'
                                  '      1-620 for PAL  (default: 620)',
                                  type=int)

        decoder_opts.add_argument('-o', '--offset',
                                  help='NTSC: Overlay the adaptive filter map (only used for testing).',
                                  action='store_true',
                                  default=False)

        decoder_opts.add_argument('--chroma-decoder',
                                  help='Chroma decoder to use.',
                                  type=ChromaDecoder,
                                  choices=list(ChromaDecoder))

        decoder_opts.add_argument('--chroma-gain',
                                  help='Gain factor applied to chroma components (default 1.5 for PAL, 2.0 for NTSC).',
                                  type=float)

        decoder_opts.add_argument('--chroma-phase',
                                  help='Phase rotation applied to chroma components (degrees).',
                                  type=float,
                                  default=0.0)

        decoder_opts.add_argument('--chroma-nr',
                                  help='NTSC: Chroma noise reduction level in dB.',
                                  type=float,
                                  default=0.0)

        decoder_opts.add_argument('--luma-nr',
                                  help='Luma noise reduction level in dB.',
                                  type=float,
                                  default=1.0)

        decoder_opts.add_argument('--simple-pal',
                                  help='Transform: Use 1D UV filter',
                                  type=str)

        decoder_opts.add_argument('--transform-threshold',
                                  help='Transform: Uniform similarity threshold in \'threshold\' mode.',
                                  type=float,
                                  default=0.4)

        decoder_opts.add_argument('--transform-thresholds',
                                  help='Transform: File containing per-bin similarity thresholds in \'threshold\' mode.',
                                  type=str)

        decoder_opts.add_argument('--show-ffts',
                                  help='Transform: Overlay the input and output FFTs.',
                                  action='store_true',
                                  default=False)

        # ffmpeg arguments
        ffmpeg_opts.add_argument('--ffmpeg-profile',
                                 help='Specify an FFmpeg profile to use.',
                                 type=str,
                                 choices=ffmpeg_profiles.names,
                                 default=next(iter(ffmpeg_profiles.names)))

        ffmpeg_opts.add_argument('--ffmpeg-profile-luma',
                                 help='Specify an FFmpeg profile to use for luma.',
                                 type=str,
                                 choices=ffmpeg_profiles.names_luma,
                                 default=next(iter(ffmpeg_profiles.names_luma)))

        ffmpeg_opts.add_argument('--ffmpeg-metadata',
                                 help='Add metadata to file, eg. \'foo=\"bar\"\'.',
                                 type=str,
                                 action='append')

        ffmpeg_opts.add_argument('--ffmpeg-thread-queue-size',
                                 help='Sets the thread queue size for FFmpeg.',
                                 type=int,
                                 default=1024)

        ffmpeg_opts.add_argument('--ffmpeg-force-animorphic',
                                 help='Force widescreen aspect ratio.',
                                 action='store_true',
                                 default=False)

        ffmpeg_opts.add_argument('--ffmpeg-overwrite',
                                 help='Set to overwrite existing video files.',
                                 action='store_true',
                                 default=False)

        ffmpeg_opts.add_argument('--ffmpeg-audio-file',
                                 help='Audio file to mux with generated video.',
                                 type=str,
                                 action='append')

        ffmpeg_opts.add_argument('--ffmpeg-audio-title',
                                 help='Title of the audio track.',
                                 type=str,
                                 action='append')

        ffmpeg_opts.add_argument('--ffmpeg-audio-language',
                                 help='Language of the audio track.',
                                 type=str,
                                 action='append')

        return parser.parse_args()

    def flatten(self, A):
        """Flatten list of lists. Skips None values."""
        rt = []
        for i in A:
            if isinstance(i, list):
                rt.extend(self.flatten(i))
            elif i is not None:
                rt.append(i)
        return rt

    def run_cmds(self, dropout_correct_cmd, decoder_cmd, ffmpeg_cmd):
        """Run ld-dropout-correct, ld-chroma-decoder and ffmpeg."""
        dropout_correct = subprocess.Popen(self.flatten(dropout_correct_cmd), stdout=subprocess.PIPE)
        decoder = subprocess.Popen(self.flatten(decoder_cmd), stdin=dropout_correct.stdout, stdout=subprocess.PIPE)
        ffmpeg_chroma = subprocess.Popen(self.flatten(ffmpeg_cmd), stdin=decoder.stdout)

        ffmpeg_chroma.communicate()

    def generate_luma(self, add_audio):
        """Generate the luma file.
        This has to be a 2 step process as we're unable to easily use multiple pipes to ffmpeg."""

        file = self.files.name + '_luma.' + self.ffmpeg_settings.profile_luma.get_container()

        if os.path.isfile(file) and self.ffmpeg_settings.get_overwrite_opt() is None:
            raise Exception(file + ' exists, use --ffmpeg-overwrite or move them')

        dropout_correct_cmd = [
            'ld-dropout-correct',
            '-i',
            self.files.tbc,
            '--output-json',
            os.devnull,
            '-'
        ]

        decoder_cmd = [
            'ld-chroma-decoder',
            self.decoder_settings.get_luma_opts(),
            '-p',
            'y4m',
            self.decoder_settings.get_opts(),
            '--input-json',
            self.files.tbc_json,
            '-',
            '-'
        ]

        ffmpeg_cmd = [
            'ffmpeg',
            '-hide_banner',
            self.ffmpeg_settings.get_overwrite_opt(),
            self.ffmpeg_settings.get_thread_queue_size_opt(),
            '-i',
            '-'
        ]

        if add_audio:
            ffmpeg_cmd.append([
                self.ffmpeg_settings.get_audio_opts(),
                '-map',
                '0',
                self.ffmpeg_settings.get_audio_map_opts(1),
            ])

        ffmpeg_cmd.append([
            self.ffmpeg_settings.get_metadata_opts(),
            self.ffmpeg_settings.get_rate_opt(),
            self.ffmpeg_settings.profile_luma.get_video_opts(),
            '-pass',
            '1',
            file
        ])

        self.files.video_luma = file

        if self.program_opts.what_if:
            print('luma:')
            print(*self.flatten(dropout_correct_cmd))
            print(*self.flatten(decoder_cmd))
            print(*self.flatten(ffmpeg_cmd))
            print('---\n')

        else:
            self.run_cmds(dropout_correct_cmd, decoder_cmd, ffmpeg_cmd)

    def generate_chroma(self):
        """Generate the final video file."""
        file = self.files.name + '.' + self.ffmpeg_settings.profile.get_container()

        if os.path.isfile(file) and self.ffmpeg_settings.get_overwrite_opt() is None:
            raise Exception(file + ' exists, use --ffmpeg-overwrite or move them')

        dropout_correct_cmd = [
            'ld-dropout-correct',
            '-i',
            self.files.tbc_chroma,
            '--input-json',
            self.files.tbc_json,
            '--output-json',
            os.devnull,
            '-'
        ]

        decoder_cmd = [
            'ld-chroma-decoder',
            self.decoder_settings.get_chroma_opts(),
            '-p',
            'y4m',
            self.decoder_settings.get_opts(),
            '--input-json',
            self.files.tbc_json,
            '-',
            '-'
        ]

        ffmpeg_cmd = [
            'ffmpeg',
            '-hide_banner',
            self.ffmpeg_settings.get_overwrite_opt(),
            self.ffmpeg_settings.get_thread_queue_size_opt(),
            self.ffmpeg_settings.get_color_range_opt(),
            '-i',
            self.files.video_luma,
            self.ffmpeg_settings.get_thread_queue_size_opt(),
            '-i',
            '-',
            self.ffmpeg_settings.get_audio_opts(),
            self.ffmpeg_settings.get_audio_map_opts(2),
            self.ffmpeg_settings.get_metadata_opts(),
            '-filter_complex',
            '[0]format=pix_fmts=' + self.ffmpeg_settings.profile.get_video_format() +
            ',extractplanes=y[y];'
            '[1]format=pix_fmts=' + self.ffmpeg_settings.profile.get_video_format() +
            ',extractplanes=u+v[u][v];'
            '[y][u][v]mergeplanes=0x001020:' + self.ffmpeg_settings.profile.get_video_format() +
            ',format=pix_fmts=' + self.ffmpeg_settings.profile.get_video_format(),
            self.ffmpeg_settings.profile.get_video_opts(),
            self.ffmpeg_settings.get_rate_opt(),
            self.ffmpeg_settings.get_aspect_ratio_opt(),
            self.ffmpeg_settings.get_color_range_opt(),
            self.ffmpeg_settings.get_color_opts(),
            file
        ]

        self.files.video = file
        if self.program_opts.what_if:
            print('chroma:')
            print(*self.flatten(dropout_correct_cmd))
            print(*self.flatten(decoder_cmd))
            print(*self.flatten(ffmpeg_cmd))
            print('---\n')
        else:
            self.run_cmds(dropout_correct_cmd, decoder_cmd, ffmpeg_cmd)

    def get_video_system(self, json_file):
        """Determine whether a TBC is PAL or NTSC."""
        try:
            with open(json_file, 'r') as file:
                data = json.load(file)
        except:
            raise Exception(json_file + ' is not valid json file')

        # search for PAL* or NTSC* in videoParameters.system or the existence
        # if isSourcePal keys
        if (VideoSystem.PAL.value in data['videoParameters']['system'].lower()
            or 'isSourcePal' in data['videoParameters']
                or 'isSourcePalM' in data['videoParameters']):
            return VideoSystem.PAL
        elif VideoSystem.NTSC.value in data['videoParameters']['system'].lower():
            return VideoSystem.NTSC
        else:
            raise Exception('could not read video system from ' + json_file)

    def get_profile_file(self):
        """Returns name of json file to load profiles from. Checks for existence of
        a .custom file."""
        if os.path.isfile('tbc-video-export.custom.json'):
            return 'tbc-video-export.custom.json'

        return 'tbc-video-export.json'

    def check_paths(self):
        """Ensure required binaries are in PATH."""
        for tool in ['ld-dropout-correct', 'ld-chroma-decoder', 'ffmpeg']:
            if not which(tool):
                raise Exception(tool + ' not in PATH')


def main():
    tbc_video_export = TBCVideoExport()
    tbc_video_export.run()


if __name__ == '__main__':
    main()
