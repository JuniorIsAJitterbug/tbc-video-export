# TBC-Video-Export

<img alt="tbc-video-export icon" src="assets/icon.ico" width=100>

---

Tool for exporting S-Video and CVBS-type TBCs to video files. ([VHS-Decode & CVBS-Decode](https://github.com/oyvindln/vhs-decode) / [LaserDisc-Decode](https://github.com/happycube/ld-decode))  

This is just a fancy wrapper for `tbc-tools` and `FFmpeg`.

# Installation

### Windows, Linux and macOS

You can find the latest binaries on the [releases](https://github.com/JuniorIsAJitterbug/tbc-video-export/releases) page.

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
- `--profile` - Select FFmpeg profile.
- `--dump-default-config` - Dump the FFmpeg profiles config to `tbc-video-export.json`, allowing the creation and editing of profiles.

## Readout Terminal

### CVBS (Combined)

![tbc-video-export-readout-cvbs](https://github.com/JuniorIsAJitterbug/tbc-video-export/wiki/assets/gifs/Windows_Terminal_tbc-video-export_v0.1.0b2_Composite.gif)

### S-Video (Y + C)

![tbc-video-export-readout-s-video](https://github.com/JuniorIsAJitterbug/tbc-video-export/wiki/assets/gifs/Windows_Terminal_tbc-video-export_v0.1.0b2_S-Video.gif)

# Credits 

- [JuniorIsAJitterbug](https://github.com/JuniorIsAJitterbug/) - Development
- [Harry Munday](https://github.com/harrypm/) - Documentation, testing, ideas and images

# Disclaimer

This is my first major Python project. If you have any comments, suggestions, or improvements, feel free to create an issue, do a pull request, or ask on the [Domesday86](https://discord.gg/pVVrrxd) discord.
