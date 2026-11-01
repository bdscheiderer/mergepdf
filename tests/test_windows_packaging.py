"""Checks for the Windows packaging files. These tests do not build an exe.

Run them from the project folder:

    .venv/bin/python -m unittest tests.test_windows_packaging -v

On Windows:

    .venv\\Scripts\\python -m unittest tests.test_windows_packaging -v

PyInstaller executes a spec file. These tests execute the spec with stand-in
Analysis, PYZ, and EXE calls, so the checks run on Linux and on Windows
without packing a program. They confirm the Windows spec stays a single
windowed exe, and that the Mac spec still builds a .app.
"""

import subprocess
import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parent.parent
WINDOWS_SPEC = PROJECT / "MergePDF-windows.spec"
MAC_SPEC = PROJECT / "MergePDF.spec"
INNO_SCRIPT = PROJECT / "mergepdf.iss"
BUILD_SCRIPT = PROJECT / "scripts" / "build_windows.ps1"
GITIGNORE = PROJECT / ".gitignore"


def execute_spec(path, platform_name):
    """Run a PyInstaller spec with stand-in build steps.

    Purpose:
        Check the choices in a spec file (one file or a folder, windowed
        or console, which icon) without running a real PyInstaller build.

    Inputs:
        path: pathlib.Path of a .spec file.
        platform_name: the value to put in sys.platform while the spec
            runs. "win32" is Windows. "darwin" is macOS. "linux" is Linux.

    Outputs:
        A dict of the calls the spec made. Keys appear only when that
        step ran: "analysis", "exe", "exe_args", "collect", "bundle".

    Side effects:
        Sets sys.platform for the duration of the spec, then puts the
        previous value back. Does not write a dist folder.
        Raises SystemExit when the spec refuses this platform.
    """
    captured = {}

    class Analysis:
        """Stand-in for PyInstaller's Analysis. Records the arguments."""

        def __init__(self, scripts, **kwargs):
            self.pure = []
            self.scripts = []
            self.binaries = "BINARIES"
            self.datas = "DATAS"
            captured["analysis_scripts"] = scripts
            captured["analysis"] = kwargs

    class PYZ:
        """Stand-in for PyInstaller's PYZ. Records that it was called."""

        def __init__(self, pure):
            captured["pyz"] = pure

    class EXE:
        """Stand-in for PyInstaller's EXE. Records the arguments."""

        def __init__(self, *args, **kwargs):
            captured["exe_args"] = args
            captured["exe"] = kwargs

    class COLLECT:
        """Stand-in for PyInstaller's COLLECT. Marks an onedir build."""

        def __init__(self, *args, **kwargs):
            captured["collect"] = kwargs

    class BUNDLE:
        """Stand-in for PyInstaller's BUNDLE. Marks a Mac .app."""

        def __init__(self, *args, **kwargs):
            captured["bundle"] = kwargs

    namespace = {
        "Analysis": Analysis,
        "PYZ": PYZ,
        "EXE": EXE,
        "COLLECT": COLLECT,
        "BUNDLE": BUNDLE,
        "__name__": "spec",
    }
    source = path.read_text(encoding="utf-8")
    original_platform = sys.platform
    sys.platform = platform_name
    try:
        exec(compile(source, str(path), "exec"), namespace)
    finally:
        sys.platform = original_platform
    return captured


def exit_message(exc):
    """Return the text a SystemExit was raised with.

    Purpose:
        Spec files stop with raise SystemExit("a message"). The message
        is on the exception. This helper reads it for assertions.

    Inputs:
        exc: a SystemExit instance.

    Outputs:
        The message as a string.

    Side effects:
        None.
    """
    if isinstance(exc.code, str):
        return exc.code
    return str(exc)


