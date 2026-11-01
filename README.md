# MergePDF

MergePDF is a small desktop app. You pick a folder, check the PDFs you want, name the result, and it writes one new PDF in that same folder. The files stay on your computer. The app does not upload them.

This version uses [pypdf](https://pypi.org/project/pypdf/) to join the pages and [ttkbootstrap](https://ttkbootstrap.readthedocs.io/) for the window. An earlier version used PyPDF2. That library is no longer maintained. pypdf is the project that continued the work, and `PdfWriter.append` is the call that joins the files.

The app icon is the red rounded square with the white script “m”.

Portfolio: [s2legacy.com](https://s2legacy.com) · Download page: [mergepdf.s2legacy.com](https://mergepdf.s2legacy.com)

The download buttons on the website can stay as they are for now. This project folder is the app itself.

## Run it on a Mac

These steps were checked as far as a Linux machine can check them (the tests, and opening the window). Building the `.app` and the `.dmg` has to happen on your Mac. The script is ready. The Dock picture and Gatekeeper warning were not seen from here.

### 1. Install Python 3.10 or newer, with Tk

Tk is the toolkit that draws the window. The python.org installer includes it.

1. Open [https://www.python.org/downloads/macos/](https://www.python.org/downloads/macos/) and install the current macOS Python (3.12 or 3.13 is fine).
2. Open Terminal and run:

```bash
python3 --version
python3 -c "import tkinter; print(tkinter.TkVersion)"
```

You want a version of at least 3.10, and the second command should print a number such as `8.6`.

If you already installed Python with Homebrew and the second command fails, install the matching Tk package and try again. For Homebrew’s Python 3.12 that package is:

```bash
brew install python-tk@3.12
```

Use the `@` version that matches `python3 --version`.

### 2. Get the code

```bash
git clone https://github.com/bdscheiderer/mergepdf.git
cd mergepdf
```

If the folder is already on the Mac, `cd` into it instead of cloning again.

### 3. Install the libraries into a project folder

A virtual environment (the `.venv` folder) keeps these libraries next to the project.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

### 4. Start the app

```bash
.venv/bin/python mergepdf.py
```

The window has three steps:

1. **Select folder.** A checklist opens with every PDF in that folder checked. The list starts in A to Z order. Click a file name, then use Move up, Move down, Move to top, or Move to bottom. Uncheck any file you want to leave out. Confirm needs at least two files. The merge follows the list from top to bottom.
2. **Submit name.** Leave the box blank to use `merged_pdfs.pdf`.
3. **Merge PDFs.** The new file is written in the same folder. If that name already exists, the date and time are added in front so the older file is kept.

**Open merged PDF** appears after a successful merge and opens the file in Preview.

**Reset** clears the form. It does not delete any PDF.

While you run from source, the title bar uses `assets/icon.png`. The Dock icon for a source run is still Python’s icon. The red “m” shows in the Dock after you build `MergePDF.app` (next section).

## Check the code

From the project folder:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

`tests/test_merge_logic.py` builds small PDFs and merges them. It checks page order, bookmarks, a bad file, and a password-protected file.

`tests/test_window.py` opens the real window, fills in a name, and clicks the merge code. It needs a display (your Mac has one). It does not click the system folder dialog. Try that dialog yourself once: Select folder, confirm two files, merge, and open the result in Preview.

## Build a Mac app and a disk image

Run this on the Mac, in the project folder:

```bash
chmod +x scripts/build_macos.sh
./scripts/build_macos.sh
```

The script:

1. Creates `.venv` if it is missing and installs `requirements-build.txt` (the run libraries plus PyInstaller).
2. Rebuilds `assets/favicon.ico` and `assets/icon.icns` from `assets/icon.png`.
3. When `sips` and `iconutil` are available (they are on a normal Mac), it rebuilds `icon.icns` with Apple’s tools so Finder gets a native icon.
4. Runs PyInstaller with `MergePDF.spec`.
5. Checks that `dist/MergePDF.app` contains `Contents/Resources/icon.icns` and that `Info.plist` points at it.
6. Writes `dist/MergePDF-1.2.dmg` with the app and a shortcut to the Applications folder.

The `.app` matches the kind of Mac you build it on. An Apple silicon Mac mini produces an Apple silicon app. `LSMinimumSystemVersion` in the bundle is 11.0. The practical floor is the macOS version required by the Python you used to build.

PyInstaller is the right packager for this stack: one Python file, Tk, and pypdf, with no separate web view. The spec file uses the onedir `.app` layout. A one-file Mac bundle fights macOS security checks, and current PyInstaller warns against it.

### First launch on a Mac

The script does not sign the app and does not send it to Apple for notarization. Gatekeeper will block a normal double-click.

To open it the first time:

1. Move `MergePDF.app` to the Applications folder (or open the `.dmg` and drag the app onto the Applications shortcut).
2. In Finder, Control-click `MergePDF` and choose **Open**.
3. Confirm **Open** in the dialog. macOS remembers that choice.

If Control-click is not offered, open **System Settings → Privacy & Security** and use the **Open Anyway** button next to the MergePDF block message.

After that, a normal double-click is enough. The Dock and Finder icon should be the red “m”. If you still see a generic icon, the build script would have stopped with an error about `icon.icns`. Run it again and read the last lines.

To see a Python error, run from source (` .venv/bin/python mergepdf.py `) in Terminal. The built app has no Terminal window. A crash in the built app shows PyInstaller’s error dialog.

### Signing and notarizing later

These commands are optional. They need an Apple Developer membership and a Developer ID Application certificate in your Keychain. They were not run from the machine that prepared this update. Replace the name in quotes with the exact certificate name from Keychain Access.

```bash
codesign --deep --force --options runtime --sign "Developer ID Application: Your Name (TEAMID)" dist/MergePDF.app
codesign --verify --verbose dist/MergePDF.app

xcrun notarytool submit dist/MergePDF-1.2.dmg --apple-id "you@example.com" --team-id "TEAMID" --wait
xcrun stapler staple dist/MergePDF.app
```

`notarytool` also accepts a keychain profile so the Apple ID password is not typed into the command. Apple’s notarization notes: [https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution).

Do this only when you are ready to publish a download. It is not required to use the app on your own Mac.

## Icons

| File | Role |
| --- | --- |
| `assets/icon.png` | Master picture, 512×512, red “m”. The window uses this when you run from source. |
| `assets/icon.icns` | Mac Finder and Dock icon, used by PyInstaller. |
| `assets/favicon.ico` | Same artwork, several sizes. Windows exe icon, installer icon, and the window icon on Windows. Also used for a browser tab. |

Rebuild them after replacing the PNG:

```bash
.venv/bin/python scripts/make_icons.py
```

On a Mac, `./scripts/build_macos.sh` does that and then runs `iconutil`. On Windows, `.\scripts\build_windows.ps1` runs the same icon script when `favicon.ico` is missing or older than the PNG.

## Where the code lives

Read in this order:

1. `merge_logic.py` — finds PDFs, checks the file name, and merges. No window. Each function says what it is for, what it expects, and what it changes.
2. `mergepdf.py` — the three-step window. It calls the functions in `merge_logic.py`. The shared sizes are in `window_layout.py`.
3. `tests/` — small PDFs created during the test, then deleted.
4. `MergePDF.spec` and `scripts/build_macos.sh` — the Mac app build.
5. `MergePDF-windows.spec`, `scripts/build_windows.ps1`, and `mergepdf.iss` — the Windows exe and the Setup installer.

`main()` is at the bottom of `mergepdf.py`.

## Windows

Build the `.exe` and the Setup installer on a Windows PC. Python 3.10 or newer, Git, and [Inno Setup 6](https://jrsoftware.org/isinfo.php) are the tools these steps use. Python 3.13 is a good choice. Creating `MergePDF.exe` has to happen on Windows. The checks in this repository cover the spec file and the build script. They do not produce the exe.

Inno Setup is what turns `dist\MergePDF.exe` into `installer\MergePDF-1.2-Setup.exe`. When Inno Setup is missing, the build script still creates the exe and prints how to install Inno and try again.

The window uses the same layout as the Mac app (720 by 640, with the same gaps around the buttons). On a Windows display set above 100%, that layout grows with the display. A 150% setting opens a wider, taller window so Merge, Reset, Help, and Exit are not packed into the 100% pixel size. The Mac window stays the size it already is.

### 1. Install Python, with Tcl/Tk

Tcl/Tk is the toolkit that draws the window. The python.org installer includes it when **tcl/tk and IDLE** is checked. That box is checked by default. Leave it checked.

1. Open [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/) and install the current Windows Python (3.12 or 3.13 is fine).
2. If the installer offers **Add python.exe to PATH**, check it.
3. Open PowerShell and run:

```powershell
py -3 --version
py -3 -c "import tkinter; print(tkinter.TkVersion)"
```

You want a version of at least 3.10, and the second command should print a number such as `8.6`.

If the second command fails, run the Python installer again, choose **Modify**, and turn **tcl/tk and IDLE** on. Then open a new PowerShell window and try the two commands again.

### 2. Get the code

```powershell
git clone https://github.com/bdscheiderer/mergepdf.git
cd mergepdf
```

If the folder is already on the PC, `cd` into it instead of cloning again.

### 3. Build the program and the installer

From the project folder, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
```

If you are already in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\build_windows.ps1
```

`Bypass` applies only to this window. It lets PowerShell run the script. It does not change the setting for the whole PC. Run the script from PowerShell. Opening `build_windows.ps1` from File Explorer often opens the file in Notepad.

The script:

1. Creates `.venv` if it is missing and installs `requirements-build.txt` (the run libraries plus PyInstaller).
2. Rebuilds `assets\favicon.ico` from `assets\icon.png` when that icon is missing or older than the PNG. It uses `scripts\make_icons.py`.
3. Runs PyInstaller with `MergePDF-windows.spec`. That writes one windowed program, `dist\MergePDF.exe`, with the red “m” as its icon.
4. Checks that `dist\MergePDF.exe` exists.
5. When Inno Setup 6 is installed, compiles `mergepdf.iss` and checks that the Setup file exists. The script looks for `ISCC.exe` under `Program Files` and `Program Files (x86)\Inno Setup 6`.

The file to ship is:

```
installer\MergePDF-1.2-Setup.exe
```

Copy that file to another Windows PC and run it. Setup installs MergePDF for the current user. A desktop icon is an optional checkbox during setup.

`dist\MergePDF.exe` is the program the installer places on the PC. You can run that file on the computer that built it. Each launch unpacks into a temporary folder, so the first window can take a few seconds.

PyInstaller is the same packager the Mac build uses. On Windows the spec builds one file, because `mergepdf.iss` copies `dist\MergePDF.exe`. Close MergePDF before building again. Windows will not replace an exe that is still running.

### First launch on Windows

The script does not sign the exe or the installer. Windows SmartScreen may warn that an unrecognized app was blocked.

When that warning appears:

1. Choose **More info**.
2. Choose **Run anyway**. Some Windows versions say **Open anyway**.

Windows remembers that choice for that file.

To see a Python error, run from source in PowerShell. The built exe has no console window. A crash in the built exe shows PyInstaller’s error dialog.

```powershell
.\.venv\Scripts\python mergepdf.py
```

The build script already created `.venv` and installed the libraries. Tests, from the project folder:

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
```

`tests\test_window.py` opens the real window, so run it in a desktop session.

## License

MIT. See `LICENSE.txt`. Copyright 2026 S2 Legacy, LLC.
