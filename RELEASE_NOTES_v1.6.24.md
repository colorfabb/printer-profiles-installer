# Release notes — v1.6.24

Date: 2026-04-24

## Added

- Ubuntu Linux support for the colorFabb installer.
- Linux slicer detection for native `~/.config/...` installs and supported Flatpak installs under `~/.var/app/.../config/...`.
- Linux release artifacts: native binary, AppImage, and SHA256 checksum files.

## Changed

- Linux slicer detection now shows slicer-specific paths in the UI.
- Linux packaging disables the PyInstaller splash screen dependency on tkinter/Tcl-Tk.