# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Windows MergePDF.exe.

Run this through PyInstaller on Windows, not by itself:

    .venv/Scripts/python -m PyInstaller --noconfirm --clean MergePDF-windows.spec

scripts/build_windows.ps1 does that, then asks Inno Setup to compile
mergepdf.iss. The installer expects one file: dist/MergePDF.exe.

This is a onefile build. One file is what mergepdf.iss copies, and it
is also a reasonable portable exe. The Mac spec (MergePDF.spec) stays
onedir because a Mac .app is a folder. Do not copy the Mac EXE block
into this file.

The red m icon on the exe and in the window is assets/favicon.ico.
assets/icon.png is included too, the same way the Mac app includes both
files. resource_path() in mergepdf.py finds them at runtime.
"""

import sys


def require_windows():
    """Stop the build when it is not running on Windows.

    Purpose:
        This file creates MergePDF.exe. PyInstaller builds a Windows exe
        on Windows. On a Mac, MergePDF.spec is the file that builds the app.

    Inputs:
        None. It looks at sys.platform.

    Outputs:
        None.

    Side effects:
        Exits the program with a message when the system is not Windows.
    """
    if sys.platform != "win32":
        raise SystemExit(
            "MergePDF-windows.spec builds a Windows program.\n"
            "On Windows, run:  .\\scripts\\build_windows.ps1\n"
            "On a Mac, run:  ./scripts/build_macos.sh"
        )


require_windows()

# Analysis finds mergepdf.py, the modules it imports, and the icon files
# that must be copied into the exe. "assets" on the right is the folder
# name inside the packed program. resource_path() looks there.
#
# The file list matches MergePDF.spec. optimize=0 keeps assert statements
# in the packed program, so a failure is easier to read. requirements-build.txt
# asks for PyInstaller 6.16 or newer, which accepts optimize.
#
# hiddenimports is empty on purpose, same as the Mac spec. mergepdf.py
# imports tkinter, ttkbootstrap, and pypdf directly, so PyInstaller sees
# them. ttkbootstrap brings its own hook that copies its theme pictures.
# Those pictures are not listed here.
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
    optimize=0,
)
pyz = PYZ(a.pure)

# onefile: binaries and datas are arguments of EXE, and there is no COLLECT
# and no BUNDLE. PyInstaller then writes a single dist/MergePDF.exe.
# exclude_binaries=False is what makes that one file hold the libraries.
# The Mac spec sets exclude_binaries=True and then uses COLLECT, because a
# Mac .app is a folder. Leave this one False.
#
# console=False means no black console window behind the app.
# disable_windowed_traceback=False lets PyInstaller show a crash dialog.
# If that dialog is not enough, run from source:
#     .venv\Scripts\python mergepdf.py
#
# The name must stay MergePDF. On Windows that becomes MergePDF.exe, which
# is the file mergepdf.iss copies out of dist\.
#
# The empty list is PyInstaller's slot for extra Python options. Leave it
# empty so assert statements stay active.
#
# upx=False: UPX compresses executables. It is unnecessary here and can
# make antivirus tools more suspicious of the exe. Same choice as the Mac spec.
#
# runtime_tmpdir=None: each launch unpacks into the normal Windows temp
# folder. The first window can take a few seconds. That is normal for onefile.
#
# icon is the red m. favicon.ico holds several sizes. Windows picks one.
# uac_admin=False: opening the program does not ask for administrator rights.
# This build does not sign the exe.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    exclude_binaries=False,
    name="MergePDF",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/favicon.ico",
    uac_admin=False,
)
