# Changelog

All notable changes to this project will be documented in this file.

The format is based on *Keep a Changelog*, and this project follows *Semantic Versioning*.

## [Unreleased]

## [1.6.11] - 2025-12-18
### Changed
- BambuStudio: stricter account detection — only install/remove in numeric `%APPDATA%\\BambuStudio\\user\\<id>` folders; use `user\\default` only when no numeric folders exist.

## [1.6.10] - 2025-12-18
### Changed
- BambuStudio: if multiple per-account folders exist under `%APPDATA%\BambuStudio\user\<id>`, install/remove profiles in all detected folders (supports multiple active accounts).

## [1.6.9] - 2025-12-18
### Fixed
- BambuStudio: detect per-account numeric folder under `%APPDATA%\BambuStudio\user\<id>` and install profiles into the active folder instead of always using `user\default`.

## [1.6.8] - 2025-12-16
### Changed
- CI signing: releases no longer fail if the certificate chain is not trusted on the runner (still requires the EXE to be signed).

## [1.6.7] - 2025-12-16
### Fixed
- CI code signing: surface the actual `signtool` error output (and avoid ambiguous exit code 1).

## [1.6.6] - 2025-12-16
### Fixed
- GitHub Actions: harden code signing step (sanitize base64 secret and validate PFX/password) to prevent signing failures.

## [1.6.4] - 2025-12-16
### Fixed
- GitHub Actions: fixed workflow validation error so release builds can run again.

### Changed
- Docs: user README and build instructions are now English-only.

## [1.6.3] - 2025-12-16
### Fixed
- CI/GitHub Releases build: remove hard-coded local paths and venv dependency so the Windows build works on GitHub Actions.

## [1.6.2] - 2025-12-16
### Added
- `--check-download` CLI mode to validate HTTPS download + ZIP integrity/extraction without running the GUI.

### Changed
- UI: Step 4 install flow uses a single install action (no duplicate install button).
- UI: Bottom navigation buttons have consistent spacing/margins on all steps.

### Fixed
- Packaging: kept required SSL/OpenSSL runtime dependencies so HTTPS downloads work in the packaged EXE.
- UI: Step 4 crash after removing the duplicate install button.
