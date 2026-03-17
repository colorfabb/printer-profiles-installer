
# colorFabb Filament Installer

This installer helps you download and install the **official colorFabb printer/slicer profiles** on your Windows PC.

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

## How to use (end users)

1. Download the latest installer from **GitHub Releases**.
	- Versioned file: `colorFabbInstaller_vX.Y.Z.exe`
	- Stable (direct link to latest): `colorFabbInstaller.exe`
2. Double-click to start.
3. Follow the steps in the window (select slicer(s) / location(s) if prompted).
4. Click **Install** on step 3. The installer will switch to step 4 and start copying immediately.
5. Wait until it shows “Done/Completed”.

Tip: if Windows warns (SmartScreen), verify the **SHA256** (and the digital signature if signing is enabled) on the release.

## Troubleshooting

- Download problems? Restart the installer and try again. Network/SSL blocking (proxy/AV) can prevent downloads.
- Want to only test download/unzip (without doing the GUI install)?

```powershell
colorFabbInstaller_vX.Y.Z.exe --check-download
```

## For developers

Build/release instructions are in `build.md`.
