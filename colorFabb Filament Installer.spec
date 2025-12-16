# -*- mode: python ; coding: utf-8 -*-

import ast
import os
import re
from pathlib import Path

from PyInstaller.config import CONF


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


def _version_tuple(ver: str) -> tuple[int, int, int, int]:
    parts = [p for p in re.split(r'[^0-9]+', ver) if p]
    nums = [int(p) for p in parts[:3]]
    while len(nums) < 3:
        nums.append(0)
    return (nums[0], nums[1], nums[2], 0)


_fv = _version_tuple(APP_VERSION)
_pv = _fv

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
    datas=[('C:\\DevOps\\printer-profiles-installer-py\\logo\\cF_Logo.png', 'logo')],
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
    return not any(dest.startswith(p) for p in _remove_prefixes)

a.binaries = [b for b in a.binaries if _keep_binary(b)]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=EXE_NAME,
    version=str(_version_file),
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
