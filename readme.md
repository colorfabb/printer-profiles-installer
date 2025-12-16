
# colorFabb Filament Installer

This installer helps you download and install the **official colorFabb printer/slicer profiles** on your Windows PC.

## What does this installer do?

- Downloads the latest profiles (ZIP) from GitHub.
- Validates that the download/ZIP is correct.
- Installs the profile files into the correct folder(s) for supported slicers.

## How to use (end users)

1. Download the latest `colorFabbInstaller_vX.Y.Z.exe` from **GitHub Releases**.
2. Double-click to start.
3. Follow the steps in the window (select slicer(s) / location(s) if prompted).
4. Click **Install** and wait until it shows “Done/Completed”.

Tip: if Windows warns (SmartScreen), verify the **SHA256** (and the digital signature if signing is enabled) on the release.

## Troubleshooting

- Download problems? Restart the installer and try again. Network/SSL blocking (proxy/AV) can prevent downloads.
- Want to only test download/unzip (without doing the GUI install)?

```powershell
colorFabbInstaller_vX.Y.Z.exe --check-download
```

## For developers

Build/release instructions are in `build.md`.
