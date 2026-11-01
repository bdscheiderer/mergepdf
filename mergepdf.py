"""MergePDF window.

How to read this file
---------------------
1. main(), at the bottom, starts the program.
2. MergePDFApp builds the three-step window and reacts to buttons.
3. PdfChoiceDialog is the checklist that opens after a folder is chosen.
4. The merge itself is in merge_logic.py. This file collects choices
   and calls those functions. It does not upload PDFs.

How to run it
-------------
From the project folder, on a Mac:

    .venv/bin/python mergepdf.py

On Windows:

    .venv/Scripts/python mergepdf.py

The README has the full setup, including the Mac app and the Windows installer.
"""

import os
import subprocess
import sys
import warnings
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    from tkinter.font import nametofont
    import ttkbootstrap as tb
except ImportError as import_error:
    print("MergePDF could not start the window.")
    print("Details: " + str(import_error))
    print("")
    if sys.platform == "win32":
        print("Install Python from https://www.python.org/downloads/windows/")
        print("That installer includes Tk, which draws this window.")
        print("Leave tcl/tk and IDLE checked.")
        print("Then install the project libraries:")
        print(r"    .venv\Scripts\python -m pip install -r requirements.txt")
    else:
        print("Install Python from https://www.python.org/downloads/macos/")
        print("That installer includes Tk, which draws this window.")
        print("If you installed Python with Homebrew, also install the matching python-tk package.")
        print("Then install the project libraries:")
        print("    .venv/bin/python -m pip install -r requirements.txt")
    raise SystemExit(1)

from merge_logic import (
    APP_VERSION,
    MergeError,
    choose_output_path,
    chosen_files,
    describe_platform_opener,
    list_pdfs,
    merge_pdfs,
    move_down,
    move_to_bottom,
    move_to_top,
    move_up,
    prepare_output_name,
    selection_problem,
)


# The window is wide enough for the three instructions to wrap cleanly.
WINDOW_WIDTH = 720
WINDOW_HEIGHT = 640

# Status lines wrap inside the window instead of running off the edge.
MESSAGE_WRAP = 660

# The merge status sits beside the Open button, so it wraps in a narrower column.
MERGE_MESSAGE_WRAP = 330


def resource_path(relative_path):
    """Find a file that ships with the app.

    Purpose:
        Icons live in the assets folder next to this script while we are
        developing. PyInstaller copies those files into a temporary folder
        and stores that folder on sys._MEIPASS. This function checks the
        frozen folder first, then the folder that contains this script.
        The current working directory is not used, so the app can be
        started from any folder.

    Inputs:
        relative_path: a path such as "assets/icon.png".

    Outputs:
        A pathlib.Path. The file may still be missing. Callers check.

    Side effects:
        None.
    """
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root) / relative_path
    here = Path(__file__).resolve().parent
    return here / relative_path


