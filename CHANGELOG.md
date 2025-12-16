# Changelog

All notable changes to this project will be documented in this file.

The format is based on *Keep a Changelog*, and this project follows *Semantic Versioning*.

## [Unreleased]

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
