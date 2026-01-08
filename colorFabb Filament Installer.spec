# -*- mode: python ; coding: utf-8 -*-

import ast
import binascii
import os
import re
import sys
import struct
import zlib
from pathlib import Path

from PyInstaller.config import CONF
from PyInstaller.building.splash import Splash


SPEC_DIR = Path(globals().get('SPECPATH') or Path.cwd())


def _read_app_version() -> str:
    try:
        candidates = [SPEC_DIR / 'main.py', Path.cwd() / 'main.py']

        for main_py in candidates:
            if not main_py.is_file():
                continue

            text = main_py.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(text, filename=str(main_py))
            for node in tree.body:
                if not isinstance(node, ast.Assign):
                    continue
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'VERSION':
                        value = node.value
                        if isinstance(value, ast.Constant) and isinstance(value.value, str):
                            return value.value.strip()
    except Exception:
        pass
    return '0.0.0'


APP_VERSION = _read_app_version()
EXE_NAME = f'colorFabbInstaller_v{APP_VERSION}'

IS_WINDOWS = sys.platform.startswith('win')
IS_MACOS = sys.platform == 'darwin'


def _version_tuple(ver: str) -> tuple[int, int, int, int]:
    parts = [p for p in re.split(r'[^0-9]+', ver) if p]
    nums = [int(p) for p in parts[:3]]
    while len(nums) < 3:
        nums.append(0)
    return (nums[0], nums[1], nums[2], 0)


_fv = _version_tuple(APP_VERSION)
_pv = _fv

_version_file = None
if IS_WINDOWS:
    # Generate a Windows version resource file so Explorer shows File/Product version.
    _version_file = SPEC_DIR / '_pyinstaller_version_info.txt'
    _version_file.write_text(
            """# UTF-8
VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=%(filevers)s,
        prodvers=%(prodvers)s,
        mask=0x3f,
        flags=0x0,
        OS=0x4,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    '040904B0',
                    [
                        StringStruct('CompanyName', 'colorFabb B.V.'),
                        StringStruct('FileDescription', 'colorFabb Filament Installer'),
                        StringStruct('FileVersion', '%(ver)s'),
                        StringStruct('InternalName', '%(exe)s'),
                        StringStruct('LegalCopyright', '%(copyright)s'),
                        StringStruct('OriginalFilename', '%(exe)s.exe'),
                        StringStruct('ProductName', 'colorFabb Filament Installer'),
                        StringStruct('ProductVersion', '%(ver)s')
                    ]
                )
            ]
        ),
        VarFileInfo([VarStruct('Translation', [1033, 1200])])
    ]
)
"""
            % {
                    'filevers': repr(_fv),
                    'prodvers': repr(_pv),
                    'ver': APP_VERSION,
                    'exe': EXE_NAME,
                'copyright': 'Copyright (c) colorFabb B.V.',
            },
            encoding='utf-8',
    )

# Optional: point PyInstaller to UPX without needing it on PATH.
# Usage:  $env:UPX_DIR = 'C:\\Tools\\upx'
_upx_dir = os.environ.get('UPX_DIR')
if _upx_dir:
    CONF['upx_dir'] = _upx_dir


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[(
        str(
            (SPEC_DIR / 'Logo' / 'cF_Logo.png')
            if (SPEC_DIR / 'Logo' / 'cF_Logo.png').is_file()
            else (SPEC_DIR / 'logo' / 'cF_Logo.png')
        ),
        'logo',
    )],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # App uses only QtCore/QtGui/QtWidgets.
        # Excluding common addons avoids accidental pull-in via hooks.
        'PySide6.Qt3DAnimation',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DExtras',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DRender',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtNetworkAuth',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
        'PySide6.QtPositioning',
        'PySide6.QtQuick',
        'PySide6.QtQuickControls2',
        'PySide6.QtQml',
        'PySide6.QtRemoteObjects',
        'PySide6.QtScxml',
        'PySide6.QtSensors',
        'PySide6.QtSerialPort',
        'PySide6.QtSpatialAudio',
        'PySide6.QtSql',
        'PySide6.QtStateMachine',
        'PySide6.QtTextToSpeech',
        'PySide6.QtWebChannel',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebSockets',
        'PySide6.QtXml',
        'PySide6.QtXmlPatterns',
    ],
    noarchive=False,
    optimize=2,
)

