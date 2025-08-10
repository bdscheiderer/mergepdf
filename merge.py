''' MergePDF is a prgram that merges several pdf files into one 
    new pdf file. Currently using PdfMerger library and tkinter gui.
'''

from PyPDF2 import PdfMerger
from pathlib import Path
import sys
import os
import tkinter as tk
from tkinter import filedialog
from tkinter.font import nametofont
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# global variables
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400
FILE_LIST = [] # global list to pass to functions

def main():
    """Main function to initialize and run the Tkinter application."""
    root = tb.Window(themename="superhero")
    root.title("MergePDF")

    # set size of window and center on screen, prohibit resizing
    center_window(root)
    root.resizable(False, False)

    # Get the default font object and configure its size
    default_font = nametofont("TkDefaultFont")
    default_font.configure(size=12)

    # Load the icon image
    root.iconbitmap("favicon_m.ico")

    # create menus
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    create_menu(root, menubar)

    # dictionary of Tkinter variables to hold data
    named_vars = {
    "folder_name" : tk.StringVar(value=""),
    "file_name" : tk.StringVar(value=""),
    "number_files" : tk.IntVar(value=0)
    }

    # creates tkinter window and widgets
    create_gui(root, named_vars)

    root.mainloop()

def create_gui(root, named_vars):
    ''' Create the gui and widgets using tk grid system'''

    # Configure the rows to expand equally
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=1)
    root.grid_rowconfigure(2, weight=1)

    # Configure the single column to expand
    root.grid_columnconfigure(0, weight=1)

    # Create three frames for the rows
    frame1 = tb.Frame(root, relief="sunken")
    frame2 = tb.Frame(root, relief="sunken")
    frame3 = tb.Frame(root, relief="sunken")

    # Place them in the grid, making them sticky to fill the space
    frame1.grid(row=0, column=0, sticky="nsew")
    frame2.grid(row=1, column=0, sticky="nsew")
    frame3.grid(row=2, column=0, sticky="nsew")

    # Configure rows to have the same height
    for i in range(3): # For rows 0, 1, and 2
        root.grid_rowconfigure(i, weight=1, uniform="same_height_group")

    # Configure columns within frame2 for equal width
    frame2.columnconfigure(0, uniform="equal_cols", weight=1)
    frame2.columnconfigure(0, uniform="equal_cols", weight=2)

    ''' Frame 1 - Select Folder '''
    # Widgets for Frame 1
    instruction1 = tb.Label(frame1, text="First, click 'Select' to choose the folder where your pdf files are located:")
    button1 = tb.Button(frame1, text="Select folder", command=lambda: select_folder(message1, named_vars, button1, button2))
    message1 = tb.Label(frame1, font=("TkDefaultFont", 10, "italic"), text="No folder selected yet.")

    instruction1.grid(row=0, column=0, sticky="w", padx=20, pady=5)
    button1.grid(row=1, column=0, sticky="w", padx=20, pady=5)
    message1.grid(row=2, column=0, sticky="w", padx=20, pady=5)

    button1.focus_set()

    ''' Frame 2 - Select File Name '''
    # Widgets for Frame 2
    instruction2 = tb.Label(frame2, text="Second, enter a name for the merged file and click 'Submit':")
    entry2 = tb.Entry(frame2, width=50, textvariable=named_vars["file_name"])
    button2 = tb.Button(frame2, text="Submit name", command=lambda: select_name(message2, named_vars, merge_button))
    message2 = tb.Label(frame2, font=("TkDefaultFont", 10, "italic"), text="Leave blank for default name of: 'merged_pdfs.pdf'")

    instruction2.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=5)
    button2.grid(row=1, column=0, sticky="w", padx=20, pady=5)
    entry2.grid(row=1, column=1, sticky="w", padx=20, pady=5)
    message2.grid(row=2, column=0, columnspan=2, sticky="w", padx=20, pady=5)

    ''' Frame 3 - Action Buttons '''
    # Widgets for Frame 3
    instruction3 = tb.Label(frame3, text="Third, click the 'MERGE PDFs!' button:")
    merge_button = tb.Button(frame3, bootstyle="primary", text="Merge PDFs!", command=lambda: pdf_merge(named_vars, message3, reset_button))
    reset_button = tb.Button(frame3, bootstyle="success", text="Reset", command=lambda: reset_form(named_vars, message1, message2, message3, button1))
    help_button = tb.Button(frame3, bootstyle="warning", text="Help", command=lambda: open_help_topics())
    exit_button = tb.Button(frame3, bootstyle="danger", text="Exit", command=root.destroy)
    message3 = tb.Label(frame3, font=("TkDefaultFont", 10, "italic"), text="")

    instruction3.grid(row=0, column=0, sticky=tk.EW, padx=20, pady=5)
    merge_button.grid(row=1, column=0, columnspan=2, sticky=tk.EW, padx=20, pady=5)
    reset_button.grid(row=1, column=2, sticky=tk.EW, padx=10, pady=5)
    help_button.grid(row=1, column=3, sticky=tk.EW, padx=10, pady=5)
    exit_button.grid(row=1, column=4, sticky=tk.EW, padx=10, pady=5)
    message3.grid(row=2, column=0, columnspan=5, rowspan=1, sticky=tk.EW, padx=20, pady=5)

