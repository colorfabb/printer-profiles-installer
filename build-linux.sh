#!/usr/bin/env bash
set -euo pipefail

# Build the Linux installer binary and AppImage using the existing PyInstaller spec.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

APP_VERSION="$(python3 ./_version_probe.py | tr -d '\r\n')"
if [[ -z "$APP_VERSION" || "$APP_VERSION" == "NOTFOUND" || "$APP_VERSION" == "NON_CONSTANT" ]]; then
  echo "ERROR: Unable to determine VERSION from main.py (got: '$APP_VERSION')" >&2
  exit 1
fi

APP_NAME="colorFabbInstaller_v${APP_VERSION}"
APP_ID="colorfabb-installer"
APPDIR_PATH="$ROOT_DIR/build/${APP_NAME}.AppDir"
APPIMAGE_PATH="$ROOT_DIR/dist/${APP_NAME}-x86_64.AppImage"
STABLE_APPIMAGE_PATH="$ROOT_DIR/dist/colorFabbInstaller-x86_64.AppImage"
STABLE_BIN_PATH="$ROOT_DIR/dist/colorFabbInstaller"
APPIMAGE_TOOL_PATH="${APPIMAGETOOL:-$ROOT_DIR/tools/appimagetool-x86_64.AppImage}"
APPIMAGE_TOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
APPIMAGE_RUNTIME_PATH="$ROOT_DIR/tools/runtime-x86_64"
APPIMAGE_SQUASHFS_PATH="$ROOT_DIR/build/${APP_NAME}.squashfs"

print_ubuntu_dependency_help() {
  echo "Missing Python environment tooling for the Linux build." >&2
  echo "On Ubuntu/Debian install the required packages with:" >&2
  echo "  sudo apt update" >&2
  echo "  sudo apt install -y python3-venv python3-pip" >&2
}

download_appimagetool() {
  mkdir -p "$(dirname "$APPIMAGE_TOOL_PATH")"
  if command -v curl >/dev/null 2>&1; then
    curl -L "$APPIMAGE_TOOL_URL" -o "$APPIMAGE_TOOL_PATH"
  elif command -v wget >/dev/null 2>&1; then
    wget -O "$APPIMAGE_TOOL_PATH" "$APPIMAGE_TOOL_URL"
  else
    echo "ERROR: Neither curl nor wget is available to download appimagetool." >&2
    exit 1
  fi
  chmod +x "$APPIMAGE_TOOL_PATH"
}

run_appimagetool() {
  local runtime_offset

  runtime_offset="$(grep -abo 'hsqs' "$APPIMAGE_TOOL_PATH" | tail -n 1 | cut -d: -f1)"
  if [[ -z "$runtime_offset" ]]; then
    echo "ERROR: Unable to locate squashfs payload inside $APPIMAGE_TOOL_PATH" >&2
    exit 1
  fi

  dd if="$APPIMAGE_TOOL_PATH" of="$APPIMAGE_RUNTIME_PATH" bs=1 count="$runtime_offset" status=none
  chmod +x "$APPIMAGE_RUNTIME_PATH"

  rm -f "$APPIMAGE_SQUASHFS_PATH"
  mksquashfs "$APPDIR_PATH" "$APPIMAGE_SQUASHFS_PATH" -root-owned -comp xz -noappend >/dev/null

  cat "$APPIMAGE_RUNTIME_PATH" "$APPIMAGE_SQUASHFS_PATH" > "$APPIMAGE_PATH"
}

create_python_env() {
  if [[ -x .venv/bin/python ]]; then
    return 0
  fi

  if python3 -m venv .venv >/dev/null 2>&1; then
    return 0
  fi

  echo "python3 -m venv is unavailable; falling back to virtualenv..."

  if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "ERROR: pip is not available for python3, so a fallback virtualenv cannot be created." >&2
    echo "Install python3-venv or python3-pip and try again." >&2
    print_ubuntu_dependency_help
    exit 1
  fi

  python3 -m pip install --user virtualenv
  python3 -m virtualenv .venv
}

preflight_checks() {
  if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 is required to build the Linux installer." >&2
    exit 1
  fi

  if ! python3 -m venv -h >/dev/null 2>&1 && ! python3 -m pip --version >/dev/null 2>&1; then
    print_ubuntu_dependency_help
    exit 1
  fi

  if ! command -v mksquashfs >/dev/null 2>&1; then
    echo "ERROR: mksquashfs is required to build the Linux AppImage." >&2
    echo "On Ubuntu/Debian install it with:" >&2
    echo "  sudo apt update" >&2
    echo "  sudo apt install -y squashfs-tools" >&2
    exit 1
  fi
}

