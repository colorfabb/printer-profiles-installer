
# colorFabb Filament Installer

This installer helps you download and install the **official colorFabb printer/slicer profiles** on Windows, macOS, and Ubuntu Linux.

## What does this installer do?

- Downloads the latest profiles (ZIP) from GitHub.
- Downloads profiles from: https://github.com/colorfabb/printer-profiles
- Validates that the download/ZIP is correct.
- Installs the profile files into the correct folder(s) for supported slicers.

Supported slicers:
- PrusaSlicer
- OrcaSlicer
- Bambu Studio
- Snapmaker Orca
- AnyCubicSlicer (AnycubicSlicerNext)
- QIDI Studio

On Windows, Bambu Studio profiles are copied into all detected per-account folders under `%APPDATA%\BambuStudio\user\<digits>\` (or `user\default` if no numeric folders exist), for both `filament` and `process`.

On Windows, AnyCubicSlicer profiles are copied into all detected per-account folders under `%APPDATA%\AnycubicSlicerNext\user\<digits>\` (or `user\default` if no numeric folders exist), for both `filament` and `process`.

On Windows, Snapmaker Orca profiles are copied into all detected per-account folders under `%APPDATA%\Snapmaker_Orca\user\<digits>\` (or `user\default` if no numeric folders exist), for both `filament` and `process`.

On Windows, QIDI Studio profiles are copied into all detected per-account folders under `%APPDATA%\QIDIStudio\user\<digits>\` (or `user\default` if no numeric folders exist), for both `filament` and `process`.

On Ubuntu/Linux, AppImage or native slicer installs use the standard `~/.config/...` config folders. For the slicers covered by Flatpak packages, the installer also targets the matching `~/.var/app/.../config/...` folders automatically:
- `com.bambulab.BambuStudio`
- `com.prusa3d.PrusaSlicer`
- `com.orcaslicer.OrcaSlicer`
- `com.anycubic.SlicerNext`

## How to use (end users)

1. Download the latest installer from **GitHub Releases**.
	- Versioned file: `colorFabbInstaller_vX.Y.Z.exe`
	- Stable (direct link to latest): `colorFabbInstaller.exe`
	- Ubuntu/Linux AppImage: `colorFabbInstaller-x86_64.AppImage`
	- Ubuntu/Linux native binary: `colorFabbInstaller`
2. Start the installer for your platform.
3. Follow the steps in the window (select slicer(s) / location(s) if prompted).
4. Click **Install** on step 3. The installer will switch to step 4 and start copying immediately.
5. Wait until it shows “Done/Completed”.

On Ubuntu, the recommended package is the AppImage release:

```bash
chmod +x ./colorFabbInstaller-x86_64.AppImage
./colorFabbInstaller-x86_64.AppImage
```

If the AppImage does not start on Ubuntu because of local FUSE or AppImageLauncher issues, use the native Linux binary instead:

```bash
chmod +x ./colorFabbInstaller
./colorFabbInstaller
```

Tip: if Windows warns (SmartScreen), verify the **SHA256** (and the digital signature if signing is enabled) on the release.

## Troubleshooting

- Download problems? Restart the installer and try again. Network/SSL blocking (proxy/AV) can prevent downloads.
- On Ubuntu, Flatpak slicers are detected from `~/.var/app/.../config/...` automatically. AppImage/native installs are detected from `~/.config/...`.
- Want to only test download/unzip (without doing the GUI install)?

```powershell
colorFabbInstaller_vX.Y.Z.exe --check-download
```

## For developers

Build/release instructions are in `build.md`.
