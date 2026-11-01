#!/bin/bash
# Build MergePDF.app and a MergePDF disk image on a Mac.
#
# This script does not run on Linux or Windows. The cloud agent that
# prepared the project could not create the .dmg or check the Dock icon.
# Run this on the Mac mini, from any folder:
#
#     ./scripts/build_macos.sh
#
# What you get
# ------------
# dist/MergePDF.app
# dist/MergePDF-1.2.dmg
#
# The .app and the .dmg are not signed and not notarized. macOS will
# warn the first time they are opened. The README explains that warning.

set -euo pipefail

# The script lives in scripts/. Move to the project folder so every
# relative path below (assets, dist, .venv) is correct even when the
# Terminal was sitting somewhere else.
cd "$(dirname "$0")/.."
PROJECT_FOLDER="$(pwd)"

echo "Project folder: ${PROJECT_FOLDER}"

require_mac() {
    # Purpose: refuse to build a Mac app on the wrong computer.
    # Inputs: none. Reads the output of uname.
    # Outputs: none.
    # Side effects: exits the script when the system is not macOS.
    local system_name
    system_name="$(uname -s)"
    if [[ "${system_name}" != "Darwin" ]]; then
        echo "This build is for macOS. This computer reports: ${system_name}"
        echo "On Windows, run:  .\\scripts\\build_windows.ps1"
        exit 1
    fi
}

python_can_draw_a_window() {
    # Purpose: make sure this Python includes Tk, which draws the window.
    # Inputs: none. Uses the PYTHON variable set below.
    # Outputs: none.
    # Side effects: exits with install help when tkinter cannot be imported.
    if "${PYTHON}" -c "import tkinter" >/dev/null 2>&1; then
        return 0
    fi

    echo "This Python cannot draw a window (tkinter is missing)."
    echo "Install Python from https://www.python.org/downloads/macos/"
    echo "That installer includes Tk."
    echo "If you use Homebrew, install the python-tk package that matches"
    echo "your Python version, then delete the .venv folder and run this script again."
    exit 1
}

install_build_tools() {
    # Purpose: create a private library folder and install PyInstaller.
    # Inputs: none.
    # Outputs: none.
    # Side effects: creates .venv if needed and installs requirements-build.txt.
    if [[ ! -x ".venv/bin/python" ]]; then
        echo "Creating .venv with: python3 -m venv .venv"
        python3 -m venv .venv
    fi

    PYTHON="${PROJECT_FOLDER}/.venv/bin/python"
    echo "Using ${PYTHON}"
    "${PYTHON}" -m pip install --upgrade pip
    "${PYTHON}" -m pip install -r requirements-build.txt
    python_can_draw_a_window
}

refresh_icons() {
    # Purpose: rebuild favicon.ico and icon.icns from the red m PNG.
    # Inputs: none. Reads assets/icon.png.
    # Outputs: none.
    # Side effects: rewrites assets/favicon.ico and assets/icon.icns.
    # On a Mac, Apple's iconutil then replaces icon.icns with a native one.
    echo "Refreshing icons from assets/icon.png"
    "${PYTHON}" scripts/make_icons.py
    build_native_icns_if_possible
}

