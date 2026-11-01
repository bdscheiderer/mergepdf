"""Build the Windows .ico and the Mac .icns from the red "m" PNG.

How to run this file
--------------------
From the project folder, after the libraries are installed.

On a Mac:

    .venv/bin/python scripts/make_icons.py

On Windows:

    .venv/Scripts/python scripts/make_icons.py

scripts/build_macos.sh always runs this file. scripts/build_windows.ps1
runs it when favicon.ico is missing or older than icon.png.

What it reads
-------------
assets/icon.png

That PNG is the brand: a red rounded square with a white script "m".
It is the picture used on https://mergepdf.s2legacy.com and the picture
Bryan chose for the app. Do not replace it with the older drawing of
two documents and arrows.

What it writes
--------------
assets/favicon.ico   Windows icon, several sizes in one file.
assets/icon.icns     Mac icon. The Mac build script replaces this with
                     an icon made by Apple's iconutil when that tool is
                     available, because iconutil is the native tool.

Pillow (the image library) comes in with ttkbootstrap, so a normal
install of requirements.txt is enough to run this script.
"""

from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow is not installed, so the icons cannot be rebuilt.")
    print("From the project folder, run:")
    print("    .venv/bin/python -m pip install -r requirements.txt")
    raise SystemExit(1)


# Folder that contains mergepdf.py. This script lives in scripts/.
PROJECT_FOLDER = Path(__file__).resolve().parent.parent
ICON_PNG = PROJECT_FOLDER / "assets" / "icon.png"
FAVICON_ICO = PROJECT_FOLDER / "assets" / "favicon.ico"
ICON_ICNS = PROJECT_FOLDER / "assets" / "icon.icns"

# Sizes stored inside the .ico. Windows picks the one closest to the
# spot it is drawing (title bar, taskbar, desktop shortcut).
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def load_master_icon():
    """Open the red "m" PNG that every other icon is copied from.

    Purpose:
        Fail early, with a plain message, if the master picture is missing.

    Inputs:
        None. The path is ICON_PNG at the top of this file.

    Outputs:
        A Pillow image in RGBA mode (red, green, blue, and transparency).

    Side effects:
        Reads assets/icon.png from disk.
        Exits the program if that file is missing or is not an image.
    """
    if not ICON_PNG.is_file():
        print("Missing the master icon: " + str(ICON_PNG))
        print("Put the red m PNG at assets/icon.png and run this script again.")
        raise SystemExit(1)

    image = Image.open(ICON_PNG)
    image.load()
    return image.convert("RGBA")


def write_favicon(master):
    """Write assets/favicon.ico with several sizes of the same artwork.

    Purpose:
        Windows and browsers want an .ico file. One .ico can hold many
        sizes. Pillow scales the 512 pixel master down to each size.

    Inputs:
        master: the Pillow image returned by load_master_icon().

    Outputs:
        None.

    Side effects:
        Creates or replaces assets/favicon.ico.
    """
    size_pairs = []
    for size in ICO_SIZES:
        size_pairs.append((size, size))

    master.save(FAVICON_ICO, format="ICO", sizes=size_pairs)


def write_icns(master):
    """Write a fallback assets/icon.icns for the Mac app bundle.

    Purpose:
        PyInstaller needs an .icns file to set the Finder and Dock icon.
        Pillow can write one on any computer. On a Mac, scripts/build_macos.sh
        builds a sharper one with iconutil and overwrites this file.

    Inputs:
        master: the Pillow image returned by load_master_icon().

    Outputs:
        None.

    Side effects:
        Creates or replaces assets/icon.icns.
    """
    master.save(ICON_ICNS, format="ICNS")


def main():
    """Rebuild favicon.ico and icon.icns, then print where they went.

    Purpose:
        One command refreshes both generated icon files from icon.png.

    Inputs:
        None.

    Outputs:
        None.

    Side effects:
        Writes the two icon files and prints their paths.
    """
    master = load_master_icon()
    write_favicon(master)
    write_icns(master)
    print("Wrote " + str(FAVICON_ICO))
    print("Wrote " + str(ICON_ICNS))


if __name__ == "__main__":
    main()
