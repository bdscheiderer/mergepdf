''' MergePDF is a prgram that merges several pdf files into one 
    new pdf file. Currently using PdfMerger library and tkinter gui.
'''

from datetime import datetime
from PyPDF2 import PdfMerger
from pathlib import Path
import os
import tkinter as tk
from tkinter import filedialog
from tkinter.font import nametofont
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# global variables
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400
DEFAULT_MERGED_NAME = "merged_pdfs.pdf"

# global list of pdf files to pass to functions because of tkinter behavior
FILE_LIST = []


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

    # Create dictionary of all widgets
    widgets = create_widgets(root, frame1, frame2, frame3, named_vars)

    # Frame 1 grid
    widgets['instruction1'].grid(row=0, column=0, sticky="w", padx=20, pady=5)
    widgets['select_button'].grid(row=1, column=0, sticky="w", padx=20, pady=5)
    widgets['message1'].grid(row=2, column=0, sticky="w", padx=20, pady=5)
    widgets['select_button'].focus_set() # set intial focus to folder select button

    # Frame 2 grid
    widgets['instruction2'].grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=5)
    widgets['submit_button'].grid(row=1, column=0, sticky="w", padx=20, pady=5)
    widgets['entry2'].grid(row=1, column=1, sticky="w", padx=20, pady=5)
    widgets['message2'].grid(row=2, column=0, columnspan=2, sticky="w", padx=20, pady=5)

    # Frame 3 grid
    widgets['instruction3'].grid(row=0, column=0, sticky=tk.EW, padx=20, pady=5)
    widgets['merge_button'].grid(row=1, column=0, columnspan=2, sticky=tk.EW, padx=20, pady=5)
    widgets['reset_button'].grid(row=1, column=2, sticky=tk.EW, padx=10, pady=5)
    widgets['help_button'].grid(row=1, column=3, sticky=tk.EW, padx=10, pady=5)
    widgets['exit_button'].grid(row=1, column=4, sticky=tk.EW, padx=10, pady=5)
    widgets['message3'].grid(row=2, column=0, columnspan=5, rowspan=1, sticky=tk.EW, padx=20, pady=5)

def create_widgets(root, frame1, frame2, frame3, named_vars):
    ''' Create all widgets and return as dict '''
    widgets = {} # needed bc dict self-references
    widgets = {
        # Frame 1 widgets
        "instruction1" : tb.Label(frame1, 
                        text="First, click 'Select' to choose the folder where your pdf files are located:"),
        "select_button" : tb.Button(frame1, 
                        text="Select folder", 
                        command=lambda: select_folder(widgets, named_vars)),
        "message1" : tb.Label(frame1, 
                        font=("TkDefaultFont", 10, "italic"), 
                        text="No folder selected yet."),

        # Frame 2 widgets
        "instruction2" : tb.Label(frame2, 
                        text="Second, enter a name for the merged file and click 'Submit':"),
        "entry2" : tb.Entry(frame2, 
                        width=50, 
                        textvariable=named_vars["file_name"]),
        "submit_button" : tb.Button(frame2, 
                        text="Submit name", 
                        command=lambda: select_name(widgets, named_vars)),
        "message2" : tb.Label(frame2, 
                        font=("TkDefaultFont", 10, "italic"), 
                        text="Leave blank for default name of: 'merged_pdfs.pdf'"),

        # Frame 3 widgets
        "instruction3" : tb.Label(frame3, 
                        text="Third, click the 'MERGE PDFs!' button:"),
        "merge_button" : tb.Button(frame3, 
                        bootstyle="primary", 
                        text="Merge PDFs!", 
                        command=lambda: pdf_merge(widgets, named_vars)),
        "reset_button" : tb.Button(frame3, 
                        bootstyle="success", 
                        text="Reset", 
                        command=lambda: reset_form(widgets, named_vars)),
        "help_button" :  tb.Button(frame3, 
                        bootstyle="warning", 
                        text="Help", 
                        command=lambda: open_help_topics()),
        "exit_button" : tb.Button(frame3, 
                        bootstyle="danger", 
                        text="Exit", 
                        command=root.destroy),
        "message3" : tb.Label(frame3, 
                        font=("TkDefaultFont", 10, "italic"), 
                        text="")
    }

    return widgets

def create_menu(root, menubar):
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Exit", command=root.destroy)

    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="Instructions", command=open_help_topics)
    help_menu.add_command(label="About", command=show_about_info)
    help_menu.add_command(label="Contact", command=open_contact)

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

