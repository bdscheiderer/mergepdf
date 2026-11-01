"""Tests for scripts/check_tk.py. These tests do not open a window.

Run them from the project folder:

    .venv/bin/python -m unittest tests.test_check_tk -v

On Windows:

    .venv/Scripts/python -m unittest tests.test_check_tk -v
"""

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parent.parent
CHECK_TK = PROJECT / "scripts" / "check_tk.py"


def run_check(fake_tkinter_source):
    """Run scripts/check_tk.py with a stand-in tkinter module.

    Purpose:
        Prove the checker without using the machine's real Tk, and
        without a python -c string. PowerShell's quoting bug is what
        this file exists to avoid, so the test runs the file too.

    Inputs:
        fake_tkinter_source: Python source for a module named tkinter.
            It is placed on PYTHONPATH ahead of the real standard library.

    Outputs:
        A completed subprocess.CompletedProcess. returncode, stdout, and
        stderr are filled in.

    Side effects:
        Writes one temporary tkinter.py and runs a Python process.
        Deletes that folder when the process ends.
    """
    with tempfile.TemporaryDirectory() as folder:
        fake_path = Path(folder) / "tkinter.py"
        fake_path.write_text(fake_tkinter_source, encoding="utf-8")
        env = os.environ.copy()
        # This folder is searched before the real standard library, so the
        # stand-in tkinter is the one the checker imports.
        env["PYTHONPATH"] = folder
        return subprocess.run(
            [sys.executable, str(CHECK_TK)],
            cwd=PROJECT,
            capture_output=True,
            text=True,
            env=env,
        )


class CheckTkTests(unittest.TestCase):
    def test_present_tk_prints_the_version_and_exits_zero(self):
        result = run_check("TkVersion = 8.6\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Tk version 8.6", result.stdout)
        self.assertNotIn("tkinter is missing", result.stdout)

    def test_missing_tk_exits_2_and_says_it_is_missing(self):
        source = textwrap.dedent(
            """
            raise ImportError("No module named tkinter")
            """
        )
        result = run_check(source)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("tkinter is missing.", result.stdout)
        self.assertNotIn("SyntaxError", result.stderr)

    def test_a_different_error_is_not_called_missing_tk(self):
        source = textwrap.dedent(
            """
            raise RuntimeError("tkinter failed while loading")
            """
        )
        result = run_check(source)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotEqual(result.returncode, 2)
        self.assertIn("RuntimeError", result.stderr)
        self.assertNotIn("tkinter is missing.", result.stdout)