# Reduce bundled Qt libraries/plugins. PyInstaller's PySide6 hooks often collect
# more than a simple Widgets app needs.
_remove_prefixes = (
    # Unused large Qt modules
    'PySide6\\Qt6Quick',
    'PySide6\\Qt6Qml',
    'PySide6\\Qt6Pdf',
    'PySide6\\Qt6Svg',
    'PySide6\\QtQuick',
    'PySide6\\QtQml',
    'PySide6\\QtPdf',
    'PySide6\\QtSvg',

    # QtNetwork + its payload (app uses urllib, not QtNetwork)
    'PySide6\\Qt6Network',
    'PySide6\\QtNetwork',
    'PySide6\\plugins\\tls\\',
    'PySide6\\plugins\\networkinformation\\',

    # IMPORTANT: do NOT exclude Python's OpenSSL DLLs (libssl-3.dll/libcrypto-3.dll).
    # Those are required for urllib HTTPS support in the packaged app.

    # Platforms we don't need on Windows
    'PySide6\\plugins\\platforms\\qminimal',
    'PySide6\\plugins\\platforms\\qoffscreen',

    # Optional input/generic plugins
    'PySide6\\plugins\\platforminputcontexts\\qtvirtualkeyboardplugin',
    'PySide6\\plugins\\generic\\qtuiotouchplugin',

    # Image formats not used by this app (logo is PNG).
    # Keep qpng/qico to be safe.
    'PySide6\\plugins\\imageformats\\qgif',
    'PySide6\\plugins\\imageformats\\qicns',
    'PySide6\\plugins\\imageformats\\qpdf',
    'PySide6\\plugins\\imageformats\\qsvg',
    'PySide6\\plugins\\imageformats\\qtga',
    'PySide6\\plugins\\imageformats\\qtiff',
    'PySide6\\plugins\\imageformats\\qwbmp',
    'PySide6\\plugins\\imageformats\\qwebp',
    # Optional: if you never load JPGs, you can exclude the jpeg plugin.
    # Enable by setting:  $env:CF_EXCLUDE_QJPEG = '1'
)

_remove_prefixes = list(_remove_prefixes)
if os.environ.get('CF_EXCLUDE_QJPEG') == '1':
    _remove_prefixes.append('PySide6\\plugins\\imageformats\\qjpeg')

# Optional (higher risk): exclude Qt's software OpenGL fallback.
# This can shrink the EXE further, but may break rendering on some systems (e.g. no GPU/remote).
# Enable by setting:  $env:CF_EXCLUDE_OPENGL_SW = '1'
if os.environ.get('CF_EXCLUDE_OPENGL_SW') == '1':
    _remove_prefixes.append('PySide6\\opengl32sw')

_remove_prefixes = tuple(_remove_prefixes)

def _keep_binary(entry):
    dest = entry[0]
    dest_norm = dest.replace('\\', '/')
    return not any(dest_norm.startswith(p.replace('\\', '/')) for p in _remove_prefixes)

a.binaries = [b for b in a.binaries if _keep_binary(b)]

