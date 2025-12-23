#!/usr/bin/env bash
set -euo pipefail

# Build the macOS .app using the existing PyInstaller spec.
# Run this on macOS (PyInstaller cannot cross-build macOS apps from Windows).

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

rm -rf dist build

python -m PyInstaller --noconfirm --clean "./colorFabb Filament Installer.spec"

APP_PATH="$(ls -1d ./dist/*.app | head -n 1 || true)"
if [[ -z "${APP_PATH}" ]]; then
  echo "ERROR: No .app produced in ./dist" >&2
  exit 1
fi

echo "Built: ${APP_PATH}"

echo "\nTo create a DMG:" 
cat <<'EOF'
  APP="dist/<YourApp>.app"
  STAGING="dist/dmg-staging"
  rm -rf "$STAGING"; mkdir -p "$STAGING"
  cp -R "$APP" "$STAGING/"
  ln -sf /Applications "$STAGING/Applications"
  hdiutil create -volname "colorFabb Filament Installer" -srcfolder "$STAGING" -ov -format UDZO "dist/<YourApp>.dmg"
EOF