build_native_icns_if_possible() {
    # Purpose: build assets/icon.icns with Apple's iconutil when it exists.
    # Inputs: none. Reads assets/icon.png.
    # Outputs: none.
    # Side effects: replaces assets/icon.icns when sips and iconutil succeed.
    # The 512 pixel master is scaled into the sizes iconutil expects.
    # The 1024 pixel slot is a scaled copy of that 512 pixel picture.
    if ! command -v sips >/dev/null 2>&1; then
        echo "sips was not found. Keeping the icon.icns written by Pillow."
        return 0
    fi
    if ! command -v iconutil >/dev/null 2>&1; then
        echo "iconutil was not found. Keeping the icon.icns written by Pillow."
        return 0
    fi

    local iconset
    iconset="${PROJECT_FOLDER}/build/MergePDF.iconset"
    rm -rf "${iconset}"
    mkdir -p "${iconset}"

    local source_png
    source_png="${PROJECT_FOLDER}/assets/icon.png"

    sips -z 16 16     "${source_png}" --out "${iconset}/icon_16x16.png" >/dev/null
    sips -z 32 32     "${source_png}" --out "${iconset}/icon_16x16@2x.png" >/dev/null
    sips -z 32 32     "${source_png}" --out "${iconset}/icon_32x32.png" >/dev/null
    sips -z 64 64     "${source_png}" --out "${iconset}/icon_32x32@2x.png" >/dev/null
    sips -z 128 128   "${source_png}" --out "${iconset}/icon_128x128.png" >/dev/null
    sips -z 256 256   "${source_png}" --out "${iconset}/icon_128x128@2x.png" >/dev/null
    sips -z 256 256   "${source_png}" --out "${iconset}/icon_256x256.png" >/dev/null
    sips -z 512 512   "${source_png}" --out "${iconset}/icon_256x256@2x.png" >/dev/null
    sips -z 512 512   "${source_png}" --out "${iconset}/icon_512x512.png" >/dev/null
    sips -z 1024 1024 "${source_png}" --out "${iconset}/icon_512x512@2x.png" >/dev/null

    iconutil -c icns "${iconset}" -o "${PROJECT_FOLDER}/assets/icon.icns"
    echo "Wrote a native Mac icon: assets/icon.icns"
}

build_app() {
    # Purpose: run PyInstaller and require the red m icon inside the .app.
    # Inputs: none.
    # Outputs: none.
    # Side effects: deletes and recreates build/ and dist/MergePDF.app.
    # --clean drops leftovers from an older icon so Finder cannot keep
    # showing a previous picture.
    echo "Running PyInstaller"
    "${PYTHON}" -m PyInstaller --noconfirm --clean MergePDF.spec

    local app_path
    app_path="${PROJECT_FOLDER}/dist/MergePDF.app"
    local icon_in_app
    icon_in_app="${app_path}/Contents/Resources/icon.icns"

    if [[ ! -d "${app_path}" ]]; then
        echo "PyInstaller did not create ${app_path}"
        exit 1
    fi
    if [[ ! -f "${icon_in_app}" ]]; then
        echo "The app bundle has no Contents/Resources/icon.icns."
        echo "Finder and the Dock would show a generic icon."
        exit 1
    fi

    local icon_name
    icon_name="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIconFile' "${app_path}/Contents/Info.plist")"
    echo "Info.plist icon file: ${icon_name}"
    if [[ "${icon_name}" != "icon.icns" ]]; then
        echo "CFBundleIconFile should be icon.icns so the Dock uses the red m."
        exit 1
    fi
}

build_disk_image() {
    # Purpose: wrap MergePDF.app in a .dmg with a shortcut to Applications.
    # Inputs: none.
    # Outputs: none.
    # Side effects: writes dist/MergePDF-1.2.dmg and a temporary dmg-root folder.
    #
    # hdiutil flags:
    #   -volname   the name you see when the disk image is opened
    #   -srcfolder the folder to copy onto the disk image
    #   -ov        replace an older dmg with the same name
    #   -format UDZO  compressed, the usual format for a download
    local dmg_root
    dmg_root="${PROJECT_FOLDER}/dist/dmg-root"
    local dmg_path
    dmg_path="${PROJECT_FOLDER}/dist/MergePDF-1.2.dmg"

    rm -rf "${dmg_root}"
    mkdir -p "${dmg_root}"
    cp -R "${PROJECT_FOLDER}/dist/MergePDF.app" "${dmg_root}/"
    ln -s /Applications "${dmg_root}/Applications"

    rm -f "${dmg_path}"
    hdiutil create \
        -volname "MergePDF" \
        -srcfolder "${dmg_root}" \
        -ov \
        -format UDZO \
        "${dmg_path}"

    rm -rf "${dmg_root}"
    echo "Disk image: ${dmg_path}"
}

require_mac
install_build_tools
refresh_icons
build_app
build_disk_image

echo ""
echo "Built:"
echo "    dist/MergePDF.app"
echo "    dist/MergePDF-1.2.dmg"
echo ""
echo "The app is not signed. The first time you open it, use the steps"
echo "in the README section named \"First launch on a Mac\"."
