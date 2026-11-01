"""Tests for merge_logic.py. These tests do not open a window.

Run them from the project folder:

    .venv/bin/python -m unittest discover -s tests -t . -v
"""

import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from merge_logic import (
    DEFAULT_MERGED_NAME,
    MergeError,
    choose_output_path,
    chosen_files,
    ensure_pdf_extension,
    list_pdfs,
    merge_pdfs,
    move_down,
    move_to_bottom,
    move_to_top,
    move_up,
    prepare_output_name,
    selection_problem,
    validate_filename,
)


def write_blank_pdf(folder, name, page_widths):
    """Create a simple PDF used only by tests.

    Purpose:
        Give merge_pdfs real files without checking sample PDFs into git.
        Each page has a different width so a test can see which file's
        pages came first.

    Inputs:
        folder: pathlib.Path of the folder that should hold the file.
        name: file name, for example "first.pdf".
        page_widths: list of page widths in points. One page is created
            per width. Every page is 100 points tall.

    Outputs:
        The pathlib.Path of the new PDF.

    Side effects:
        Writes one PDF into folder.
    """
    writer = PdfWriter()
    for width in page_widths:
        writer.add_blank_page(width=width, height=100)

    output = folder / name
    with output.open("wb") as handle:
        writer.write(handle)
    writer.close()
    return output


def write_encrypted_pdf(folder, name, password):
    """Create a password-protected one-page PDF.

    Purpose:
        Confirm that merge_pdfs refuses a locked file and names it.

    Inputs:
        folder: pathlib.Path.
        name: file name.
        password: the user password to set.

    Outputs:
        The pathlib.Path of the new PDF.

    Side effects:
        Writes one encrypted PDF into folder.
    """
    writer = PdfWriter()
    writer.add_blank_page(width=80, height=80)
    writer.encrypt(password)

    output = folder / name
    with output.open("wb") as handle:
        writer.write(handle)
    writer.close()
    return output


def page_widths(path):
    """Return the page widths of a PDF, as plain numbers, in order.

    Purpose:
        Tests compare widths to prove the merge kept the requested order.

    Inputs:
        path: pathlib.Path of a PDF.

    Outputs:
        A list of numbers, one per page.

    Side effects:
        Reads the PDF.
    """
    reader = PdfReader(str(path))
    widths = []
    for page in reader.pages:
        widths.append(float(page.mediabox.width))
    return widths