write_appdir() {
  local source_bin="$1"
  local icon_src=""

  if [[ -f "$ROOT_DIR/Logo/cF_Logo.png" ]]; then
    icon_src="$ROOT_DIR/Logo/cF_Logo.png"
  elif [[ -f "$ROOT_DIR/logo/cF_Logo.png" ]]; then
    icon_src="$ROOT_DIR/logo/cF_Logo.png"
  else
    echo "ERROR: Could not find cF_Logo.png for AppImage packaging." >&2
    exit 1
  fi

  rm -rf "$APPDIR_PATH"
  mkdir -p "$APPDIR_PATH/usr/bin"
  mkdir -p "$APPDIR_PATH/usr/share/applications"
  mkdir -p "$APPDIR_PATH/usr/share/icons/hicolor/256x256/apps"

  cp "$source_bin" "$APPDIR_PATH/usr/bin/$APP_ID"
  chmod +x "$APPDIR_PATH/usr/bin/$APP_ID"

  cat > "$APPDIR_PATH/AppRun" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$HERE/usr/bin/colorfabb-installer" "$@"
EOF
  chmod +x "$APPDIR_PATH/AppRun"

  cat > "$APPDIR_PATH/${APP_ID}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=colorFabb Filament Installer
Comment=Install colorFabb slicer profiles
Exec=${APP_ID}
Icon=${APP_ID}
Categories=Utility;Graphics;
Terminal=false
StartupNotify=true
EOF

  cp "$APPDIR_PATH/${APP_ID}.desktop" "$APPDIR_PATH/usr/share/applications/${APP_ID}.desktop"
  cp "$icon_src" "$APPDIR_PATH/${APP_ID}.png"
  cp "$icon_src" "$APPDIR_PATH/.DirIcon"
  cp "$icon_src" "$APPDIR_PATH/usr/share/icons/hicolor/256x256/apps/${APP_ID}.png"
}

preflight_checks
create_python_env
# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

rm -rf dist build

python -m PyInstaller --noconfirm --clean "./colorFabb Filament Installer.spec"

BIN_PATH="$(find ./dist -maxdepth 1 -type f -name 'colorFabbInstaller_v*' | head -n 1 || true)"
if [[ -z "$BIN_PATH" ]]; then
  echo "ERROR: No Linux binary produced in ./dist" >&2
  exit 1
fi

SHA_PATH="${BIN_PATH}.sha256.txt"
sha256sum "$BIN_PATH" > "$SHA_PATH"

cp -f "$BIN_PATH" "$STABLE_BIN_PATH"
chmod +x "$STABLE_BIN_PATH"

STABLE_BIN_SHA_PATH="${STABLE_BIN_PATH}.sha256.txt"
sha256sum "$STABLE_BIN_PATH" > "$STABLE_BIN_SHA_PATH"

if [[ ! -x "$APPIMAGE_TOOL_PATH" ]]; then
  download_appimagetool
fi

write_appdir "$BIN_PATH"
run_appimagetool

if [[ ! -f "$APPIMAGE_PATH" ]]; then
  echo "ERROR: appimagetool completed without producing $APPIMAGE_PATH" >&2
  exit 1
fi

chmod +x "$APPIMAGE_PATH"

APPIMAGE_SHA_PATH="${APPIMAGE_PATH}.sha256.txt"
sha256sum "$APPIMAGE_PATH" > "$APPIMAGE_SHA_PATH"

cp -f "$APPIMAGE_PATH" "$STABLE_APPIMAGE_PATH"
STABLE_APPIMAGE_SHA_PATH="${STABLE_APPIMAGE_PATH}.sha256.txt"
sha256sum "$STABLE_APPIMAGE_PATH" > "$STABLE_APPIMAGE_SHA_PATH"

echo "Built: ${BIN_PATH}"
echo "SHA256: ${SHA_PATH}"
echo "Stable binary: ${STABLE_BIN_PATH}"
echo "Stable binary SHA256: ${STABLE_BIN_SHA_PATH}"
echo "AppImage: ${APPIMAGE_PATH}"
echo "AppImage SHA256: ${APPIMAGE_SHA_PATH}"
