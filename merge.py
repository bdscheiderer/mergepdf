from PyPDF2 import PdfMerger
from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog
from tkinter.font import nametofont
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# global variables
WINDOWWIDTH = 600
WINDOWHEIGHT = 400


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
    filelist = []
    named_vars = {
    "folder_name" : tk.StringVar(value=""),
    "file_name" : tk.StringVar(value=""),
    "file_list" : tk.StringVar(value=filelist),
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
    button1 = tb.Button(frame1, text="Select folder", command=lambda: select_folder(message1, named_vars))
    message1 = tb.Label(frame1, font=("TkDefaultFont", 11, "italic"), text="No folder selected yet.")
    instruction1.grid(row=0, column=0, sticky="w", padx=20, pady=5)
    button1.grid(row=1, column=0, sticky="w", padx=20, pady=5)
    message1.grid(row=2, column=0, sticky="w", padx=20, pady=5)

    ''' Frame 2 - Select File Name '''
    # Widgets for Frame 2
    instruction2 = tb.Label(frame2, text="Second, enter a name for the merged file and click 'Submit':")
    entry2 = tb.Entry(frame2, width=50, textvariable=named_vars["file_name"])
    button2 = tb.Button(frame2, text="Submit name", command=lambda: select_name(message2, named_vars))
    message2 = tb.Label(frame2, font=("TkDefaultFont", 11, "italic"), text="Leave blank for default name of: 'merged_pdfs.pdf'")

    instruction2.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=5)
    entry2.grid(row=1, column=1, sticky="", padx=20, pady=5)
    button2.grid(row=1, column=0, sticky="w", padx=20, pady=5)
    message2.grid(row=2, column=0, columnspan=2, sticky="w", padx=20, pady=5)

    ''' Frame 3 - Action Buttons '''
    # Widgets for Frame 3
    instruction3 = tb.Label(frame3, text="Third, click the 'MERGE PDFs!' button:")
    merge_button = tb.Button(frame3, bootstyle="primary", text="Merge PDFs!", command= lambda: pdf_merge(named_vars))
    clear_button = tb.Button(frame3, bootstyle="success", text="Reset")
    info_button = tb.Button(frame3, bootstyle="warning", text="Help")
    exit_button = tb.Button(frame3, bootstyle="danger", text="Exit", command=root.destroy)
    message3 = tb.Label(frame3, font=("TkDefaultFont", 11, "italic"), text="Success/failure message here")

    instruction3.grid(row=0, column=0, sticky=tk.EW, padx=20, pady=5)
    merge_button.grid(row=1, column=0, sticky=tk.EW, padx=20, pady=5)
    clear_button.grid(row=1, column=1, sticky=tk.EW, padx=10, pady=5)
    info_button.grid(row=1, column=2, sticky=tk.EW, padx=10, pady=5)
    exit_button.grid(row=1, column=3, sticky=tk.EW, padx=10, pady=5)
    message3.grid(row=2, column=0, sticky=tk.EW, padx=20, pady=5)

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
    window.update_idletasks()
    width = WINDOWWIDTH # window.winfo_width()
    height = WINDOWHEIGHT # window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

def select_folder(label_widget, named_vars):
    """Opens a dialog for the user to select a folder and prints the path."""
    folder_var = named_vars["folder_name"]
    number_var = named_vars["number_files"]
    allpdfs = []
    
    path = filedialog.askdirectory()
    if path:  # If a folder was selected (not canceled)
        num = get_pdfs(named_vars)
        folder_var.set(path)
        number_var.set(num)
        label_widget.config(text=f"Will merge {num} pdfs found in this folder: {path}")
        # You can now use 'folder_path' to retrieve files from this directory

        named_vars["file_list"].set(allpdfs)

    else:
        print("Folder selection canceled.")

def select_name(label_widget, named_vars):
    """Updates the text of file name label widget."""
    new_text = named_vars["file_name"].get()
    label_widget.config(text=f"You entered: {new_text}")

def get_pdfs(named_vars):

    # ''' Get current path and print as a string '''
    # print(f"\nCurrent path: {str(Path.cwd())}\n")

    # ''' Get list of pdf files in path -- case-insensitive 
    #     globbing for files ending with .pdf or .PDF '''
    # allpdfs = [a for a in Path('.').glob("*.pdf", case_sensitive=False)]
    # length = len(allpdfs)

    # ''' Check if no or only one pdf found and if so, exit with warning'''
    # if length == 0:
    #     print("Warning: no PDF files found.\n")
    #     sys.exit()
    # if length == 1:
    #     print("Warning: only one PDF file found.\n")
    #     sys.exit()

    # ''' Print found pdf files '''
    # print(f"{length} PDF files found:")
    # for file in allpdfs:
    #     print(file)
    # print()

    # ''' Merge pdf files '''
    # merged_file_name = pdf_merge(allpdfs)
    # print(f"All files successfully merged to: {merged_file_name}\n")

    pdf_list = ["1.pdf", "2.pdf", "3.pdf"]
    named_vars["file_list"].set(pdf_list)
    return len(pdf_list)

def pdf_merge(named_vars):
    ''' Merges all the pdf files in current directory '''
    # merger = PdfMerger()
    # merged_file_name = "merged_pdfs.pdf"  # to do file name?
    # [merger.append(pdf) for pdf in allpdfs]
    # with open(merged_file_name, "wb") as new_file:
    #     merger.write(new_file)
    # return merged_file_name
    allpdfs = named_vars["file_list"].get()
    return True

if __name__ == "__main__":
    main()