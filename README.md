# TBC-Video-Export

<img alt="tbc-video-export icon" src="assets/icon.ico" width=100>

---

Cross-platform tool for exporting S-Video and CVBS-type TBC files to standard video files created by the decode projects:

[VHS-Decode (Tape Decoding)](https://github.com/oyvindln/vhs-decode/wiki/) / [LaserDisc-Decode](https://github.com/happycube/ld-decode) / [CVBS-Decode (Composite Decoding)](CVBS-Composite-Decode) / [HiFi-Decode (FM Audio Decoding)](https://github.com/oyvindln/vhs-decode/wiki/hifi-decode)

To playback a 4FSC TBC file on physical playout systems, check:

[FL2K TBC Player](https://github.com/oyvindln/vhs-decode/wiki/TBC-To-Analogue)


# Installation

### Windows, Linux and macOS

You can find the latest self-contained binaries on the [releases](https://github.com/JuniorIsAJitterbug/tbc-video-export/releases) page.

### PyPI
```
pipx install tbc-video-export
```

# Basic Usage

### Windows
```
tbc-video-export.exe input.tbc
```

### Linux
```
tbc-video-export.AppImage input.tbc
```

### macOS
> [!TIP]
> You can add the application to your `PATH` by creating a symlink:  
> `ln -s /Applications/tbc-video-export.app/Contents/MacOS/tbc-video-export /usr/local/bin/tbc-video-export`.
```
tbc-video-export input.tbc
```
or (*without symlink*)
```
/Applications/tbc-video-export.app/Contents/MacOS/tbc-video-export input.tbc
```

### PyPI
> [!IMPORTANT]
> Use `pipx ensurepath` to add the application to your `PATH`. If you install via `pip` you need to do this manually.
```
tbc-video-export input.tbc
```

# Help 

- `--help` - List all available arguments.  
- `--list-profiles` - List all FFmpeg profiles.  
- `--profile` - Define FFmpeg profile.
- `--dump-default-config` - Dump the FFmpeg profiles config to `tbc-video-export.json`, allowing the creation and editing of profiles.

## Readout Terminal

### CVBS (Combined)

![tbc-video-export-readout-cvbs](https://github.com/JuniorIsAJitterbug/tbc-video-export/wiki/assets/gifs/Windows_Terminal_tbc-video-export_v0.1.0b2_Composite.gif)

### S-Video (Y + C)

![tbc-video-export-readout-s-video](https://github.com/JuniorIsAJitterbug/tbc-video-export/wiki/assets/gifs/Windows_Terminal_tbc-video-export_v0.1.0b2_S-Video.gif)


# Features

- FFmpeg Encoding Profiles
- Automatic CVBS/S-Video input detection
- Clear processing readout screen and logging
- Automated `ld-tool` interactions
- Checksums for Audio and Video streams
- Advanced audio input options
- ...


## Internal function


`input.tbc` + `[input_chroma.tbc]` + `input.json` ⟶ `ld-process-*` ⟶ `ld-chroma-decoder` ⟶ `YUV stream` ⟶ `FFmpeg` ⟶ `Output Video [w/audio and metadata]`


# Credits 

- [JuniorIsAJitterbug](https://github.com/JuniorIsAJitterbug/) - Development
- [Harry Munday](https://github.com/harrypm/) - Project Management (documentation, testing, direction, icon)

# Disclaimer

This is my first major Python project. If you have any comments, suggestions, or improvements, feel free to create an issue, do a pull request, or contact **Jitterbug** or **Harry** on the [Domesday86](https://discord.gg/pVVrrxd) discord.