class MergeLogicTests(unittest.TestCase):
    """Checks for listing, naming, and merging."""

    def setUp(self):
        """Create an empty temporary folder for one test.

        Purpose:
            Keep test files away from the project and from each other.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Creates a temporary directory and stores its path on self.folder.
        """
        self.temp_dir = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp_dir.name)

    def tearDown(self):
        """Delete the temporary folder created in setUp.

        Purpose:
            Leave the disk clean after the test.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Deletes the temporary directory and the files inside it.
        """
        self.temp_dir.cleanup()

    def test_list_pdfs_is_case_insensitive_and_skips_other_files(self):
        """PDFs are found regardless of capital letters, and sorted A to Z.

        Purpose:
            .PDF and .pdf both count. Text files, subfolders, and hidden
            files do not. Order ignores capital letters.

        Inputs:
            None. The test creates its own files.

        Outputs:
            None. Failures are unittest assertions.

        Side effects:
            Writes files in the temporary folder.
        """
        write_blank_pdf(self.folder, "Zebra.PDF", [10])
        write_blank_pdf(self.folder, "apple.pdf", [10])
        write_blank_pdf(self.folder, "Middle.pdf", [10])
        (self.folder / "notes.txt").write_text("not a pdf", encoding="utf-8")
        (self.folder / ".hidden.pdf").write_bytes(b"%PDF-hidden")
        subfolder = self.folder / "nested"
        subfolder.mkdir()
        write_blank_pdf(subfolder, "inside.pdf", [10])

        found = list_pdfs(self.folder)
        names = []
        for path in found:
            names.append(path.name)

        self.assertEqual(names, ["apple.pdf", "Middle.pdf", "Zebra.PDF"])

    def test_chosen_files_keeps_checked_items_in_order(self):
        """Keep the checked files and drop the rest.

        Purpose:
            Unchecked files drop out. The remaining files stay in list order.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            None on disk.
        """
        paths = [
            Path("a.pdf"),
            Path("b.pdf"),
            Path("c.pdf"),
        ]
        chosen = chosen_files(paths, [True, False, True])
        self.assertEqual(chosen, [Path("a.pdf"), Path("c.pdf")])

    def test_move_up_and_move_down_swap_neighbors(self):
        """Move up and Move down trade places with the next file.

        Purpose:
            The highlighted file moves one step. The original list
            stays as it was, so the checklist can compare before and after.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            None on disk.
        """
        items = ["a", "b", "c"]
        moved_down, index = move_down(items, 0)
        self.assertEqual(items, ["a", "b", "c"])
        self.assertEqual(moved_down, ["b", "a", "c"])
        self.assertEqual(index, 1)

        moved_up, index = move_up(moved_down, 1)
        self.assertEqual(moved_up, ["a", "b", "c"])
        self.assertEqual(index, 0)

    def test_move_up_at_the_top_and_move_down_at_the_bottom_do_not_change_order(self):
        """The first file cannot move up, and the last file cannot move down.

        Purpose:
            The buttons at the ends of the list must not scramble the order.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            None.
        """
        items = ["a", "b"]
        moved, index = move_up(items, 0)
        self.assertEqual(moved, ["a", "b"])
        self.assertEqual(index, 0)

        moved, index = move_down(items, 1)
        self.assertEqual(moved, ["a", "b"])
        self.assertEqual(index, 1)

    def test_move_to_top_and_move_to_bottom(self):
        """Move to top and Move to bottom put the file at an end of the list.

        Purpose:
            A file in the middle can jump to the start or the end
            without the user clicking Move up several times.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            None.
        """
        items = ["a", "b", "c", "d"]
        moved, index = move_to_top(items, 2)
        self.assertEqual(moved, ["c", "a", "b", "d"])
        self.assertEqual(index, 0)

        moved, index = move_to_bottom(items, 1)
        self.assertEqual(moved, ["a", "c", "d", "b"])
        self.assertEqual(index, 3)

    def test_chosen_files_follows_the_reordered_list(self):
        """After a move, checked files stay in the new order.

        Purpose:
            The merge must use the checklist order, not A to Z.
            Unchecked files drop out and do not pull their neighbors
            back into alphabetical order.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            None.
        """
        paths = [Path("a.pdf"), Path("b.pdf"), Path("c.pdf")]
        reordered, _index = move_to_bottom(paths, 0)
        chosen = chosen_files(reordered, [True, False, True])
        self.assertEqual(chosen, [Path("b.pdf"), Path("a.pdf")])

    def test_selection_problem_requires_two_files(self):
        """Require two files before a merge is allowed.

        Purpose:
            Zero or one file is a problem. Two files is fine.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            None.
        """
        self.assertIsNone(selection_problem([Path("a.pdf"), Path("b.pdf")]))
        self.assertIn("Only one", selection_problem([Path("a.pdf")]))
        self.assertIn("at least two", selection_problem([]))

    def test_prepare_output_name_uses_the_default_when_blank(self):
        """Use the default file name when the box is blank.

        Purpose:
            An empty box becomes merged_pdfs.pdf.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            None.
        """
        is_ok, name = prepare_output_name("   ")
        self.assertTrue(is_ok)
        self.assertEqual(name, DEFAULT_MERGED_NAME)

        is_ok, name = prepare_output_name(None)
        self.assertTrue(is_ok)
        self.assertEqual(name, DEFAULT_MERGED_NAME)

    def test_prepare_output_name_adds_extension_and_rejects_bad_characters(self):
        """Add .pdf to a legal name and reject a colon.

        Purpose:
            Legal names gain .pdf. A colon is rejected.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            None.
        """
        is_ok, name = prepare_output_name("  notes  ")
        self.assertTrue(is_ok)
        self.assertEqual(name, "notes.pdf")

        is_ok, name = prepare_output_name("Notes.PDF")
        self.assertTrue(is_ok)
        self.assertEqual(name, "Notes.PDF")

        is_ok, reason = prepare_output_name("bad:name")
        self.assertFalse(is_ok)
        self.assertIn(":", reason)

        is_ok, reason = validate_filename("CON.pdf")
        self.assertFalse(is_ok)
        self.assertIn("reserved", reason)

    def test_ensure_pdf_extension_leaves_an_existing_extension_alone(self):
        """Leave an extension the user already typed unchanged.

        Purpose:
            Do not change the capital letters in an extension the user typed.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            None.
        """
        self.assertEqual(ensure_pdf_extension("notes"), "notes.pdf")
        self.assertEqual(ensure_pdf_extension("notes.PDF"), "notes.PDF")

    def test_choose_output_path_adds_a_timestamp_when_the_name_is_taken(self):
        """An existing file is kept. The new name starts with digits and an underscore.

        Purpose:
            "Report.pdf" and "report.pdf" count as the same name, because
            a Mac treats them as the same file.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Writes a placeholder file in the temporary folder.
        """
        (self.folder / "Report.pdf").write_bytes(b"keep me")

        chosen = choose_output_path(self.folder, "report.pdf")

        self.assertNotEqual(chosen.name.casefold(), "report.pdf")
        self.assertTrue(chosen.name.endswith("_report.pdf"))
        self.assertEqual((self.folder / "Report.pdf").read_bytes(), b"keep me")

    def test_merge_keeps_page_order_and_adds_a_bookmark_per_file(self):
        """Pages follow the list order, and each file name becomes a bookmark.

        Purpose:
            merge_pdfs must not re-sort. The widths below are the proof:
            the second file is passed first, so its wide page comes first.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Writes source PDFs and one merged PDF in the temporary folder.
        """
        second = write_blank_pdf(self.folder, "second.pdf", [300])
        first = write_blank_pdf(self.folder, "first.pdf", [200, 210])
        output = self.folder / "joined.pdf"

        merge_pdfs([second, first], output)

        self.assertEqual(page_widths(output), [300.0, 200.0, 210.0])

        reader = PdfReader(str(output))
        titles = []
        for item in reader.outline:
            titles.append(str(item["/Title"]))
        self.assertEqual(titles, ["second.pdf", "first.pdf"])

    def test_merge_refuses_a_password_and_leaves_no_partial_file(self):
        """Stop when a PDF is locked, and do not leave a partial file.

        Purpose:
            A locked PDF stops the merge. No output file and no .partial file remain.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Writes one good PDF and one encrypted PDF, then attempts a merge.
        """
        good = write_blank_pdf(self.folder, "good.pdf", [100, 110])
        locked = write_encrypted_pdf(self.folder, "secret.pdf", "secret")
        output = self.folder / "joined.pdf"

        with self.assertRaises(MergeError) as caught:
            merge_pdfs([good, locked], output)

        message = str(caught.exception)
        self.assertIn("secret.pdf", message)
        self.assertIn("password", message.lower())
        self.assertFalse(output.exists())
        self.assertFalse(Path(str(output) + ".partial").exists())

    def test_merge_refuses_a_pdf_with_no_pages(self):
        """Stop when a PDF has no pages.

        Purpose:
            A PDF that opens but has zero pages stops the merge.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Writes one normal PDF, one empty PDF, and attempts a merge.
        """
        good = write_blank_pdf(self.folder, "good.pdf", [100])
        empty = self.folder / "empty.pdf"
        writer = PdfWriter()
        with empty.open("wb") as handle:
            writer.write(handle)
        writer.close()
        output = self.folder / "joined.pdf"

        with self.assertRaises(MergeError) as caught:
            merge_pdfs([good, empty], output)

        self.assertIn("empty.pdf", str(caught.exception))
        self.assertIn("no pages", str(caught.exception))
        self.assertFalse(output.exists())

    def test_merge_refuses_a_file_that_is_not_a_pdf(self):
        """Stop when a file is not a real PDF.

        Purpose:
            A .pdf name with garbage contents is reported, and nothing is saved.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Writes one real PDF and one fake PDF, then attempts a merge.
        """
        good = write_blank_pdf(self.folder, "good.pdf", [120])
        fake = self.folder / "fake.pdf"
        fake.write_bytes(b"this is not a pdf")
        output = self.folder / "joined.pdf"

        with self.assertRaises(MergeError) as caught:
            merge_pdfs([good, fake], output)

        self.assertIn("fake.pdf", str(caught.exception))
        self.assertFalse(output.exists())

    def test_merge_does_not_overwrite_an_existing_file_when_the_caller_picks_a_new_name(self):
        """Write the merge beside an older file instead of replacing it.

        Purpose:
            choose_output_path plus merge_pdfs leaves the older bytes untouched.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Writes source PDFs, a placeholder output name, and a new merge.
        """
        existing = self.folder / "merged_pdfs.pdf"
        existing.write_bytes(b"keep me")
        first = write_blank_pdf(self.folder, "a.pdf", [100])
        second = write_blank_pdf(self.folder, "b.pdf", [200])

        output = choose_output_path(self.folder, "merged_pdfs.pdf")
        merge_pdfs([first, second], output)

        self.assertEqual(existing.read_bytes(), b"keep me")
        self.assertTrue(output.is_file())
        self.assertEqual(len(page_widths(output)), 2)


if __name__ == "__main__":
    unittest.main()