# Bootloader splash screen (shows immediately during onefile startup/unpacking).
# Note: PyInstaller splash uses Tcl/Tk under the hood, which can increase bundle size,
# but it provides immediate user feedback on slow-starting onefile apps.
def _write_plain_png_splash(path: Path, *, width: int = 600, height: int = 240) -> None:
    # Keep within PyInstaller's default max splash size (760x480).
    # Plain white background; PyInstaller will render its default progress text/bar.
    def _chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack('>I', len(data))
            + tag
            + data
            + struct.pack('>I', binascii.crc32(tag + data) & 0xFFFFFFFF)
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    signature = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)  # 8-bit RGB

    # Build RGB pixel buffer so we can draw a simple label without Pillow.
    pixels = bytearray(b'\xFF' * (width * height * 3))  # white background

    FONT_5x7 = {
        'A': ["01110","10001","10001","11111","10001","10001","10001"],
        'D': ["11110","10001","10001","10001","10001","10001","11110"],
        'E': ["11111","10000","10000","11110","10000","10000","11111"],
        'G': ["01111","10000","10000","10111","10001","10001","01110"],
        'I': ["11111","00100","00100","00100","00100","00100","11111"],
        'L': ["10000","10000","10000","10000","10000","10000","11111"],
        'N': ["10001","11001","10101","10011","10001","10001","10001"],
        'O': ["01110","10001","10001","10001","10001","10001","01110"],
        'R': ["11110","10001","10001","11110","10100","10010","10001"],
        'S': ["01111","10000","10000","01110","00001","00001","11110"],
        'T': ["11111","00100","00100","00100","00100","00100","00100"],
        '.': ["00000","00000","00000","00000","00000","00100","00100"],
        ' ': ["00000","00000","00000","00000","00000","00000","00000"],
    }

    def _set_px(x: int, y: int, r: int, g: int, b: int) -> None:
        if 0 <= x < width and 0 <= y < height:
            idx = (y * width + x) * 3
            pixels[idx:idx+3] = bytes((r, g, b))

    def _draw_text(x0: int, y0: int, text: str, *, scale: int = 4) -> None:
        x = x0
        for ch in text:
            glyph = FONT_5x7.get(ch, FONT_5x7[' '])
            for gy, row_bits in enumerate(glyph):
                for gx, bit in enumerate(row_bits):
                    if bit == '1':
                        for sy in range(scale):
                            for sx in range(scale):
                                _set_px(x + gx * scale + sx, y0 + gy * scale + sy, 0, 0, 0)
            x += (5 + 1) * scale  # glyph width + spacing

    label = "LOADING INSTALLER..."
    scale = 4
    label_w = len(label) * (5 + 1) * scale
    label_h = 7 * scale
    start_x = max(0, (width - label_w) // 2)
    start_y = max(0, (height - label_h) // 2)
    _draw_text(start_x, start_y, label, scale=scale)

    # PNG scanlines: each row is prefixed with filter byte 0 (None)
    raw_rows = []
    for y in range(height):
        raw_rows.append(b'\x00' + bytes(pixels[y * width * 3:(y + 1) * width * 3]))
    raw = b''.join(raw_rows)
    idat = zlib.compress(raw, level=9)

    png = signature + _chunk(b'IHDR', ihdr) + _chunk(b'IDAT', idat) + _chunk(b'IEND', b'')
    path.write_bytes(png)

_splash_candidates = [
    # Preferred: provide a dedicated small splash asset if desired.
    SPEC_DIR / 'Logo' / 'splash.png',
    SPEC_DIR / 'logo' / 'splash.png',
]

_splash_image = next((p for p in _splash_candidates if p.is_file()), None)
if _splash_image is None:
    _splash_image = SPEC_DIR / 'build' / '_cf_splash.png'
    _write_plain_png_splash(_splash_image)

# NOTE: PyInstaller splash is not supported on macOS.
splash = None
if not IS_MACOS and _splash_image is not None:
    splash = Splash(
        str(_splash_image),
        binaries=a.binaries,
        datas=a.datas,
        # Do NOT enable text support; otherwise the bootloader shows extraction filenames.
    )

pyz = PYZ(a.pure)

_exe_args = [pyz]
if splash is not None:
    # Splash must be passed as a positional argument so it becomes a 'SPLASH' entry in the PKG TOC.
    _exe_args.append(splash)

_exe_args.extend([a.scripts, a.binaries, a.datas])

if splash is not None:
    # Also pass splash's Tcl/Tk runtime dependencies.
    _exe_args.append(splash.binaries)

_exe_args.append([])

exe = EXE(
    *_exe_args,
    name=EXE_NAME,
    version=str(_version_file) if _version_file else None,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

if IS_MACOS:
    app = BUNDLE(
        exe,
        name=f'{EXE_NAME}.app',
        bundle_identifier='com.colorfabb.filament-installer',
    )