class WindowsPackagingTests(unittest.TestCase):
    def test_windows_spec_refuses_other_systems(self):
        with self.assertRaises(SystemExit) as caught:
            execute_spec(WINDOWS_SPEC, "linux")
        message = exit_message(caught.exception)
        self.assertIn("MergePDF-windows.spec", message)
        self.assertIn("build_windows.ps1", message)
        self.assertIn("build_macos.sh", message)

    def test_windows_spec_builds_one_windowed_exe(self):
        captured = execute_spec(WINDOWS_SPEC, "win32")

        self.assertEqual(captured["analysis_scripts"], ["mergepdf.py"])
        datas = captured["analysis"]["datas"]
        self.assertIn(("assets/icon.png", "assets"), datas)
        self.assertIn(("assets/favicon.ico", "assets"), datas)
        self.assertEqual(captured["analysis"]["optimize"], 0)

        exe = captured["exe"]
        self.assertEqual(exe["name"], "MergePDF")
        self.assertIs(exe["console"], False)
        self.assertIs(exe["exclude_binaries"], False)
        self.assertEqual(exe["icon"], "assets/favicon.ico")
        self.assertIs(exe["upx"], False)
        self.assertIs(exe["uac_admin"], False)
        self.assertIn("BINARIES", captured["exe_args"])
        self.assertIn("DATAS", captured["exe_args"])
        self.assertNotIn("collect", captured)
        self.assertNotIn("bundle", captured)

    def test_mac_spec_still_refuses_other_systems(self):
        with self.assertRaises(SystemExit) as caught:
            execute_spec(MAC_SPEC, "linux")
        message = exit_message(caught.exception)
        self.assertIn("macOS", message)
        self.assertIn("build_macos.sh", message)
        self.assertIn("build_windows.ps1", message)

    def test_mac_spec_still_builds_an_app_bundle(self):
        captured = execute_spec(MAC_SPEC, "darwin")

        self.assertEqual(captured["analysis_scripts"], ["mergepdf.py"])
        datas = captured["analysis"]["datas"]
        self.assertIn(("assets/icon.png", "assets"), datas)
        self.assertIn(("assets/favicon.ico", "assets"), datas)

        exe = captured["exe"]
        self.assertEqual(exe["name"], "MergePDF")
        self.assertIs(exe["console"], False)
        self.assertIs(exe["exclude_binaries"], True)
        self.assertEqual(exe["icon"], "assets/icon.icns")
        self.assertIn("collect", captured)
        self.assertEqual(captured["bundle"]["name"], "MergePDF.app")
        self.assertEqual(captured["bundle"]["version"], "1.2.0")
        self.assertEqual(captured["bundle"]["icon"], "assets/icon.icns")

    def test_inno_script_still_packages_dist_mergepdf_exe(self):
        text = INNO_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('#define AppVersion "1.2"', text)
        self.assertIn('#define AppExeName "MergePDF.exe"', text)
        self.assertIn("OutputDir=installer", text)
        self.assertIn("OutputBaseFilename=MergePDF-1.2-Setup", text)
        self.assertIn('Source: "dist\\{#AppExeName}"', text)
        self.assertIn("SetupIconFile=assets\\favicon.ico", text)
        self.assertIn("LicenseFile=LICENSE.txt", text)

    def test_build_script_matches_the_spec_and_the_installer(self):
        text = BUILD_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("MergePDF-windows.spec", text)
        self.assertIn("--noconfirm", text)
        self.assertIn("--clean", text)
        self.assertIn("dist\\MergePDF.exe", text)
        self.assertIn("installer\\MergePDF-1.2-Setup.exe", text)
        self.assertIn("requirements-build.txt", text)
        self.assertIn("make_icons.py", text)
        self.assertIn("Program Files (x86)", text)
        self.assertIn("Inno Setup 6\\ISCC.exe", text)
        self.assertIn("Purpose:", text)
        # PowerShell 5.1, which ships with Windows, does not support these.
        self.assertNotIn("&&", text)
        self.assertNotIn("??", text)
        self.assert_every_powershell_function_is_documented(text)

    def assert_every_powershell_function_is_documented(self, text):
        """Each PowerShell function states purpose, inputs, and results.

        Purpose:
            The build script is meant to be read by someone new to
            packaging. A function without those notes is incomplete.

        Inputs:
            text: the full text of scripts/build_windows.ps1.

        Outputs:
            None.

        Side effects:
            Fails the test when a function is missing one of the notes.
        """
        parts = text.split("\nfunction ")
        # parts[0] is the script header, before the first function.
        functions = parts[1:]
        self.assertGreaterEqual(len(functions), 10)
        for function_text in functions:
            name = function_text.splitlines()[0].strip().rstrip("{").strip()
            # The param() block may sit above the notes, or the notes may
            # sit above param(). Either order is fine. Both must be present
            # in the function, before the next function starts.
            for note in ("Purpose:", "Inputs:", "Outputs:", "Side effects:"):
                self.assertIn(note, function_text, name + " is missing " + note)

    def test_gitignore_keeps_the_windows_spec_and_drops_the_installer(self):
        text = GITIGNORE.read_text(encoding="utf-8")
        self.assertIn("!MergePDF.spec", text)
        self.assertIn("!MergePDF-windows.spec", text)
        self.assertIn("installer/", text)

        # git check-ignore -q exits 0 when the path is ignored, and 1 when
        # it is not. -v is the wrong check here: it also matches the "!"
        # lines that put a file back, and then exits 0.
        spec_check = subprocess.run(
            ["git", "check-ignore", "-q", "MergePDF-windows.spec"],
            cwd=PROJECT,
        )
        self.assertEqual(
            spec_check.returncode,
            1,
            "MergePDF-windows.spec is ignored, so the Windows build file would not be committed.",
        )

        mac_check = subprocess.run(
            ["git", "check-ignore", "-q", "MergePDF.spec"],
            cwd=PROJECT,
        )
        self.assertEqual(mac_check.returncode, 1)

        installer_check = subprocess.run(
            ["git", "check-ignore", "-q", "installer/MergePDF-1.2-Setup.exe"],
            cwd=PROJECT,
        )
        self.assertEqual(installer_check.returncode, 0)


if __name__ == "__main__":
    unittest.main()
