''' MergePDF is a prgram that merges several pdf files into one
    new pdf file. Currently using PdfWriter library and tkinter gui.

    Version 1.1 -- add file selection; cleaned up some code

    Copyright 2026 S2Legacy.com
'''

from datetime import datetime
from pypdf import PdfWriter
from pathlib import Path
import logging
import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.font import nametofont
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# suppress pypdf annotation/size warnings
logging.getLogger("pypdf").setLevel(logging.ERROR)

# global constants
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400
DEFAULT_MERGED_NAME = "merged_pdfs.pdf"


class MergePDFApp:

    def __init__(self):
        self.file_list = []

        self.root = tb.Window(themename="superhero")
        self.root.title("MergePDF")

        center_window(self.root)
        self.root.resizable(False, False)

        nametofont("TkDefaultFont").configure(size=12)

        # Load app icon — .ico for Windows, .png for macOS/Linux
        if sys.platform == "win32":
            self.root.iconbitmap(resource_path("favicon.ico"))
        else:
            try:
                icon = tk.PhotoImage(file=resource_path("icon.png"))
                self.root.iconphoto(True, icon)
            except Exception:
                pass  # icon is non-critical; skip if file missing

        self.named_vars = {
            "folder_name" : tk.StringVar(value=""),
            "file_name"   : tk.StringVar(value=""),
            "number_files": tk.IntVar(value=0)
        }

        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        self.create_menu(menubar)

        self.create_gui()
        self.root.mainloop()

    def create_gui(self):
        ''' Create the gui and widgets using tk grid system '''
        # Configure rows to expand equally
        for i in range(3):
            self.root.grid_rowconfigure(i, weight=1, uniform="same_height_group")
        self.root.grid_columnconfigure(0, weight=1)

        # Create three frames for the rows
        frame1 = tb.Frame(self.root, relief="sunken")
        frame2 = tb.Frame(self.root, relief="sunken")
        frame3 = tb.Frame(self.root, relief="sunken")

        frame1.grid(row=0, column=0, sticky="nsew")
        frame2.grid(row=1, column=0, sticky="nsew")
        frame3.grid(row=2, column=0, sticky="nsew")

        # Configure columns within frame2 for equal width
        frame2.columnconfigure(0, uniform="equal_cols", weight=1)
        frame2.columnconfigure(1, uniform="equal_cols", weight=2)

        self.create_widgets(frame1, frame2, frame3)

        # Frame 1 grid
        self.widgets['instruction1'].grid(row=0, column=0, sticky="w", padx=20, pady=5)
        self.widgets['select_button'].grid(row=1, column=0, sticky="w", padx=20, pady=5)
        self.widgets['message1'].grid(row=2, column=0, sticky="w", padx=20, pady=5)
        self.widgets['select_button'].focus_set()  # set initial focus to folder select button

        # Frame 2 grid
        self.widgets['instruction2'].grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=5)
        self.widgets['submit_button'].grid(row=1, column=0, sticky="w", padx=20, pady=5)
        self.widgets['entry2'].grid(row=1, column=1, sticky="w", padx=20, pady=5)
        self.widgets['message2'].grid(row=2, column=0, columnspan=2, sticky="w", padx=20, pady=5)

        # Frame 3 grid
        self.widgets['instruction3'].grid(row=0, column=0, sticky=tk.EW, padx=20, pady=5)
        self.widgets['merge_button'].grid(row=1, column=0, columnspan=2, sticky=tk.EW, padx=20, pady=5)
        self.widgets['reset_button'].grid(row=1, column=2, sticky=tk.EW, padx=10, pady=5)
        self.widgets['help_button'].grid(row=1, column=3, sticky=tk.EW, padx=10, pady=5)
        self.widgets['exit_button'].grid(row=1, column=4, sticky=tk.EW, padx=10, pady=5)
        self.widgets['message3'].grid(row=2, column=0, columnspan=3, sticky=tk.EW, padx=20, pady=5)
        self.widgets['open_pdf_button'].grid(row=2, column=3, columnspan=2, sticky=tk.E, padx=10, pady=5)
        self.widgets['open_pdf_button'].grid_remove()  # hidden until a merge succeeds

    def create_widgets(self, frame1, frame2, frame3):
        ''' Create all widgets and store as instance dict '''
        self.widgets = {
            # Frame 1 widgets
            "instruction1"   : tb.Label(frame1,
                               text="First, click 'Select' to choose the folder where your pdf files are located:"),
            "select_button"  : tb.Button(frame1,
                               text="Select folder",
                               command=self.select_folder),
            "message1"       : tb.Label(frame1,
                               font=("TkDefaultFont", 10, "italic"),
                               text="No folder selected yet."),

            # Frame 2 widgets
            "instruction2"   : tb.Label(frame2,
                               text="Second, enter a name for the merged file and click 'Submit':"),
            "entry2"         : tb.Entry(frame2,
                               width=50,
                               textvariable=self.named_vars["file_name"]),
            "submit_button"  : tb.Button(frame2,
                               text="Submit name",
                               command=self.select_name),
            "message2"       : tb.Label(frame2,
                               font=("TkDefaultFont", 10, "italic"),
                               text="Leave blank for default name of: 'merged_pdfs.pdf'"),

            # Frame 3 widgets
            "instruction3"   : tb.Label(frame3,
                               text="Third, click the 'MERGE PDFs!' button:"),
            "merge_button"   : tb.Button(frame3,
                               bootstyle="primary",
                               text="Merge PDFs!",
                               command=self.pdf_merge),
            "reset_button"   : tb.Button(frame3,
                               bootstyle="success",
                               text="Reset",
                               command=self.reset_form),
            "help_button"    : tb.Button(frame3,
                               bootstyle="warning",
                               text="Help",
                               command=open_help_topics),
            "exit_button"    : tb.Button(frame3,
                               bootstyle="danger",
                               text="Exit",
                               command=self.root.destroy),
            "message3"       : tb.Label(frame3,
                               font=("TkDefaultFont", 10, "italic"),
                               text=""),
            "open_pdf_button": tb.Button(frame3,
                               bootstyle="info",
                               text="Open merged PDF",
                               command=lambda: None)
        }

    def create_menu(self, menubar):
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.destroy)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Instructions", command=open_help_topics)
        help_menu.add_command(label="About", command=open_about_info)
        help_menu.add_command(label="Contact", command=open_contact_info)

    def reset_form(self):
        self.file_list = []
        self.named_vars["folder_name"].set("")
        self.named_vars["file_name"].set("")
        self.named_vars["number_files"].set(0)

        self.widgets['message1'].config(text="No folder selected yet.")
        self.widgets['message2'].config(text="Leave blank for default name of: 'merged_pdfs.pdf'")
        self.widgets['message3'].config(text="")
        self.widgets['open_pdf_button'].grid_remove()

        self.widgets['select_button'].focus_set()

    def select_folder(self):
        ''' Opens a dialog for the user to select a folder and updates the path var '''
        # known issue - cannot see files in the directory when selecting folder
        path = filedialog.askdirectory(mustexist=True)

        if path:
            self.named_vars['folder_name'].set(path)
            num, message = self.get_pdfs()
        else:
            self.widgets['message1'].config(text="Folder selection canceled.")
            self.widgets['select_button'].focus_set()
            return

        if num == 0 or num == 1:
            self.widgets['message1'].config(text=message)
            self.widgets['select_button'].focus_set()
            return

        # Show file selection dialog so user can pick which PDFs to include
        self.show_file_selection()

    def show_file_selection(self):
        ''' Show a popup checklist of found PDFs so user can pick which to merge '''
        if not self.file_list:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Select PDF files to merge")
        dialog.resizable(False, False)

        tb.Label(dialog, text="Check the PDFs you want to include (all selected by default):").pack(
            padx=20, pady=(15, 5), anchor="w"
        )

        # Scrollable inner frame
        outer = tb.Frame(dialog)
        outer.pack(padx=20, pady=5, fill="both", expand=True)

        canvas = tk.Canvas(outer, height=250, width=420)
        scrollbar = tb.Scrollbar(outer, orient="vertical", command=canvas.yview)
        scroll_frame = tb.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda _: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # One checkbox per file, all checked by default
        check_vars = []
        for pdf in self.file_list:
            var = tk.BooleanVar(value=True)
            tb.Checkbutton(scroll_frame, text=pdf.name, variable=var).pack(anchor="w", padx=5, pady=2)
            check_vars.append((pdf, var))

        def confirm():
            selected = [pdf for pdf, var in check_vars if var.get()]
            if len(selected) < 2:
                messagebox.showwarning(
                    "Too few files", "Please select at least 2 PDF files.", parent=dialog
                )
                return
            self.file_list = selected
            self.named_vars['number_files'].set(len(selected))
            self.widgets['message1'].config(
                text=f"Selected {len(selected)} of {len(check_vars)} PDF files from: {self.named_vars['folder_name'].get()}"
            )
            dialog.destroy()
            self.widgets['submit_button'].focus_set()

        def clear_all():
            for _, var in check_vars:
                var.set(False)

        def cancel():
            dialog.destroy()
            self.widgets['select_button'].focus_set()

        btn_frame = tb.Frame(dialog)
        btn_frame.pack(pady=(5, 15))
        tb.Button(btn_frame, text="Confirm selection", bootstyle="primary", command=confirm).pack(
            side="left", padx=10
        )
        tb.Button(btn_frame, text="Clear all", bootstyle="warning", command=clear_all).pack(
            side="left", padx=10
        )
        tb.Button(btn_frame, text="Cancel", bootstyle="secondary", command=cancel).pack(
            side="left", padx=10
        )

        dialog.transient(self.root)
        dialog.grab_set()
        dialog.update_idletasks()
        w = dialog.winfo_width()
        h = dialog.winfo_height()
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        dialog.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")
        self.root.wait_window(dialog)

    def select_name(self):
        ''' Checks validity of file name and updates widget '''
        file_name = self._get_user_file_name()

        success, message = is_valid_filename(file_name)
        if not success:
            self.widgets['message2'].config(text=f"Error: {message}")
            self.named_vars["file_name"].set("")
            self.widgets['submit_button'].focus_set()
            return

        self.widgets['message2'].config(text=f"You entered: {file_name}")
        self.widgets['merge_button'].focus_set()

    def get_pdfs(self):
        ''' Get list of pdf files in path -- case-insensitive,
            sorted alphabetically to match the OS directory window '''
        self.file_list = sorted(
            Path(self.named_vars['folder_name'].get()).glob("*.pdf", case_sensitive=False),
            key=lambda p: p.name.lower()
        )

        length = len(self.file_list)
        if length == 0:
            return length, "Warning: no PDF files found."
        elif length == 1:
            return length, "Warning: only one PDF file found."
        else:
            self.named_vars['number_files'].set(length)
            return length, "success"

    def pdf_merge(self):
        ''' Merges all the pdf files in current directory
            PdfWriter/pypdf from https://pypi.org/project/pypdf/
        '''
        if len(self.file_list) < 2:
            self.widgets['message3'].config(text="Need to select a folder with two or more files.")
            self.widgets['reset_button'].focus_set()
            return

        merger = PdfWriter()
        merged_file_name = self._check_file_name()
        name_and_path = Path(self.named_vars['folder_name'].get()) / merged_file_name

        try:
            for pdf in self.file_list:
                merger.append(pdf)
            with open(name_and_path, "wb") as new_file:
                merger.write(new_file)
            self.widgets['message3'].config(text=f"Successfully merged {len(self.file_list)} files.")
            self.widgets['open_pdf_button'].config(command=lambda p=name_and_path: open_merged_pdf(p))
            self.widgets['open_pdf_button'].grid()
        except Exception as e:
            self.widgets['message3'].config(text=f"Error merging files: {e}")
            return
        finally:
            merger.close()

        self.widgets['reset_button'].focus_set()

    def _check_file_name(self):
        ''' Returns validated filename with .pdf extension, timestamped if conflict exists '''
        file_name = self._get_user_file_name()
        file_name = check_pdf_extension(file_name)

        # if filename already exists on disk in the destination folder, prepend datetime to avoid overwrite
        directory_path = Path(self.named_vars['folder_name'].get())
        existing = {f.name for f in directory_path.iterdir() if f.is_file()}
        if file_name in existing:
            file_name = datetime.now().strftime("%y%m%d%H%M%S") + file_name

        self.named_vars['file_name'].set(file_name)
        self.widgets['message2'].config(text=f"New merged file name: {file_name}")
        return file_name

    def _get_user_file_name(self):
        ''' Returns user-entered filename, or default if blank '''
        name = self.named_vars['file_name'].get()
        return name if name else DEFAULT_MERGED_NAME