def reset_form(widgets, named_vars):
    named_vars["folder_name"].set("")
    named_vars["file_name"].set("")
    named_vars["number_files"].set(0)

    # reset text
    widgets['message1'].config(text=f"No folder selected yet.") # message1 default text
    widgets['message2'].config(text=f"Leave blank for default name of: 'merged_pdfs.pdf'")
    widgets['message3'].config(text=f"")

    # focus to Select folder button
    widgets['select_button'].focus_set() 

def select_folder(widgets, named_vars):
    ''' Opens a dialog for the user to select a folder and updaets the path var '''
    # known issue - cannot see files in the directory when selecting folder
    path = filedialog.askdirectory(mustexist=True)

    if path:  # If a folder was selected (not canceled)
        named_vars['folder_name'].set(path)

        # now that have path, find any pdf files in that path
        num, message = get_pdfs(widgets, named_vars)
    else:
        widgets['message1'].config(text=f"Folder selection canceled.")
        widgets['select_button'].focus_set()
        return
    
    if num == 0 or num == 1:
        widgets['message1'].config(text=message)
        widgets['select_button'].focus_set()
        return

    widgets['message1'].config(text=f"Found {num} pdf files in this folder: {path}")
    widgets['submit_button'].focus_set()

def select_name(widgets, named_vars):
    '''Checks validity of file name and updates widget '''
    # Get user entered file name and check not empty strong
    if named_vars['file_name'].get() == "":
        name = DEFAULT_MERGED_NAME
    else:
        name = named_vars['file_name'].get()

    # Check valid filename
    success, message = is_valid_filename(name)
    if success == False:
        # send error message and return focus to submit
        widgets['message2'].config(text=f"Error: {message}")
        named_vars["file_name"].set("")
        widgets['submit_button'].focus_set()
        return

    # check if ends with .pdf, if not add .pdf to end
    file_name = check_pdf_extension(name)

    # check if filename is in the pdf folder (will be in FILE_LIST)
    # if no continue, if yes add datetime to beginnning of name
    for item in FILE_LIST:
        file_path = Path(item)
        if file_path.name == file_name:
            
            # Get the current datetime object and format as string
            current_datetime = datetime.now()
            datetime_as_string = current_datetime.strftime("%y%m%d%H%M%S")
            file_name = datetime_as_string + file_name

    # if pass all above checks, set new file_name
    named_vars['file_name'].set(file_name)

    # print new name and set focus to the merge button
    widgets['message2'].config(text=f"Merged file name: {file_name}")
    widgets['merge_button'].focus_set()

def get_pdfs(widgets, named_vars):
    ''' Get list of pdf files in path -- case-insensitive 
        globbing for files ending with .pdf or .PDF '''

    # this function will update global var; ensure list is empty
    global FILE_LIST 
    FILE_LIST = []

    # search for all pdf files in selected folder
    directory_path = Path(named_vars['folder_name'].get())
    FILE_LIST = [item for item in directory_path.glob("*.pdf", case_sensitive=False)]

    # ensure at least two pdfs to merge
    length = len(FILE_LIST)
    if length == 0:
        message = "Warning: no PDF files found."
        return length, message
    elif length == 1:
        message = "Warning: only one PDF file found."
        return length, message
    else:
        named_vars['number_files'].set(length)
        message = "sucess"

    return length, message

def pdf_merge(widgets, named_vars):
    ''' Merges all the pdf files in current directory '''
    merger = PdfMerger()
    merged_file_name = named_vars['file_name'].get()
    directory_path = Path(named_vars['folder_name'].get())
    name_and_path = directory_path / merged_file_name

    try:
        [merger.append(pdf) for pdf in FILE_LIST]
        with open(name_and_path, "wb") as new_file:
            merger.write(new_file)
    except Exception as e:
        widgets['message3'].config(text=f"Error merging files: {e}") 
        widgets['reset_button'].focus_set()
        return
    
    widgets['message3'].config(text=f"Successfully merged {len(FILE_LIST)} files.") 
    widgets['reset_button'].focus_set()

def check_pdf_extension(filename):
    ''' Checks that filename ends with ".pdf", if not, add extension. '''
    if not filename.lower().endswith(".pdf"):
        return filename + ".pdf"
    print(filename)
    return filename

def is_valid_filename(filename):
    """
    PathValidate function from: https://github.com/thombashi/pathvalidate

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