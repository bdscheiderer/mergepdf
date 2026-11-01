"""Check that this Python can draw a window.

The Windows build script runs this file. It does not use python -c.
Windows PowerShell 5.1 rewrites quotes inside a python -c string before
Python starts. A check written as one line was split into:

    import tkinter; print(Tk

Python then reported a SyntaxError, and the build script treated that
as a missing Tk. This file is a normal program, so those quotes never
go through PowerShell's argument rules.

How to run it
-------------
From the project folder:

    .venv/Scripts/python scripts/check_tk.py

Exit codes
----------
0    tkinter imported. The Tk version is printed.
2    tkinter is not installed. The message says that, and only that.
any other code
     Something else failed. The traceback is the reason. It does not
     mean Tcl/Tk is missing.
"""

# scripts/build_windows.ps1 treats 2 as "Tk is really missing".
# Any other non-zero code is a different failure.
EXIT_TK_MISSING = 2


def read_tk_version():
    """Return the Tk version, or None when tkinter is not installed.

    Purpose:
        Ask this Python whether Tcl/Tk is available. MergePDF's window
        is drawn by Tk. The version number is enough. Opening a window
        here would fail on a machine with no screen, even when Tk is
        installed.

    Inputs:
        None.

    Outputs:
        A string such as "8.6" when tkinter imports.
        None when importing tkinter raises ImportError.

    Side effects:
        Imports tkinter when it is installed.
        Does not open a window and does not create a Tk object.
        Any error other than ImportError is left alone, so the traceback
        still names the real problem.
    """
    try:
        import tkinter
    except ImportError:
        return None

    return str(tkinter.TkVersion)


def main():
    """Print the Tk version, or report that tkinter is missing.

    Purpose:
        Give scripts/build_windows.ps1 a result it can trust.

    Inputs:
        None. Uses the Python that started this file.

    Outputs:
        None.

    Side effects:
        Prints "Tk version " and the version, then exits 0, when Tk works.
        Prints "tkinter is missing." and exits 2 when the import fails.
        Lets any other error end the program with Python's normal traceback.
    """
    version = read_tk_version()
    if version is None:
        print("tkinter is missing.")
        print("MergePDF needs Tcl/Tk to draw its window.")
        raise SystemExit(EXIT_TK_MISSING)

    print("Tk version " + version)


if __name__ == "__main__":
    main()
