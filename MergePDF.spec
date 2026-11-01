# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the macOS MergePDF.app bundle.

Run this through PyInstaller on a Mac, not by itself:

    .venv/bin/pyinstaller --noconfirm --clean MergePDF.spec

scripts/build_macos.sh does that, then wraps the .app in a .dmg.

The red m icon is assets/icon.icns. The window, while the app is
running from source, uses assets/icon.png. Both come from the same
master picture.
"""

import sys


def require_mac():
    """Stop the build when it is not running on macOS.

    Purpose:
        This file creates a Mac .app bundle. The bundle step does nothing
        useful on Linux or Windows.

    Inputs:
        None. It looks at sys.platform.

    Outputs:
        None.

    Side effects:
        Exits the program with a message when the system is not macOS.
    """
    if sys.platform != "darwin":
        raise SystemExit(
            "MergePDF.spec builds a macOS app.\n"
            "On a Mac, run:  ./scripts/build_macos.sh\n"
            "On Windows, run:  .\\scripts\\build_windows.ps1"
        )


require_mac()

# Analysis finds mergepdf.py, the modules it imports, and the icon files
# that must be copied into the app. "assets" on the right is the folder
# name inside the built app. resource_path() looks there.
a = Analysis(
    ["mergepdf.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("assets/icon.png", "assets"),
        ("assets/favicon.ico", "assets"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

# exclude_binaries=True plus COLLECT below is the onedir layout.
# A Mac .app is a folder, so onedir is the layout PyInstaller expects.
# console=False means no Terminal window. On macOS it also keeps the app
# from being marked as a background-only program (that flag would hide it).
# If a built app crashes, run it from source with python to see the error.
# disable_windowed_traceback=False lets PyInstaller show a crash dialog.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MergePDF",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.icns",
)

# upx=False: UPX compresses executables. It is unnecessary here and can
# make antivirus tools more suspicious of the app.
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MergePDF",
)

# version becomes CFBundleShortVersionString. It must be a string.
# The icon file is copied into Contents/Resources and named in Info.plist
# so Finder and the Dock show the red m.
app = BUNDLE(
    coll,
    name="MergePDF.app",
    icon="assets/icon.icns",
    bundle_identifier="com.s2legacy.mergepdf",
    version="1.2.0",
    info_plist={
        "CFBundleName": "MergePDF",
        "CFBundleDisplayName": "MergePDF",
        "CFBundleVersion": "1.2.0",
        "CFBundleShortVersionString": "1.2.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "11.0",
        "LSApplicationCategoryType": "public.app-category.productivity",
        "NSHumanReadableCopyright": "Copyright 2026 S2 Legacy, LLC",
    },
)
