# tbc-video-export

Cross platform tool for exporting S-Video & CVBS type TBC files to standard video files created by the decode projects:

[VHS-Decoode (Tape Decoding)](https://github.com/oyvindln/vhs-decode/wiki/) / [LaserDisc-Decode](https://github.com/happycube/ld-decode) / [CVBS-Decode (Composite Decoding)](CVBS-Composite-Decode) / [HiFi-Decode (FM Audio Decoding)](https://github.com/oyvindln/vhs-decode/wiki/hifi-decode)

To playback an 4fsc TBC file to analogue playout systems have a look at:

[FL2K TBC Player](https://github.com/oyvindln/vhs-decode/wiki/TBC-To-Analogue)


# Basic Usage 

[Download Page](https://github.com/JuniorIsAJitterbug/tbc-video-export/tags)

Linux & MacOS:

    python3 tbc-video-export.py input.tbc

Windows 10 & 11:

    tbc-video-export.exe input.tbc

## Help 


`--help` - Lists command list

`--list-profiles` - Lists all FFmpeg profiles.

`--dump-default-config` - Will dump the FFmpeg profiles config to a `tbc-video-export.json` file, easy to edit for your own needs.


## Features


- FFmpeg Encoding Profiles
- Automtic CVBS or S-Video type `tbc` input detection
- Automated ld-tool interactions
- Advanced audio input options
- Many Many More (will expand later) 

## Internal function


`input.tbc`, `input_chroma.tbc` & `input.json` --> ld-process-* --> ld-chroma-decoder --> YUV stream --> FFmpeg Handling --> Video file with metadata & sound.


## Changelog & Development Notes

[This has a dedicated Wiki Page](https://github.com/JuniorIsAJitterbug/tbc-video-export/wiki/Changelog---Devlog)


## Credits 


- [JuniorIsAJitterbug](https://github.com/JuniorIsAJitterbug/) - Development & Implimentation
- [Harry Munday](https://github.com/harrypm/) - Development Direction, Testing, Application Icon


## Disclaimer


I don't usually write python. There are likely bugs and other terrible pieces of code that go against best practices.
If you have any comments, suggestions or improvements feel free to do a pull request or contact me `@jitterbug (videodump)` on the [Domesday86](https://discord.gg/pVVrrxd) discord.