def create_main_window():
    """Create the main window in the superhero colors this app has always used.

    Purpose:
        Open a ttkbootstrap window. The theme name "superhero" is the dark
        blue theme from the first version of the app. ttkbootstrap 2 still
        draws those colors, and it also prints a deprecation warning because
        the name comes from version 1 of the library. The warning is hidden
        here so a normal launch does not fill the Terminal with it.
        Any other warning or error is still shown.

        default_button="primary" keeps buttons that do not name a color on
        the blue action color. Buttons that pass bootstyle (Merge, Reset,
        Help, Exit) keep the colors named on those buttons.

    Inputs:
        None.

    Outputs:
        The ttkbootstrap main window.

    Side effects:
        Creates the Tk root window and loads the red m icon when the file
        is present.         Does not enter the event loop.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=".*legacy \\(pre-2.0\\) theme name.*",
            category=DeprecationWarning,
        )
        window = tb.Window(
            title="MergePDF",
            themename="superhero",
            iconphoto=window_icon_path(),
            default_button="primary",
        )
    return window


def window_icon_path():
    """Choose the icon file for the title bar on this operating system.

    Purpose:
        Windows title bars use the .ico file. macOS and Linux use the PNG.
        The Dock and Finder icon of a built Mac app comes from the .icns
        inside the .app, which PyInstaller sets. This function is only
        the icon shown while the window is open.

    Inputs:
        None.

    Outputs:
        A string path when the file exists.
        None when the icon file is missing. The app still runs.

    Side effects:
        None. Does not read the image, only checks that the path exists.
    """
    if sys.platform == "win32":
        icon_file = resource_path("assets/favicon.ico")
    else:
        icon_file = resource_path("assets/icon.png")

    if icon_file.is_file():
        return str(icon_file)
    return None


def place_window_on_screen(window, width, height):
    """Put a window in the middle of the screen.

    Purpose:
        A fixed-size window should open where the user can see it,
        not in the corner.

    Inputs:
        window: a Tk window that already exists.
        width: width in pixels.
        height: height in pixels.

    Outputs:
        None.

    Side effects:
        Changes the window's size and position.
    """
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x_position = (screen_width - width) // 2
    y_position = (screen_height - height) // 2
    window.geometry(str(width) + "x" + str(height) + "+" + str(x_position) + "+" + str(y_position))


def open_merged_pdf(filepath):
    """Ask the operating system to open a PDF in the default viewer.

    Purpose:
        After a merge, the user can look at the result without hunting
        for the file. On a Mac this opens Preview.

    Inputs:
        filepath: pathlib.Path of a PDF that already exists.

    Outputs:
        None.

    Side effects:
        Starts the default PDF app.
        Raises OSError when the system refuses to open the file.
    """
    path_text = str(filepath)

    if sys.platform == "darwin":
        # check=True raises CalledProcessError (an OSError) when open fails.
        subprocess.run(["open", path_text], check=True)
        return

    if sys.platform == "win32":
        # startfile exists only on Windows. It opens the file with the
        # app registered for .pdf.
        os.startfile(path_text)
        return

    subprocess.run(["xdg-open", path_text], check=True)


def show_about(parent):
    """Show the short About box.

    Purpose:
        Tell the user which version this is, and that the merge is local.

    Inputs:
        parent: the main window. The box stays in front of that window.

    Outputs:
        None.

    Side effects:
        Opens a modal message box. The call returns when the user closes it.
    """
    messagebox.showinfo(
        "About",
        "MergePDF " + APP_VERSION + "\n\n"
        "Combines PDF files on this computer.\n"
        "The files are not uploaded anywhere.\n\n"
        "Built with Python, pypdf, and ttkbootstrap.\n\n"
        "Copyright 2026 S2 Legacy, LLC\n"
        "Released under the MIT License.",
        parent=parent,
    )


def show_help(parent):
    """Show the step-by-step instructions.

    Purpose:
        Repeat the three steps that are on the main window, plus the
        rules that are easy to miss (order, passwords, existing names).

    Inputs:
        parent: the main window.

    Outputs:
        None.

    Side effects:
        Opens a modal message box.
    """
    messagebox.showinfo(
        "Instructions",
        "How to use MergePDF:\n\n"
        "1. Click Select folder and choose the folder\n"
        "   that contains your PDF files.\n\n"
        "2. A checklist opens. Every PDF starts checked.\n"
        "   The list starts in A to Z order.\n"
        "   Click a file name to highlight it, then use\n"
        "   Move up, Move down, Move to top, or Move to bottom.\n"
        "   The merge follows the list from top to bottom.\n"
        "   Uncheck any file you want to leave out.\n"
        "   At least two files must stay checked.\n\n"
        "3. Type a name for the merged file and click\n"
        "   Submit name. Leave the box blank to use\n"
        "   merged_pdfs.pdf.\n\n"
        "4. Click Merge PDFs. The new file is saved in\n"
        "   the same folder as the source PDFs.\n\n"
        "If that file name already exists, the date and\n"
        "time are added so the older file is kept.\n\n"
        "Password-protected PDFs are reported and skipped\n"
        "as a failed merge. Remove the password and try again.\n\n"
        "Reset clears the form. It does not delete files.",
        parent=parent,
    )


def show_contact(parent):
    """Show the contact box.

    Purpose:
        Give a place to send feedback. The address is the one already
        published for S2 Legacy.

    Inputs:
        parent: the main window.

    Outputs:
        None.

    Side effects:
        Opens a modal message box.
    """
    messagebox.showinfo(
        "Contact",
        "S2 Legacy, LLC\n\n"
        "For support or feedback:\n"
        "admin@s2legacy.com",
        parent=parent,
    )


class VerticalScroll:
    """Connect the mouse wheel to a scrollable canvas.

    Tk does not scroll a canvas when the wheel moves unless a program
    binds the wheel. This class holds those bindings. The dialog keeps
    a reference to the object. If nothing points at it, Python may
    delete it and the wheel will stop working.
    """

    def __init__(self, canvas):
        """Remember the canvas and watch for the pointer to enter it.

        Purpose:
            Start and stop wheel scrolling so only this list moves.

        Inputs:
            canvas: a tkinter Canvas.

        Outputs:
            None.

        Side effects:
            Binds enter and leave events on the canvas.
        """
        self.canvas = canvas
        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)

    def on_enter(self, _event):
        """Listen for the wheel while the pointer is over the list.

        Purpose:
            Checkboxes sit on top of the canvas. bind_all receives the
            wheel even when the pointer is over a checkbox, not only
            when it is over the canvas background.

        Inputs:
            _event: the Tk event. It is unused.

        Outputs:
            None.

        Side effects:
            Adds wheel bindings for the whole application until on_leave.
        """
        self.canvas.bind_all("<MouseWheel>", self.on_wheel)
        self.canvas.bind_all("<Button-4>", self.on_linux_up)
        self.canvas.bind_all("<Button-5>", self.on_linux_down)

    def on_leave(self, _event):
        """Stop listening when the pointer leaves the list.

        Purpose:
            The main window should not scroll because the checklist was
            open earlier.

        Inputs:
            _event: the Tk event. It is unused.

        Outputs:
            None.

        Side effects:
            Removes the wheel bindings added by on_enter.
        """
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def on_wheel(self, event):
        """Scroll one step up or down on macOS and Windows.

        Purpose:
            Move the checklist. Windows reports a large delta (often 120
            per notch). macOS often reports a small delta such as 1 or -1.
            The sign is what matters: positive means scroll up.

        Inputs:
            event: a Tk event with a delta attribute.

        Outputs:
            None.

        Side effects:
            Scrolls the canvas by one unit.
        """
        if event.delta > 0:
            steps = -1
        else:
            steps = 1
        self.canvas.yview_scroll(steps, "units")

    def on_linux_up(self, _event):
        """Scroll the checklist up on Linux.

        Purpose:
            Linux reports the mouse wheel as mouse button 4.

        Inputs:
            _event: the Tk event. It is unused.

        Outputs:
            None.

        Side effects:
            Scrolls the canvas up one unit.
        """
        self.canvas.yview_scroll(-1, "units")

    def on_linux_down(self, _event):
        """Scroll the checklist down on Linux.

        Purpose:
            Linux reports the mouse wheel as mouse button 5.

        Inputs:
            _event: the Tk event. It is unused.

        Outputs:
            None.

        Side effects:
            Scrolls the canvas down one unit.
        """
        self.canvas.yview_scroll(1, "units")


class PdfChoiceDialog:
    """The checklist of PDFs found in the chosen folder.

    Every box starts checked. The list starts in A to Z order.
    Clicking a file name highlights that row. The Move buttons change
    the order of the highlighted row. Confirm stores the checked paths
    on self.selected, in the order shown on screen, top to bottom.
    Cancel, or closing the window, leaves self.selected as None.
    The main window treats None as "do not change the previous choice".

    self.rows is a list of (path, checkbox variable) pairs.
    Index 0 is the file that will be merged first.
    The checkbox variable stays with its file when the row moves,
    so a file that was unchecked is still unchecked after a move.
    """

    def __init__(self, parent, pdf_files):
        """Build the checklist, but do not wait for the user yet.

        Purpose:
            Show one checkbox per PDF, in the order of pdf_files.
            The caller uses wait_window() so select_folder pauses
            until this window closes.

        Inputs:
            parent: the main MergePDF window.
            pdf_files: list of pathlib.Path. list_pdfs() sorts this
                A to Z before the dialog opens. The user can reorder it.

        Outputs:
            None. After the user finishes, read self.selected.

        Side effects:
            Creates a second window. Does not change the file list on
            the main window. That happens only if the caller accepts
            self.selected.
        """
        self.parent = parent
        self.selected = None
        # Each item is (path, BooleanVar). The BooleanVar objects must
        # stay on self. If we only created them inside a loop and did
        # not keep them, Tk would forget the checkmarks.
        self.rows = []
        for pdf_path in pdf_files:
            checked = tk.BooleanVar(value=True)
            self.rows.append((pdf_path, checked))

        # None means no row is highlighted. The first file starts
        # highlighted so the Move buttons have a clear target.
        if len(self.rows) > 0:
            self.selected_index = 0
        else:
            self.selected_index = None

        self.window = tb.Toplevel(
            master=parent,
            title="Select PDF files to merge",
            transient=parent,
            resizable=(False, False),
        )
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)
        self.window.bind("<Escape>", self.on_escape)

        introduction = tb.Label(
            self.window,
            text=(
                "Check the PDFs to include. Click a file name to highlight it, "
                "then use the Move buttons. The merge follows this list from "
                "top to bottom. It starts in A to Z order."
            ),
            wraplength=640,
        )
        introduction.pack(padx=20, pady=(15, 5), anchor="w")

        self._build_checklist()
        self._build_buttons()
        self.redraw_rows()
        self.update_move_buttons()
        self.show_highlight_status()

        # grab_set makes this window modal: the main window's Merge button
        # cannot run while the user is still choosing files.
        self.window.transient(self.parent)
        self.window.grab_set()
        self.window.update_idletasks()
        place_window_on_screen(
            self.window,
            self.window.winfo_width(),
            self.window.winfo_height(),
        )
        self.confirm_button.focus_set()

    def _build_checklist(self):
        """Add the scrolling list and the Move buttons beside it.

        Purpose:
            A folder may hold more PDFs than fit on screen. The canvas
            plus scrollbar lets the user reach all of them. The Move
            buttons sit beside the list so they stay visible while the
            user scrolls.

        Inputs:
            None. The files are already stored on self.rows.

        Outputs:
            None.

        Side effects:
            Creates the canvas, the scrollbar, and the four Move buttons.
            Does not draw the rows. redraw_rows() does that.
            Keeps self.scroller alive so the mouse wheel keeps working.
        """
        outer = tb.Frame(self.window)
        outer.pack(padx=20, pady=5, fill="both", expand=True)

        self.canvas = tk.Canvas(outer, height=250, width=460, highlightthickness=0)
        scrollbar = tb.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tb.Frame(self.canvas)

        self.scroll_frame.bind("<Configure>", self.on_rows_resized)
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scroll_frame,
            anchor="nw",
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")

        order_column = tb.Frame(outer)
        order_column.pack(side="left", fill="y", padx=(12, 0))

        order_label = tb.Label(order_column, text="Merge order")
        order_label.pack(anchor="w", pady=(0, 6))

        self.move_up_button = tb.Button(
            order_column,
            text="Move up",
            bootstyle="secondary",
            command=self.move_up,
            width=16,
        )
        self.move_up_button.pack(fill="x", pady=3)

        self.move_down_button = tb.Button(
            order_column,
            text="Move down",
            bootstyle="secondary",
            command=self.move_down,
            width=16,
        )
        self.move_down_button.pack(fill="x", pady=3)

        self.move_top_button = tb.Button(
            order_column,
            text="Move to top",
            bootstyle="secondary",
            command=self.move_to_top,
            width=16,
        )
        self.move_top_button.pack(fill="x", pady=3)

        self.move_bottom_button = tb.Button(
            order_column,
            text="Move to bottom",
            bootstyle="secondary",
            command=self.move_to_bottom,
            width=16,
        )
        self.move_bottom_button.pack(fill="x", pady=3)

        self.order_status = tb.Label(
            order_column,
            text="",
            wraplength=160,
            font=("TkDefaultFont", 10, "italic"),
        )
        self.order_status.pack(anchor="w", pady=(8, 0))

        self.scroller = VerticalScroll(self.canvas)

    def on_rows_resized(self, _event):
        """Keep the scrollbar matched to the height of the checklist.

        Purpose:
            Update the scrollable area when rows are added or the
            highlighted button changes the height of the list.

        Inputs:
            _event: the Tk configure event. It is unused. The new size
            is read from the frame.

        Outputs:
            None.

        Side effects:
            Sets the canvas scroll region to the full checklist height.
        """
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_resize(self, event):
        """Keep each row inside the visible list.

        Purpose:
            A long file name would otherwise make the row wider than
            the dialog. This dialog is not resizable, so the name stays
            inside the scrolling area.

        Inputs:
            event: the Tk configure event. event.width is the canvas width.

        Outputs:
            None.

        Side effects:
            Sets the width of the frame that holds the rows.
        """
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def redraw_rows(self):
        """Draw the checklist again from self.rows.

        Purpose:
            The list on screen must match self.rows after a move.
            Rebuilding the rows is easier to follow than sliding
            widgets past each other. A folder of PDFs is small enough
            that rebuilding is instant.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Destroys the old row widgets and creates new ones.
            Checkbox values are kept, because each BooleanVar lives in
            self.rows and is reused.
            The highlighted row uses the blue info style.
            The scroll position is kept so the list does not jump
            back to the top.
        """
        scroll_position = self.canvas.yview()[0]

        for child in list(self.scroll_frame.winfo_children()):
            child.destroy()

        index = 0
        while index < len(self.rows):
            pdf_path, checked = self.rows[index]
            self._add_one_row(index, pdf_path, checked)
            index = index + 1

        self.scroll_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(scroll_position)

    def _add_one_row(self, index, pdf_path, checked):
        """Add one checkbox and one file-name button to the list.

        Purpose:
            The checkbox decides whether the file is included.
            The button shows the position and the file name. Clicking
            the button, or the checkbox, highlights that row so the
            Move buttons know what to move.

        Inputs:
            index: position in self.rows. 0 is the top.
            pdf_path: pathlib.Path of this PDF.
            checked: the BooleanVar for this file's checkbox.

        Outputs:
            None.

        Side effects:
            Creates widgets inside self.scroll_frame.
        """
        row_frame = tb.Frame(self.scroll_frame)
        row_frame.pack(fill="x", padx=4, pady=2)

        include_box = tb.Checkbutton(
            row_frame,
            variable=checked,
            command=self._command_for_index(index),
        )
        include_box.pack(side="left")

        if index == self.selected_index:
            name_style = "info"
        else:
            name_style = "secondary"

        # The number is part of the label so the user can see the
        # merge position without counting rows. 1 is the first page group.
        name_button = tb.Button(
            row_frame,
            text=str(index + 1) + ".  " + pdf_path.name,
            bootstyle=name_style,
            command=self._command_for_index(index),
        )
        name_button.pack(side="left", fill="x", expand=True, padx=(4, 0))

    def _command_for_index(self, index):
        """Return a no-argument function that highlights this row.

        Purpose:
            A Tk button command cannot receive the row number directly.
            This wrapper remembers the index from the moment the button
            was created. Using the loop variable itself would be wrong:
            every button would see the last index after the loop ends.

        Inputs:
            index: position in self.rows. 0 is the top.

        Outputs:
            A function that takes no arguments.

        Side effects:
            None until the returned function is called.
        """
        def select_this_row():
            """Highlight the row this button was built for.

            Purpose:
                Mark this file as the one the Move buttons will rearrange.
                If the click was on the checkbox, the checkbox has already
                toggled. This function does not change that checkmark.

            Inputs:
                None. The index was stored when _command_for_index ran.

            Outputs:
                None.

            Side effects:
                Calls select_row, which redraws the list.
            """
            self.select_row(index)

        return select_this_row

    def select_row(self, index):
        """Highlight the row at this position.

        Purpose:
            Clicking a file name chooses which file the Move buttons
            affect. The checkbox is a separate choice: it decides
            whether the file is included at all.

        Inputs:
            index: 0 is the first row on screen.

        Outputs:
            None.

        Side effects:
            Sets self.selected_index, redraws the list, and updates the
            Move buttons and the status sentence.
            Ignores an index that is outside the list.
        """
        if index < 0 or index >= len(self.rows):
            return
        self.selected_index = index
        self.redraw_rows()
        self.update_move_buttons()
        self.show_highlight_status()

    def show_highlight_status(self):
        """Say which file the Move buttons will affect.

        Purpose:
            The blue file name is the highlighted row. This sentence
            says the same thing in words, including its position.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Changes the small status label under the Move buttons.
        """
        if self.selected_index is None or len(self.rows) == 0:
            self.set_order_status("Click a file name. That row is the one that moves.")
            return

        pdf_path, _checked = self.rows[self.selected_index]
        place = self.selected_index + 1
        total = len(self.rows)
        self.set_order_status(
            "Highlighted: "
            + pdf_path.name
            + " ("
            + str(place)
            + " of "
            + str(total)
            + ")."
        )

    def set_order_status(self, text):
        """Change the sentence under the Move buttons.

        Purpose:
            One place updates that label so the Move methods stay short.

        Inputs:
            text: the sentence to show.

        Outputs:
            None.

        Side effects:
            Changes the label text.
        """
        self.order_status.configure(text=text)

    def update_move_buttons(self):
        """Enable only the Move buttons that can do something.

        Purpose:
            Move up and Move to top do nothing on the first row.
            Move down and Move to bottom do nothing on the last row.
            A disabled button is harder to click by mistake.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Sets each Move button to normal or disabled.
        """
        if self.selected_index is None or len(self.rows) == 0:
            self._set_move_enabled(False, False, False, False)
            return

        at_top = self.selected_index <= 0
        at_bottom = self.selected_index >= len(self.rows) - 1
        self._set_move_enabled(not at_top, not at_bottom, not at_top, not at_bottom)

    def _set_move_enabled(self, up_enabled, down_enabled, top_enabled, bottom_enabled):
        """Turn the four Move buttons on or off.

        Purpose:
            Keep update_move_buttons readable. Tk wants the words
            "normal" and "disabled", and this function translates
            True and False into those words.

        Inputs:
            up_enabled: True to allow Move up.
            down_enabled: True to allow Move down.
            top_enabled: True to allow Move to top.
            bottom_enabled: True to allow Move to bottom.

        Outputs:
            None.

        Side effects:
            Changes the state of the four Move buttons.
        """
        self._set_button_enabled(self.move_up_button, up_enabled)
        self._set_button_enabled(self.move_down_button, down_enabled)
        self._set_button_enabled(self.move_top_button, top_enabled)
        self._set_button_enabled(self.move_bottom_button, bottom_enabled)

    def _set_button_enabled(self, button, enabled):
        """Turn one button on or off.

        Purpose:
            Translate True and False into the state words Tk expects.

        Inputs:
            button: a ttkbootstrap button.
            enabled: True to allow clicks. False to ignore them.

        Outputs:
            None.

        Side effects:
            Changes the button state.
        """
        if enabled:
            button.configure(state="normal")
        else:
            button.configure(state="disabled")

    def move_up(self):
        """Move the highlighted file one place up.

        Purpose:
            Trade places with the file above it so it is merged sooner.

        Inputs:
            None. Uses self.rows and self.selected_index.

        Outputs:
            None.

        Side effects:
            Reorders self.rows. The checkbox stays with its file.
            The same file stays highlighted. The first file does not move.
        """
        self._apply_move(move_up)

    def move_down(self):
        """Move the highlighted file one place down.

        Purpose:
            Trade places with the file below it so it is merged later.

        Inputs:
            None. Uses self.rows and self.selected_index.

        Outputs:
            None.

        Side effects:
            Reorders self.rows. The checkbox stays with its file.
            The same file stays highlighted. The last file does not move.
        """
        self._apply_move(move_down)

    def move_to_top(self):
        """Move the highlighted file to the top of the list.

        Purpose:
            Make that file the first PDF in the merge.

        Inputs:
            None. Uses self.rows and self.selected_index.

        Outputs:
            None.

        Side effects:
            Reorders self.rows. The checkbox stays with its file.
            The same file stays highlighted at position 1.
        """
        self._apply_move(move_to_top)

    def move_to_bottom(self):
        """Move the highlighted file to the bottom of the list.

        Purpose:
            Make that file the last PDF in the merge.

        Inputs:
            None. Uses self.rows and self.selected_index.

        Outputs:
            None.

        Side effects:
            Reorders self.rows. The checkbox stays with its file.
            The same file stays highlighted at the last position.
        """
        self._apply_move(move_to_bottom)

    def _apply_move(self, move_function):
        """Run one reorder function and refresh the checklist.

        Purpose:
            The four Move buttons share these steps. Only the direction
            changes. The functions live in merge_logic.py so they can
            be tested without opening a window.

        Inputs:
            move_function: move_up, move_down, move_to_top, or
                move_to_bottom from merge_logic.py. It accepts
                (items, index) and returns (new_items, new_index).

        Outputs:
            None.

        Side effects:
            Replaces self.rows and self.selected_index when a row is
            highlighted, then redraws the list and the Move buttons.
            If nothing is highlighted, writes a status sentence and
            does not reorder.
        """
        if self.selected_index is None:
            self.set_order_status("Click a file name first. That row is the one that moves.")
            return

        new_rows, new_index = move_function(self.rows, self.selected_index)
        self.rows = new_rows
        self.selected_index = new_index
        self.redraw_rows()
        self.update_move_buttons()
        self.show_highlight_status()

    def _build_buttons(self):
        """Add Confirm, Select all, Clear all, and Cancel.

        Purpose:
            Confirm is the only button that accepts the choice.
            Select all and Clear all edit the boxes and leave the window open.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Creates the buttons along the bottom of the dialog.
        """
        button_row = tb.Frame(self.window)
        button_row.pack(pady=(5, 15))

        self.confirm_button = tb.Button(
            button_row,
            text="Confirm selection",
            bootstyle="primary",
            command=self.confirm,
        )
        self.confirm_button.pack(side="left", padx=8)

        select_all_button = tb.Button(
            button_row,
            text="Select all",
            bootstyle="secondary",
            command=self.select_all,
        )
        select_all_button.pack(side="left", padx=8)

        clear_button = tb.Button(
            button_row,
            text="Clear all",
            bootstyle="warning",
            command=self.clear_all,
        )
        clear_button.pack(side="left", padx=8)

        cancel_button = tb.Button(
            button_row,
            text="Cancel",
            bootstyle="secondary",
            command=self.cancel,
        )
        cancel_button.pack(side="left", padx=8)

    def checked_paths(self):
        """Return the paths whose boxes are currently checked.

        Purpose:
            Read the checkbox variables into an ordinary list the merge
            code can use.

        Inputs:
            None. Uses self.rows.

        Outputs:
            A list of pathlib.Path, in the same order as the checklist.

        Side effects:
            None.
        """
        paths = []
        flags = []
        for pdf_path, checked in self.rows:
            paths.append(pdf_path)
            flags.append(bool(checked.get()))

        # chosen_files lives in merge_logic.py so it can be tested
        # without opening a window. It preserves order.
        return chosen_files(paths, flags)

    def confirm(self):
        """Save the checked files and close the dialog.

        Purpose:
            Accept the checklist. Fewer than two checked files is not
            a merge, so the dialog stays open and explains why.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            On success, sets self.selected and destroys the dialog.
            On too few files, shows a warning and leaves the dialog open.
        """
        checked = self.checked_paths()
        problem = selection_problem(checked)
        if problem is not None:
            messagebox.showwarning("Too few files", problem, parent=self.window)
            return

        self.selected = checked
        self.window.destroy()

    def select_all(self):
        """Turn every checkbox on.

        Purpose:
            Undo a Clear all without closing the dialog.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Sets every checkbox variable to True.
        """
        for _pdf_path, checked in self.rows:
            checked.set(True)

    def clear_all(self):
        """Turn every checkbox off.

        Purpose:
            Let the user start from an empty selection and check only
            the files they want. Confirm will refuse the empty list.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Sets every checkbox variable to False.
        """
        for _pdf_path, checked in self.rows:
            checked.set(False)

    def cancel(self):
        """Close the dialog without changing the chosen files.

        Purpose:
            self.selected stays None. The main window keeps whatever
            selection it already had.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Destroys the dialog.
        """
        self.selected = None
        self.window.destroy()

    def on_escape(self, _event):
        """Close the checklist without keeping a new selection.

        Purpose:
            Cancel when the user presses the Escape key.

        Inputs:
            _event: the Tk key event. It is unused.

        Outputs:
            None.

        Side effects:
            Same as clicking Cancel.
        """
        self.cancel()


class MergePDFApp:
    """The three-step main window.

    State kept on this object:
        folder      pathlib.Path of the confirmed folder, or None.
        file_list   PDFs the user confirmed, in merge order.
        last_output pathlib.Path of the last successful merge, or None.
        file_name_var
                    The text in the name box.

    Reset clears that state. It does not delete any PDF.
    """

    def __init__(self):
        """Create the window and the widgets. Do not enter the event loop.

        Purpose:
            Build the interface. main() calls run() afterwards, which
            enters the loop. Tests can construct the window, inspect it,
            and destroy it without calling run().

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Opens a window (it appears when the event loop runs).
            Loads the red m icon when the file is present.
        """
        self.folder = None
        self.file_list = []
        self.last_output = None

        self.root = create_main_window()
        self.root.resizable(False, False)
        nametofont("TkDefaultFont").configure(size=12)

        self.file_name_var = tk.StringVar(value="")

        self._build_menu()
        self._build_step_one()
        self._build_step_two()
        self._build_step_three()
        self._layout_frames()

        place_window_on_screen(self.root, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.select_button.focus_set()
        self.update_merge_button()

    def run(self):
        """Show the window and wait until the user closes it.

        Purpose:
            Hand control to Tk. Button clicks call the methods on this
            object until the window is destroyed.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Enters the Tk event loop. This call returns when the window closes.
        """
        self.root.mainloop()

    def _build_menu(self):
        """Add the File and Help menus.

        Purpose:
            The same actions as the buttons, available from the menu bar.
            macOS may show this menu on the top of the screen rather than
            inside the window. That is normal Tk behavior.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Attaches a menu bar to the main window.
        """
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Reset", command=self.reset_form)
        file_menu.add_command(label="Exit", command=self.close_app)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Instructions", command=self.open_help)
        help_menu.add_command(label="About", command=self.open_about)
        help_menu.add_command(label="Contact", command=self.open_contact)

    def _build_step_one(self):
        """Create the folder-selection row. Layout happens later.

        Purpose:
            Step 1 widgets: instruction, Select folder button, status line.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Creates widgets stored on self. They are not on screen until
            _layout_frames() places them.
        """
        self.step_one = tb.Frame(self.root, relief="sunken")
        self.instruction_folder = tb.Label(
            self.step_one,
            text="Step 1. Click Select folder. A checklist will let you choose which PDFs to include and the order to merge them.",
            wraplength=MESSAGE_WRAP,
        )
        self.select_button = tb.Button(
            self.step_one,
            text="Select folder",
            command=self.select_folder,
        )
        self.message_folder = tb.Label(
            self.step_one,
            text="No folder selected yet.",
            font=("TkDefaultFont", 10, "italic"),
            wraplength=MESSAGE_WRAP,
        )

    def _build_step_two(self):
        """Create the file-name row. Layout happens later.

        Purpose:
            Step 2 widgets: instruction, name box, Submit name button, status.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Creates widgets stored on self.
            Pressing Return in the name box submits the name.
        """
        self.step_two = tb.Frame(self.root, relief="sunken")
        self.instruction_name = tb.Label(
            self.step_two,
            text="Step 2. Type a name for the merged file and click Submit name. Leave it blank to use merged_pdfs.pdf.",
            wraplength=MESSAGE_WRAP,
        )
        self.submit_button = tb.Button(
            self.step_two,
            text="Submit name",
            command=self.select_name,
        )
        self.name_entry = tb.Entry(
            self.step_two,
            textvariable=self.file_name_var,
        )
        self.name_entry.bind("<Return>", self.on_name_enter)
        self.message_name = tb.Label(
            self.step_two,
            text="Leave blank for the default name: merged_pdfs.pdf",
            font=("TkDefaultFont", 10, "italic"),
            wraplength=MESSAGE_WRAP,
        )

    def _build_step_three(self):
        """Create the merge row. Layout happens later.

        Purpose:
            Step 3 widgets: Merge, Reset, Help, Exit, the result line,
            and the Open merged PDF button (hidden until a merge works).

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Creates widgets stored on self.
            The Merge button starts disabled until two PDFs are confirmed.
        """
        self.step_three = tb.Frame(self.root, relief="sunken")
        self.instruction_merge = tb.Label(
            self.step_three,
            text="Step 3. Click Merge PDFs. The new file is saved in the same folder.",
            wraplength=MESSAGE_WRAP,
        )
        self.merge_button = tb.Button(
            self.step_three,
            text="Merge PDFs!",
            bootstyle="primary",
            command=self.merge_clicked,
            state="disabled",
        )
        self.reset_button = tb.Button(
            self.step_three,
            text="Reset",
            bootstyle="success",
            command=self.reset_form,
        )
        self.help_button = tb.Button(
            self.step_three,
            text="Help",
            bootstyle="warning",
            command=self.open_help,
        )
        self.exit_button = tb.Button(
            self.step_three,
            text="Exit",
            bootstyle="danger",
            command=self.close_app,
        )
        self.message_merge = tb.Label(
            self.step_three,
            text="",
            font=("TkDefaultFont", 10, "italic"),
            wraplength=MERGE_MESSAGE_WRAP,
        )
        self.open_button = tb.Button(
            self.step_three,
            text="Open merged PDF",
            bootstyle="info",
            command=self.open_result,
        )

    def _layout_frames(self):
        """Place the three steps in a grid that fills the window.

        Purpose:
            Tk's grid is rows and columns. The window has one column and
            three rows of equal height. Each row is one step.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Makes the widgets visible (except Open merged PDF, which is
            placed and then hidden so Tk remembers where to put it back).
        """
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=1)

        # Let the status line in step 1 use the full width of that row.
        self.step_one.columnconfigure(0, weight=1)

        self.step_one.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 4))
        self.step_two.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        self.step_three.grid(row=2, column=0, sticky="nsew", padx=8, pady=(4, 8))

        self.instruction_folder.grid(row=0, column=0, sticky="w", padx=16, pady=(10, 4))
        self.select_button.grid(row=1, column=0, sticky="w", padx=16, pady=4)
        self.message_folder.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 10))

        self.step_two.columnconfigure(1, weight=1)
        self.instruction_name.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(10, 4))
        self.submit_button.grid(row=1, column=0, sticky="w", padx=16, pady=4)
        self.name_entry.grid(row=1, column=1, sticky="ew", padx=(8, 16), pady=4)
        self.message_name.grid(row=2, column=0, columnspan=2, sticky="ew", padx=16, pady=(4, 10))

        for column in range(5):
            self.step_three.columnconfigure(column, weight=1)

        self.instruction_merge.grid(row=0, column=0, columnspan=5, sticky="ew", padx=16, pady=(10, 4))
        self.merge_button.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(16, 4), pady=4)
        self.reset_button.grid(row=1, column=2, sticky="ew", padx=4, pady=4)
        self.help_button.grid(row=1, column=3, sticky="ew", padx=4, pady=4)
        self.exit_button.grid(row=1, column=4, sticky="ew", padx=(4, 16), pady=4)
        self.message_merge.grid(row=2, column=0, columnspan=3, sticky="ew", padx=16, pady=(4, 10))
        self.open_button.grid(row=2, column=3, columnspan=2, sticky="e", padx=(4, 16), pady=(4, 10))
        # grid() then grid_remove() records the position. A later grid()
        # with no arguments puts the button back in that same spot.
        self.open_button.grid_remove()

    def set_status(self, label, text, kind):
        """Change one status line under a step.

        Purpose:
            Show what just happened. Green means it worked. Red means
            something is wrong. The muted theme color is an ordinary note.

        Inputs:
            label: the ttkbootstrap Label to update.
            text: the sentence to show.
            kind: "info", "ok", or "error".

        Outputs:
            None.

        Side effects:
            Changes the label text and color.
        """
        if kind == "ok":
            style_name = "success"
        elif kind == "error":
            style_name = "danger"
        else:
            style_name = "secondary"

        label.configure(text=text, bootstyle=style_name)

    def update_merge_button(self):
        """Enable Merge only when two or more PDFs are confirmed.

        Purpose:
            A disabled button is harder to click by accident. merge_clicked()
            still checks the same rule, in case the button state is stale.

        Inputs:
            None. Uses self.file_list.

        Outputs:
            None.

        Side effects:
            Sets the Merge button to normal or disabled.
        """
        problem = selection_problem(self.file_list)
        if problem is None and self.folder is not None:
            self.merge_button.configure(state="normal")
        else:
            self.merge_button.configure(state="disabled")

    def hide_open_button(self):
        """Hide the Open merged PDF button.

        Purpose:
            The button should only be visible when last_output points at
            a merge from this session that we still want to offer.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Hides the button. Does not delete last_output.
        """
        self.open_button.grid_remove()

    def restore_open_button_if_file_remains(self):
        """Show Open merged PDF again when an earlier result is still on disk.

        Purpose:
            A failed retry hides the button at the start of the click.
            If the previous merged file is still there, put the button back
            so that file can still be opened.

        Inputs:
            None. Uses self.last_output.

        Outputs:
            None.

        Side effects:
            Shows the button when the previous file exists.
        """
        if self.last_output is not None and self.last_output.is_file():
            self.show_open_button()

    def show_open_button(self):
        """Show the Open merged PDF button in its saved grid position.

        Purpose:
            Offer a way to view the file that was just written.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Shows the button and asks Tk to refresh so it appears immediately.
        """
        self.open_button.grid()
        # grid() is stored right away, but the button is not actually
        # shown until Tk refreshes the window. Refresh now so the button
        # is visible before focus moves to Reset.
        self.root.update_idletasks()

    def close_app(self):
        """Close the window and end the program.

        Purpose:
            Exit. Same action as the window's close box.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Destroys the window, which ends run(). Does not delete PDFs.
        """
        self.root.destroy()

    def open_help(self):
        """Show the instructions.

        Purpose:
            Open the instructions box from a button or the Help menu.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Shows a modal message box.
        """
        show_help(self.root)

    def open_about(self):
        """Show version and copyright information.

        Purpose:
            Open the About box from the Help menu.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Shows a modal message box.
        """
        show_about(self.root)

    def open_contact(self):
        """Show the support email address.

        Purpose:
            Open the contact box from the Help menu.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Shows a modal message box.
        """
        show_contact(self.root)

    def reset_form(self):
        """Clear the form so the user can start over.

        Purpose:
            Forget the folder, the checked files, and the typed name.
            A merged PDF that was already written stays on disk.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Resets the status lines, hides Open merged PDF, disables
            Merge, and puts the keyboard focus back on Select folder.
        """
        self.folder = None
        self.file_list = []
        self.last_output = None
        self.file_name_var.set("")

        self.set_status(self.message_folder, "No folder selected yet.", "info")
        self.set_status(
            self.message_name,
            "Leave blank for the default name: merged_pdfs.pdf",
            "info",
        )
        self.set_status(self.message_merge, "", "info")
        self.hide_open_button()
        self.update_merge_button()
        self.select_button.focus_set()

    def select_folder(self):
        """Ask for a folder, then open the PDF checklist.

        Purpose:
            Step 1. The folder dialog does not show files on every system,
            so the next window lists the PDFs and lets the user uncheck some.
            Nothing is committed until they click Confirm selection.

        Inputs:
            None. The chosen path comes from the system folder dialog.

        Outputs:
            None.

        Side effects:
            May update self.folder and self.file_list when the user confirms.
            A cancel, or a folder with fewer than two PDFs, leaves the
            previous confirmed choice in place.
        """
        if self.folder is None:
            chosen = filedialog.askdirectory(
                parent=self.root,
                mustexist=True,
                title="Choose the folder that contains your PDFs",
            )
        else:
            # Start in the folder they already confirmed, so a second
            # look does not dump them at the top of the disk.
            chosen = filedialog.askdirectory(
                parent=self.root,
                mustexist=True,
                title="Choose the folder that contains your PDFs",
                initialdir=str(self.folder),
            )

        if chosen is None or str(chosen).strip() == "":
            self.set_status(self.message_folder, "Folder selection canceled.", "info")
            self.select_button.focus_set()
            return

        folder = Path(chosen)
        try:
            found = list_pdfs(folder)
        except OSError as error:
            self.set_status(
                self.message_folder,
                "Could not read that folder. Details: " + str(error),
                "error",
            )
            self.select_button.focus_set()
            return

        if len(found) < 2:
            self._reject_short_folder(len(found))
            return

        dialog = PdfChoiceDialog(self.root, found)
        # wait_window returns after the checklist is destroyed.
        self.root.wait_window(dialog.window)

        if dialog.selected is None:
            self._note_checklist_canceled()
            return

        self.folder = folder
        self.file_list = dialog.selected
        self.set_status(
            self.message_folder,
            "Selected "
            + str(len(self.file_list))
            + " of "
            + str(len(found))
            + " PDF files from: "
            + str(self.folder),
            "ok",
        )
        self.update_merge_button()
        self.submit_button.focus_set()

    def _reject_short_folder(self, found_count):
        """Tell the user a folder does not have enough PDFs to merge.

        Purpose:
            Zero files and one file are different sentences, but both
            refuse the folder. A previous good selection is kept.

        Inputs:
            found_count: 0 or 1.

        Outputs:
            None.

        Side effects:
            Updates the step 1 status line and focuses Select folder.
            Does not change self.folder or self.file_list.
        """
        if found_count == 0:
            detail = "That folder has no PDF files."
        else:
            detail = "That folder has only one PDF file. Merge needs at least two."

        if len(self.file_list) >= 2:
            detail = detail + " The earlier choice is still in place."

        self.set_status(self.message_folder, detail, "error")
        self.select_button.focus_set()

    def _note_checklist_canceled(self):
        """Update the status line after the checklist is canceled.

        Purpose:
            Make it obvious that a cancel did not silently select every file.

        Inputs:
            None.

        Outputs:
            None.

        Side effects:
            Updates the step 1 status line. Does not change the file list.
        """
        if len(self.file_list) >= 2:
            text = "File selection canceled. The earlier choice is still in place."
        else:
            text = "File selection canceled."
        self.set_status(self.message_folder, text, "info")
        self.select_button.focus_set()

    def on_name_enter(self, _event):
        """Accept the file name from the keyboard.

        Purpose:
            Submit the name when the user presses Return in the text box.

        Inputs:
            _event: the Tk key event. It is unused. The name is read from
            the text box.

        Outputs:
            None.

        Side effects:
            Same as clicking Submit name.
        """
        self.select_name()

    def select_name(self):
        """Check the name in the text box and show the result.

        Purpose:
            Give feedback before Merge is clicked. Merge checks the name
            again, because the user can edit the box after Submit.

        Inputs:
            None. Reads self.file_name_var.

        Outputs:
            None.

        Side effects:
            On success, writes the final name (with .pdf) back into the
            box and moves focus to Merge.
            On failure, leaves the typed text in the box so it can be
            corrected, and explains the problem under the box.
        """
        is_ok, result = prepare_output_name(self.file_name_var.get())
        if not is_ok:
            self.set_status(self.message_name, "Error: " + result, "error")
            self.submit_button.focus_set()
            return

        self.file_name_var.set(result)
        self.set_status(self.message_name, "You entered: " + result, "ok")
        self.merge_button.focus_set()

    def merge_clicked(self):
        """Merge the confirmed PDFs into one new file.

        Purpose:
            Step 3. Re-check the selection and the file name, pick a path
            that does not overwrite anything, then call merge_pdfs().

        Inputs:
            None. Uses self.folder, self.file_list, and the name box.

        Outputs:
            None.

        Side effects:
            On success, writes one PDF in the selected folder, shows a
            green status line, and reveals Open merged PDF.
            On failure, shows a red status line and does not reveal the
            open button. Source PDFs are not modified.
        """
        self.hide_open_button()

        problem = selection_problem(self.file_list)
        if self.folder is None or problem is not None:
            self.set_status(
                self.message_merge,
                "Select a folder with at least two PDF files first.",
                "error",
            )
            self.restore_open_button_if_file_remains()
            self.reset_button.focus_set()
            return

        is_ok, result = prepare_output_name(self.file_name_var.get())
        if not is_ok:
            self.set_status(self.message_name, "Error: " + result, "error")
            self.set_status(self.message_merge, "Fix the file name, then click Merge PDFs again.", "error")
            self.restore_open_button_if_file_remains()
            self.submit_button.focus_set()
            return

        final_name = result
        try:
            output_path = choose_output_path(self.folder, final_name)
            merge_pdfs(self.file_list, output_path)
        except MergeError as error:
            self.set_status(self.message_merge, str(error), "error")
            self.restore_open_button_if_file_remains()
            self.reset_button.focus_set()
            return
        except OSError as error:
            self.set_status(
                self.message_merge,
                "Could not use that folder. Details: " + str(error),
                "error",
            )
            self.restore_open_button_if_file_remains()
            self.reset_button.focus_set()
            return

        self.last_output = output_path
        self.file_name_var.set(output_path.name)
        self.set_status(self.message_name, "New merged file name: " + output_path.name, "ok")
        self.set_status(
            self.message_merge,
            "Successfully merged " + str(len(self.file_list)) + " files.",
            "ok",
        )
        self.show_open_button()
        # Focus Reset so a following Return does not immediately merge again.
        self.reset_button.focus_set()

    def open_result(self):
        """Open the PDF written by the last successful merge.

        Purpose:
            Hand the file to Preview on a Mac, or to the default PDF app
            on Windows and Linux.

        Inputs:
            None. Uses self.last_output.

        Outputs:
            None.

        Side effects:
            Starts the viewer when the file is still there.
            Shows an error on the merge status line when it is missing
            or the viewer fails to launch.
        """
        if self.last_output is None:
            self.set_status(self.message_merge, "There is no merged PDF to open yet.", "error")
            return

        if not self.last_output.is_file():
            self.set_status(
                self.message_merge,
                "That merged file is no longer in the folder.",
                "error",
            )
            return

        try:
            open_merged_pdf(self.last_output)
        except OSError as error:
            opener = describe_platform_opener()
            self.set_status(
                self.message_merge,
                "Could not open the PDF in " + opener + ". Details: " + str(error),
                "error",
            )


def main():
    """Start MergePDF.

    Purpose:
        Build the window and run it until the user closes it.

    Inputs:
        None.

    Outputs:
        None.

    Side effects:
        Opens the graphical window. Returns when that window is closed.
    """
    app = MergePDFApp()
    app.run()


if __name__ == "__main__":
    main()