# --- Standalone utility functions (no app state needed) ---

def center_window(window):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - WINDOW_WIDTH) // 2
    y = (screen_height - WINDOW_HEIGHT) // 2
    window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

def open_merged_pdf(filepath):
    ''' Open the merged PDF with the system default PDF viewer '''
    if sys.platform == "darwin":
        subprocess.call(["open", str(filepath)])
    elif sys.platform == "win32":
        os.startfile(str(filepath))
    else:
        subprocess.call(["xdg-open", str(filepath)])

def open_about_info():
    messagebox.showinfo("About", (
        "MergePDF v1.1\n"
        "A simple tool to merge PDF files into one.\n\n"
        "Built with Python, pypdf, and ttkbootstrap.\n\n"
        "Copyright 2026 S2Legacy.com\n"
        "Released under the MIT License."
    ))

def open_help_topics():
    messagebox.showinfo("Instructions", (
        "How to use MergePDF:\n\n"
        "1. Click 'Select Folder' to choose the folder\n"
        "   containing your PDF files.\n\n"
        "2. A file list will appear — check the PDFs\n"
        "   you want to include and click 'Confirm'.\n\n"
        "3. Enter a name for the merged file, then click\n"
        "   'Submit Name'. Leave blank to use the default\n"
        "   name 'merged_pdfs.pdf'.\n\n"
        "4. Click 'Merge PDFs!' to create the merged file.\n"
        "   It will be saved in the same folder as your\n"
        "   source PDFs.\n\n"
        "Note: If the output filename already exists, a\n"
        "timestamp will be added to avoid overwriting it."
    ))

def open_contact_info():
    messagebox.showinfo("Contact", (
        "S2Legacy.com\n\n"
        "For support or feedback:\n"
        "admin@s2legacy.com"
    ))

def check_pdf_extension(filename):
    ''' Checks that filename ends with ".pdf", if not, adds extension. '''
    if not filename.lower().endswith(".pdf"):
        return filename + ".pdf"
    return filename

def is_valid_filename(filename):
    """
    Checks if a given filename is likely valid across common operating systems.
    This is a basic check and may not cover all edge cases or specific filesystem rules.
    """
    if not filename or filename.strip() == "":
        return False, "Filename cannot be empty."

    disallowed_chars = r'<>:"/\|?*'
    for char in disallowed_chars:
        if char in filename:
            return False, f"Filename contains disallowed character: '{char}'"

    windows_reserved_names = [
        "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4",
        "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3",
        "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    ]
    if filename.upper().split('.')[0] in windows_reserved_names:
        return False, "Filename is a Windows reserved name."

    if filename.endswith('.') or filename.endswith(' '):
        return False, "Filename cannot end with a dot or space."

    return True, "Filename is valid."

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def main():
    MergePDFApp()

if __name__ == "__main__":
    main()
