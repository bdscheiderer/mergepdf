"""The part of MergePDF that joins PDF files. There is no window in this file.

How to read this file
---------------------
Start with the functions at the bottom of the "putting a name on the
result" section, then read merge_pdfs(). The window in mergepdf.py
collects the user's choices and calls these functions.

What a merge does
-----------------
1. list_pdfs() finds the PDF files sitting directly inside one folder.
2. The window lets the user uncheck any they do not want.
3. prepare_output_name() turns the text box into a legal file name.
4. choose_output_path() picks a path that will not overwrite an existing file.
5. merge_pdfs() reads the chosen PDFs and writes one new PDF.

The files stay on this computer. Nothing in this file uploads a PDF.

Library
-------
pypdf is the current PDF library. An older version of MergePDF used
PyPDF2 and its PdfMerger class. PyPDF2 is no longer maintained. The
people who worked on it moved the project to pypdf. In pypdf, the
supported way to join files is PdfWriter.append(). This file does not
import PyPDF2.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

try:
    from pypdf import PasswordType, PdfReader, PdfWriter
    from pypdf.errors import (
        EmptyFileError,
        FileNotDecryptedError,
        PdfReadError,
        WrongPasswordError,
    )
except ImportError:
    print("The pypdf library is not installed.")
    print("From the project folder, run:")
    print("    .venv/bin/python -m pip install -r requirements.txt")
    raise SystemExit(1)


# Shown in the About box and written into the Mac app bundle.
APP_VERSION = "1.2"

# Used when the name box is left blank.
DEFAULT_MERGED_NAME = "merged_pdfs.pdf"

# Long enough for a normal title, short enough that a timestamp prefix
# still fits in the 255-character file-name limit used by macOS.
MAX_NAME_LENGTH = 180

# These characters are illegal in a Windows file name. A merged PDF may
# later be copied to a Windows PC, so the Mac build rejects them too.
DISALLOWED_CHARACTERS = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]

# Windows refuses to create a file with one of these names, even when
# ".pdf" is added. "CON.pdf" is a reserved name, for example.
WINDOWS_RESERVED_NAMES = [
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
]


class MergeError(Exception):
    """A merge problem we can explain in a sentence.

    Purpose:
        Separate "this PDF could not be merged" from unexpected bugs.
        The window shows MergeError text to the user.

    Inputs:
        The usual Exception text: a short explanation.

    Outputs:
        An exception object. Raising it stops the merge.

    Side effects:
        None until some other function raises it.
    """


def quiet_pypdf_warnings():
    """Hide routine warnings printed by pypdf.

    Purpose:
        pypdf warns about minor PDF quirks (odd annotations, odd page
        sizes) even when the pages still merge. Those lines make the
        terminal look like the merge failed. Real failures are raised
        as exceptions and shown in the window.

    Inputs:
        None.

    Outputs:
        None.

    Side effects:
        Sets the pypdf logger to ERROR for the rest of this run.
    """
    logging.getLogger("pypdf").setLevel(logging.ERROR)


# Run once, when this file is first imported.
quiet_pypdf_warnings()


def pdf_sort_key(path):
    """Return a file name in lowercase so sorting ignores capitals.

    Purpose:
        "Zebra.pdf" should come after "apple.pdf". Comparing the
        original names would use the character code, and capital letters
        sort before lowercase letters.

    Inputs:
        path: a pathlib.Path.

    Outputs:
        A string such as "zebra.pdf".

    Side effects:
        None.
    """
    return path.name.lower()


def list_pdfs(folder):
    """Find the PDF files that sit directly inside one folder.

    Purpose:
        Build the list the checklist window shows. The merge follows
        this order: A to Z, ignoring capital letters. merge_pdfs() does
        not sort again. If the window passes a shorter list (the user
        unchecked some files), that shorter list is the merge order.

    Inputs:
        folder: a pathlib.Path pointing at a directory.

    Outputs:
        A list of pathlib.Path objects. The list may be empty.
        Subfolders are not searched. Hidden files (names that start
        with a dot) are left out. Mac folders sometimes contain hidden
        sidecar files that are not documents the user meant to merge.

    Side effects:
        Reads the folder's directory listing. Does not open the PDFs.
        Raises OSError if the folder cannot be read.
    """
    found = []

    for entry in folder.iterdir():
        if not entry.is_file():
            continue
        if entry.name.startswith("."):
            continue
        if entry.suffix.lower() != ".pdf":
            continue
        found.append(entry)

    found.sort(key=pdf_sort_key)
    return found


def chosen_files(paths, checked_flags):
    """Keep the files whose checklist boxes are turned on.

    Purpose:
        The checklist starts with every box checked. This function
        applies the user's edits without changing the order of the list.

    Inputs:
        paths: list of pathlib.Path, in the order shown on screen.
        checked_flags: list of True or False, one per path. True means
            the box is checked.

    Outputs:
        A new list containing only the checked paths, in the same order.

    Side effects:
        None. Raises MergeError if the two lists have different lengths,
        because that would be a bug in the window code.
    """
    if len(paths) != len(checked_flags):
        raise MergeError("The checklist sent a mismatched list of checkboxes.")

    chosen = []
    index = 0
    while index < len(paths):
        if checked_flags[index]:
            chosen.append(paths[index])
        index = index + 1
    return chosen


def selection_problem(files):
    """Explain why a selection cannot be merged, or say that it can.

    Purpose:
        Merging one PDF with nothing else is not a merge. The button
        and the checklist both ask this before they continue.

    Inputs:
        files: a list of paths the user wants to include.

    Outputs:
        None when there are two or more files.
        A short string when there are fewer than two.

    Side effects:
        None.
    """
    count = len(files)
    if count >= 2:
        return None
    if count == 1:
        return "Select at least two PDF files. Only one is checked."
    return "Select at least two PDF files."


def strip_typed_name(typed_text):
    """Remove spaces from the ends of the name the user typed.

    Purpose:
        A name like "  notes  " should be treated as "notes".
        An empty box, or a box that is only spaces, means the user
        wants the default name.

    Inputs:
        typed_text: a string, or None.

    Outputs:
        DEFAULT_MERGED_NAME when there is nothing to keep.
        Otherwise the typed name without leading or trailing spaces.

    Side effects:
        None.
    """
    if typed_text is None:
        return DEFAULT_MERGED_NAME

    cleaned = str(typed_text).strip()
    if cleaned == "":
        return DEFAULT_MERGED_NAME
    return cleaned


def ensure_pdf_extension(filename):
    """Add ".pdf" when the name does not already end with it.

    Purpose:
        The output of a merge is always a PDF. Users often type "notes"
        and expect "notes.pdf". If they already typed the extension,
        leave their capital letters alone ("Notes.PDF" stays "Notes.PDF").

    Inputs:
        filename: a non-empty string. Call strip_typed_name() first.

    Outputs:
        A string that ends with .pdf in some mix of capital letters.

    Side effects:
        None.
    """
    if filename.lower().endswith(".pdf"):
        return filename
    return filename + ".pdf"


def name_without_extension(filename):
    """Return the part of the name that comes before the last dot.

    Purpose:
        Windows reserved names are checked on the part before the
        extension. "CON.pdf" is reserved because "CON" is reserved.

    Inputs:
        filename: a string.

    Outputs:
        A string. "notes.pdf" returns "notes". "notes" returns "notes".

    Side effects:
        None.
    """
    dot_index = filename.rfind(".")
    if dot_index <= 0:
        return filename
    return filename[:dot_index]


def validate_filename(filename):
    """Decide whether a file name is safe to create on macOS and Windows.

    Purpose:
        Catch names the operating system will reject, before we try to
        write the file. This does not check whether the name is already
        taken. choose_output_path() does that.

    Inputs:
        filename: the name only, not a folder path. It should already
            be stripped. Example: "notes.pdf".

    Outputs:
        A tuple of two items.
        (True, "Filename is valid.") when the name is usable.
        (False, "a short reason") when it is not.

    Side effects:
        None.
    """
    if filename is None or str(filename).strip() == "":
        return False, "Filename cannot be empty."

    if filename.endswith(" ") or filename.endswith("."):
        return False, "Filename cannot end with a space or a dot."

    if filename == "." or filename == "..":
        return False, "That name is reserved by the file system."

    for character in DISALLOWED_CHARACTERS:
        if character in filename:
            return False, "Filename contains a character that is not allowed: '" + character + "'"

    if "\n" in filename or "\r" in filename:
        return False, "Filename cannot contain a line break."

    if len(filename) > MAX_NAME_LENGTH:
        return False, "Filename is too long. Use " + str(MAX_NAME_LENGTH) + " characters or fewer."

    bare_name = name_without_extension(filename)
    if bare_name.strip() == "":
        return False, "Type a name before the .pdf extension."

    reserved_check = bare_name.upper()
    if reserved_check in WINDOWS_RESERVED_NAMES:
        return False, "Filename is a Windows reserved name."

    return True, "Filename is valid."


def prepare_output_name(typed_text):
    """Turn the text box into a legal PDF file name.

    Purpose:
        This is the function the window should call. It applies the
        default name, strips spaces, checks the characters, and adds
        ".pdf" when needed.

    Inputs:
        typed_text: whatever is in the name box. May be empty or None.

    Outputs:
        A tuple of two items.
        Success: (True, "notes.pdf")
        Failure: (False, "Filename contains a character that is not allowed: ':'")
        On failure the second item is a sentence for the status line.

    Side effects:
        None. Does not look at the disk. A legal name can still be
        taken; choose_output_path() handles that at merge time.
    """
    cleaned = strip_typed_name(typed_text)
    is_ok, reason = validate_filename(cleaned)
    if not is_ok:
        return False, reason

    with_extension = ensure_pdf_extension(cleaned)
    is_ok, reason = validate_filename(with_extension)
    if not is_ok:
        return False, reason

    return True, with_extension


def names_match(left_name, right_name):
    """Return True when two file names would collide on a Mac.

    Purpose:
        macOS and Windows usually treat "Report.pdf" and "report.pdf"
        as the same file. We always compare without caring about capital
        letters, including when the tests run on Linux. That way a name
        that is safe on the test machine is also safe on Bryan's Mac.

    Inputs:
        left_name: a file name, not a full path.
        right_name: a file name, not a full path.

    Outputs:
        True or False.

    Side effects:
        None.
    """
    return left_name.casefold() == right_name.casefold()


def output_name_is_taken(folder, file_name):
    """Return True if the folder already has a file with this name.

    Purpose:
        Avoid overwriting a PDF the user already has. The check looks
        at every file in the folder, not only PDFs, because the output
        name might match a non-PDF too.

    Inputs:
        folder: pathlib.Path of the destination folder.
        file_name: the file name we would like to create.

    Outputs:
        True when a colliding file is present. False when the name is free.

    Side effects:
        Reads the directory listing. Raises OSError if the folder cannot
        be read.
    """
    for entry in folder.iterdir():
        if not entry.is_file():
            continue
        if names_match(entry.name, file_name):
            return True
    return False


def timestamp_prefix():
    """Return the current local time as a compact prefix for a file name.

    Purpose:
        When "merged_pdfs.pdf" already exists, the new file is named
        like "261101143005_merged_pdfs.pdf". The digits are year, month,
        day, hour, minute, second. 261101143005 means 2026-11-01 14:30:05.

    Inputs:
        None.

    Outputs:
        A 12-character string of digits.

    Side effects:
        Reads the computer's clock.
    """
    return datetime.now().strftime("%y%m%d%H%M%S")


def choose_output_path(folder, requested_name):
    """Pick a full path that will not overwrite an existing file.

    Purpose:
        Put the merged PDF in the same folder as the source PDFs.
        If the requested name is already used, add the date and time
        in front of it. An older merge result stays on disk.

    Inputs:
        folder: pathlib.Path of the folder the user selected.
        requested_name: a file name that already ends with .pdf.
            prepare_output_name() is the right way to build this.

    Outputs:
        A pathlib.Path such as folder / "merged_pdfs.pdf", or
        folder / "261101143005_merged_pdfs.pdf" when the plain name is taken.
        If that stamped name is also taken, a counter is added:
        "261101143005_2_merged_pdfs.pdf".

    Side effects:
        Reads the directory listing. Does not create the file.
        Raises MergeError if it cannot find a free name. That is rare.
        Raises OSError if the folder cannot be read.
    """
    if not output_name_is_taken(folder, requested_name):
        return folder / requested_name

    stamp = timestamp_prefix()
    stamped_name = stamp + "_" + requested_name
    if not output_name_is_taken(folder, stamped_name):
        return folder / stamped_name

    # Same second, and the stamped name is already there. Keep looking.
    counter = 2
    while counter <= 100:
        numbered_name = stamp + "_" + str(counter) + "_" + requested_name
        if not output_name_is_taken(folder, numbered_name):
            return folder / numbered_name
        counter = counter + 1

    raise MergeError("Could not find a free file name in that folder.")


def explain_pdf_problem(source, error):
    """Turn a pypdf exception into a sentence for the status line.

    Purpose:
        pypdf's own messages name internal classes. The window should
        say which file failed and what the user can do.

    Inputs:
        source: pathlib.Path of the PDF that failed.
        error: the exception pypdf raised.

    Outputs:
        A string.

    Side effects:
        None.
    """
    name = source.name

    if isinstance(error, (FileNotDecryptedError, WrongPasswordError)):
        return (
            '"' + name + '" is password-protected. '
            "MergePDF does not ask for passwords. "
            "Open the file, save a copy without a password, and try again."
        )

    if isinstance(error, EmptyFileError):
        return '"' + name + '" is empty, so it cannot be merged.'

    if isinstance(error, PdfReadError):
        return (
            '"' + name + '" could not be read as a PDF. '
            "It may be damaged. Details: " + str(error)
        )

    return '"' + name + '" could not be merged. Details: ' + str(error)


def open_source_pdf(source):
    """Open one PDF and make sure it has pages we can copy.

    Purpose:
        Check the file before any pages are added to the output.
        If this function raises, merge_pdfs() has not written a file yet.

    Inputs:
        source: pathlib.Path of one PDF.

    Outputs:
        A pypdf PdfReader for that file.

    Side effects:
        Reads the file from disk.
        Raises MergeError when the file is missing, empty, damaged,
        or locked with a password.

        Some PDFs are marked "encrypted" but open with a blank password
        (they only carry printing restrictions). This function tries the
        blank password once. It does not guess real passwords.
    """
    if not source.is_file():
        raise MergeError('"' + source.name + '" is not a file that can be read.')

    try:
        reader = PdfReader(str(source), strict=False)
    except Exception as error:
        raise MergeError(explain_pdf_problem(source, error)) from error

    if reader.is_encrypted:
        opened_with = reader.decrypt("")
        if opened_with == PasswordType.NOT_DECRYPTED:
            raise MergeError(explain_pdf_problem(source, FileNotDecryptedError("password required")))

    page_count = len(reader.pages)
    if page_count == 0:
        raise MergeError('"' + source.name + '" has no pages, so it cannot be merged.')

    return reader


def append_one_pdf(writer, source):
    """Copy every page from one PDF onto the end of the writer.

    Purpose:
        Add the document, keep any bookmarks it already has, and add one
        bookmark named after the file so the merged PDF can be navigated.

    Inputs:
        writer: an open pypdf PdfWriter.
        source: pathlib.Path of one PDF that open_source_pdf() can read.

    Outputs:
        None.

    Side effects:
        Reads the source file.
        Adds pages and bookmarks to writer.
        Raises MergeError if the file cannot be copied.
    """
    reader = open_source_pdf(source)

    try:
        # outline_item is the bookmark title shown in Preview.
        # import_outline=True copies bookmarks that already exist in this file
        # and nests them under that new bookmark.
        writer.append(reader, outline_item=source.name, import_outline=True)
    except StopIteration:
        # pypdf raises this if a bookmark is requested for a file with no pages.
        # open_source_pdf() already rejects empty files. This is a backstop.
        raise MergeError('"' + source.name + '" has no pages, so it cannot be merged.')
    except Exception as error:
        raise MergeError(explain_pdf_problem(source, error)) from error


def remove_partial_file(partial_path):
    """Delete the temporary file if it is still on disk.

    Purpose:
        A failed merge should not leave "name.pdf.partial" behind.
        After a successful save, the temporary file has already been
        renamed, so there is nothing to delete.

    Inputs:
        partial_path: pathlib.Path of the temporary file.

    Outputs:
        None.

    Side effects:
        Deletes the temporary file when it exists.
        If the delete itself fails, the error is ignored so it does not
        hide the original merge error. The status line reports that error.
    """
    if not partial_path.exists():
        return

    try:
        partial_path.unlink()
    except OSError:
        return


def write_pdf_safely(writer, output_path):
    """Write the merged PDF without leaving a half-written final file.

    Purpose:
        Write to a temporary file in the same folder, then rename it to
        the final name. A crash during the write leaves the temporary
        file, which this function deletes, and does not replace a good
        PDF with a broken one.

    Inputs:
        writer: a PdfWriter that already holds every page.
        output_path: pathlib.Path of the final PDF. The parent folder
            must exist. The caller should already have chosen a name
            that is not in use.

    Outputs:
        None. On success the final file exists at output_path.

    Side effects:
        Creates a file ending in ".pdf.partial", then renames it.
        Raises MergeError if the save fails or if the final name appears
        on disk while the write is happening. The temporary file is
        removed in both of those cases.
    """
    partial_path = Path(str(output_path) + ".partial")
    remove_partial_file(partial_path)

    try:
        # "wb" means write bytes. PDF files are binary, not text.
        with partial_path.open("wb") as partial_file:
            writer.write(partial_file)

        if output_path.exists():
            raise MergeError(
                'A file named "' + output_path.name + '" appeared while the merge was running. '
                "Nothing was overwritten. Click Merge PDFs again."
            )

        partial_path.replace(output_path)
    except MergeError:
        raise
    except Exception as error:
        raise MergeError("Could not save the merged PDF. Details: " + str(error)) from error
    finally:
        remove_partial_file(partial_path)


def same_file(left_path, right_path):
    """Return True when two paths point at the same place on disk.

    Purpose:
        The merged file must not be one of the files we are reading.
        Overwriting a source while pypdf is reading it would damage it.

    Inputs:
        left_path: a pathlib.Path.
        right_path: a pathlib.Path.

    Outputs:
        True or False. Missing files are compared as resolved paths,
        so a not-yet-created output does not count as an existing source.

    Side effects:
        None. resolve() does not create anything. strict=False means a
        missing path does not raise.
    """
    left_resolved = Path(left_path).resolve()
    right_resolved = Path(right_path).resolve()
    return left_resolved == right_resolved


def merge_pdfs(source_files, output_path):
    """Combine PDF files into one new PDF, in the order given.

    Purpose:
        Read each source and write one PDF that contains every page.
        The first file's pages come first, then the next file, and so on.

    Inputs:
        source_files: a list of at least two pathlib.Path objects.
            The order of this list is the order of the pages.
        output_path: where the new PDF should be saved. Its parent folder
            must already exist.

    Outputs:
        None.

    Side effects:
        Reads every source file.
        On success, creates the file at output_path.
        On failure, raises MergeError and does not leave the final file
        or the temporary ".pdf.partial" file behind.
        Does not delete or change the source PDFs.
        Does not upload anything.

        Each source file becomes a bookmark in the merged PDF. Bookmarks
        that were already inside a source file are kept under that bookmark.
    """
    problem = selection_problem(source_files)
    if problem is not None:
        raise MergeError(problem)

    for source in source_files:
        if same_file(source, output_path):
            raise MergeError(
                '"' + source.name + '" is the same file as the output. '
                "Choose a different name so the original is not overwritten."
            )

    writer = PdfWriter()
    try:
        # Read every source before creating the output file. A bad file
        # then stops the merge with nothing new written to the folder.
        for source in source_files:
            append_one_pdf(writer, source)

        write_pdf_safely(writer, output_path)
    finally:
        # Close the writer even when a source file fails. This releases
        # the pages it was holding in memory.
        writer.close()


def describe_platform_opener():
    """Return the program this computer uses to open a PDF, for messages.

    Purpose:
        Help text and errors can name the opener without starting it.

    Inputs:
        None. Uses sys.platform.

    Outputs:
        "Preview" on macOS, "the default PDF app" on Windows,
        "the default PDF app" on other systems.

    Side effects:
        None.
    """
    if sys.platform == "darwin":
        return "Preview"
    return "the default PDF app"