def create_menu(root, menubar):
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)

    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=help_menu)

    help_menu.add_command(label="Instructions", command=open_help_topics)
    help_menu.add_command(label="About", command=show_about_info)
    help_menu.add_command(label="Contact", command=open_contact)

    #help_menu.add_separator() # Add a separator line
    file_menu.add_command(label="Exit", command=root.destroy)

def show_about_info():
    # Function to display "About" information
    tk.messagebox.showinfo("About", "This is a sample Tkinter application.")

def open_help_topics():
    # Function to open help documentation or a new window with help info
    tk.messagebox.showinfo("Instructions", "Here you would find detailed help.")

def open_contact():
    # Function to open help documentation or a new window with help info
    tk.messagebox.showinfo("Contact", "Contact information.")

def center_window(window):
    # window.update_idletasks()
    width = WINDOW_WIDTH # window.winfo_width()
    height = WINDOW_HEIGHT # window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

def reset_form(named_vars, message1, message2, message3, button1):
    named_vars["folder_name"].set("")
    named_vars["file_name"].set("")
    #named_vars["file_list"].set([])
    named_vars["number_files"].set(0)

    message1.config(text=f"No folder selected yet.") # message1 default text
    message2.config(text=f"Leave blank for default name of: 'merged_pdfs.pdf'") # message2
    message3.config(text=f"")
    button1.focus_set() # focus to Select folder button

def select_folder(message1, named_vars, button1, button2):
    ''' Opens a dialog for the user to select a folder and updaets the path var '''
    # known issue - cannot see files in the directory when selecting folder
    path = filedialog.askdirectory(mustexist=True)

    if path:  # If a folder was selected (not canceled)
        named_vars['folder_name'].set(path)

        # not that have path, find any pdf files in that path
        num = get_pdfs(named_vars)  # function not yet working
        named_vars['number_files'].set(num)
        message1.config(text=f"Found {num} pdf files in this folder: {path}")
        # can now use 'folder_path' to retrieve files from this directory
    else:
        message1.config(text=f"Folder selection canceled.")
        button1.focus_set()
        return
    
    button2.focus_set()

def select_name(label2, named_vars, merge_button):
    """Updates the text of file name label widget."""
    new_text = named_vars["file_name"].get()
    label2.config(text=f"You entered: {new_text}")

    merge_button.focus_set()

def get_pdfs(named_vars):

    # ensure global var is empty list
    global FILE_LIST
    FILE_LIST = []

    ''' Get list of pdf files in path -- case-insensitive 
        globbing for files ending with .pdf or .PDF '''
    directory_path = Path(named_vars['folder_name'].get())
    FILE_LIST = [item for item in directory_path.glob("*.pdf", case_sensitive=False)]
    length = len(FILE_LIST)

    ''' Check if no or only one pdf found and if so, exit with warning'''
    if length == 0:
        print("Warning: no PDF files found.\n")
    if length == 1:
        print("Warning: only one PDF file found.\n")

    return len(FILE_LIST)

def pdf_merge(named_vars, message3, reset_button):
    ''' Merges all the pdf files in current directory '''

    global FILE_LIST

    directory_path = Path(named_vars['folder_name'].get())
    merger = PdfMerger()
    merged_file_name = "merged_pdfs.pdf"  # to do file name?
    name_and_path = directory_path / merged_file_name

    try:
        [merger.append(pdf) for pdf in FILE_LIST]
        with open(name_and_path, "wb") as new_file:
            merger.write(new_file)
    except Exception as e:
        message3.config(text=f"Error merging files: {e}") 
        reset_button.focus_set()
        return True
    
    message3.config(text=f"Successfully merged {len(FILE_LIST)} files.") 
    reset_button.focus_set()
    return True

def is_valid_filename(filename):
    """
    Checks if a given filename is likely valid across common operating systems.
    This is a basic check and may not cover all edge cases or specific filesystem rules.
    """
    if not filename or filename.strip() == "":
        return False, "Filename cannot be empty."

    # Common disallowed characters across Windows and Unix-like systems
    disallowed_chars = r'<>:"/\|?*'
    for char in disallowed_chars:
        if char in filename:
            return False, f"Filename contains disallowed character: '{char}'"

    # Windows-specific reserved names (case-insensitive)
    windows_reserved_names = [
        "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4",
        "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3",
        "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    ]
    if os.name == 'nt' and filename.upper().split('.')[0] in windows_reserved_names:
        return False, "Filename is a Windows reserved name."

    # Basic check for leading/trailing spaces or dots (often problematic)
    if filename.endswith('.') or filename.endswith(' '):
        return False, "Filename cannot end with a dot or space."

    return True, "Filename is valid."





if __name__ == "__main__":
    main()