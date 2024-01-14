# tbc-video-export

Cross-platform tool for exporting S-Video & CVBS type TBC files to standard video files created by the decode projects:

[VHS-Decoode (Tape Decoding)](https://github.com/oyvindln/vhs-decode/wiki/) / [LaserDisc-Decode](https://github.com/happycube/ld-decode) / [CVBS-Decode (Composite Decoding)](CVBS-Composite-Decode) / [HiFi-Decode (FM Audio Decoding)](https://github.com/oyvindln/vhs-decode/wiki/hifi-decode)

To playback an 4fsc TBC file to physical playout systems have a look at:

[FL2K TBC Player](https://github.com/oyvindln/vhs-decode/wiki/TBC-To-Analogue)


## Installation


[Download Page](https://github.com/JuniorIsAJitterbug/tbc-video-export/releases) - Self-contained binaries.

Linux:

    pip tbc-video-export


# Basic Usage 


Linux & MacOS:

    tbc-video-export input.tbc

Windows 10 & 11:

    tbc-video-export.exe input.tbc


## Help 


`--help` - Lists command list

`--list-profiles` - Lists all FFmpeg profiles.

`--dump-default-config` - Will dump the FFmpeg profiles config to a `tbc-video-export.json` file, easy to edit for your own needs.


## Readout Terminal


CVBS (Combined)

![tbc-video-export-readout-cvbs](https://github.com/JuniorIsAJitterbug/tbc-video-export/wiki/assets/gifs/Windows_Terminal_tbc-video-export_v0.1.0_Composite.gif)

S-Video (Y + C)

![tbc-video-export-readout-s-video](https://github.com/JuniorIsAJitterbug/tbc-video-export/wiki/assets/gifs/Windows_Terminal_tbc-video-export_v0.1.0_S-Video.gif)


## Features


- FFmpeg Encoding Profiles
- Automtic CVBS or S-Video type `tbc` input detection
- Clear processing readout screen & logging
- Automated ld-tool interactions
- Checksums for Audio & Video streams
- Advanced audio input options
- Many Many More (will expand later) 

## Internal function


`input.tbc`, `input_chroma.tbc` & `input.json` --> ld-process-* --> ld-chroma-decoder --> YUV stream --> FFmpeg Handling --> Video file with metadata & sound.


## Changelog & Development Notes

[This has a dedicated Wiki Page](https://github.com/JuniorIsAJitterbug/tbc-video-export/wiki/Changelog-&-Devlog)


## Credits 


- [JuniorIsAJitterbug](https://github.com/JuniorIsAJitterbug/) - Development & Implementation
- [Harry Munday](https://github.com/harrypm/) - Development Direction, Testing, Icon


## Disclaimer


I don't usually write python. There are likely bugs and other terrible pieces of code that go against best practices.

If you have any comments, suggestions or improvements feel free to do a pull request or contact me `@jitterbug (videodump)` on the [Domesday86](https://discord.gg/pVVrrxd) discord.
