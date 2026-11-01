"""Tests for the MergePDF window that do not need a person to click.

Run them from the project folder, on a machine where Tk can open a display:

    .venv/bin/python -m unittest discover -s tests -t . -v

These tests build the window, click the code behind the buttons, and
close the window. They do not cover the system folder dialog. That
dialog has to be tried by hand on a Mac.
"""

import tempfile
import unittest
from pathlib import Path

from pypdf import PdfWriter

from mergepdf import MergePDFApp


def write_blank_pdf(folder, name, page_widths):
    """Create a one-or-more-page PDF for the window test.

    Purpose:
        The window test needs real files so Merge PDFs can succeed.

    Inputs:
        folder: pathlib.Path.
        name: file name.
        page_widths: list of page widths in points.

    Outputs:
        The pathlib.Path of the new PDF.

    Side effects:
        Writes one PDF.
    """
    writer = PdfWriter()
    for width in page_widths:
        writer.add_blank_page(width=width, height=100)

    output = folder / name
    with output.open("wb") as handle:
        writer.write(handle)
    writer.close()
    return output


class WindowTests(unittest.TestCase):
    """One window, shared by the tests, then destroyed."""

    @classmethod
    def setUpClass(cls):
        """Open the MergePDF window once for this class.

        Purpose:
            ttkbootstrap allows one main window at a time. Building it
            once keeps the tests from fighting over that window.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Creates a Tk window. It is not entered into mainloop.
            Creates a temporary folder for the merge test.
        """
        cls.app = MergePDFApp()
        cls.app.root.update()
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.folder = Path(cls.temp_dir.name)

    @classmethod
    def tearDownClass(cls):
        """Close the window and delete the temporary folder.

        Purpose:
            Leave no window and no test files behind.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Destroys the Tk window and deletes the temporary folder.
        """
        cls.temp_dir.cleanup()
        cls.app.root.destroy()

    def setUp(self):
        """Put the form back to its starting state before each test.

        Purpose:
            A test that types a name or runs a merge should not affect
            the next test.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Clears the form the same way the Reset button does.
        """
        self.app.reset_form()

    def test_window_title_and_merge_starts_disabled(self):
        """Open with Merge turned off until the user confirms files.

        Purpose:
            The window is titled MergePDF and Merge is off until files are chosen.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Reads widget state.
        """
        self.assertEqual(self.app.root.title(), "MergePDF")
        self.assertEqual(str(self.app.merge_button.cget("state")), "disabled")
        self.assertFalse(self.app.open_button.winfo_ismapped())
        self.assertIn("No folder", self.app.message_folder.cget("text"))

    def test_blank_name_becomes_the_default(self):
        """Fill in the default name when Submit is clicked on a blank box.

        Purpose:
            Submit name with an empty box fills in merged_pdfs.pdf.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Changes the name box and the step 2 status line.
        """
        self.app.file_name_var.set("   ")
        self.app.select_name()
        self.assertEqual(self.app.file_name_var.get(), "merged_pdfs.pdf")
        self.assertIn("merged_pdfs.pdf", self.app.message_name.cget("text"))

    def test_bad_name_is_explained_and_left_in_the_box(self):
        """Reject a colon and keep the typed text for editing.

        Purpose:
            A colon is rejected, and the typed text stays so it can be fixed.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Updates the step 2 status line.
        """
        self.app.file_name_var.set("bad:name")
        self.app.select_name()
        self.assertEqual(self.app.file_name_var.get(), "bad:name")
        self.assertIn("not allowed", self.app.message_name.cget("text"))

    def test_merge_without_files_explains_why(self):
        """Explain why Merge did nothing when no files are selected.

        Purpose:
            Clicking Merge with nothing selected does not write a file.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Updates the step 3 status line.
        """
        self.app.merge_clicked()
        self.assertIn("at least two", self.app.message_merge.cget("text"))

    def test_merge_clicked_writes_the_pdf_and_shows_the_open_button(self):
        """The Merge button calls the same merge used by the logic tests.

        Purpose:
            Confirm the window passes the folder, the file list, and the
            name through to merge_pdfs and then offers to open the result.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Writes two source PDFs and one merged PDF in the temporary folder.
            Updates the form.
        """
        first = write_blank_pdf(self.folder, "a.pdf", [100])
        second = write_blank_pdf(self.folder, "b.pdf", [200])
        self.app.folder = self.folder
        self.app.file_list = [first, second]
        self.app.file_name_var.set("joined")
        self.app.update_merge_button()

        self.app.merge_clicked()

        output = self.folder / "joined.pdf"
        self.assertTrue(output.is_file())
        self.assertEqual(self.app.last_output, output)
        self.assertIn("Successfully merged 2", self.app.message_merge.cget("text"))
        self.assertTrue(self.app.open_button.winfo_ismapped())
        self.assertEqual(str(self.app.merge_button.cget("state")), "normal")


if __name__ == "__main__":
    unittest.main()
