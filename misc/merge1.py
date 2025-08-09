import tkinter as tk
from tkinter import filedialog

def select_file():
    """Opens a file dialog and returns the selected file's path."""
    file_path = filedialog.askopenfilename(
        title="Select a File",
        filetypes=(("All Files", "*.*"), ("Text Files", "*.txt"))
    )
    if file_path:  # If a file was selected
        path_label.config(text=f"Selected File: {file_path}")
        # You can now use 'file_path' to retrieve and process the file
        print(f"File path selected: {file_path}")
    else:
        path_label.config(text="No file selected.")

def select_folder():
    """Opens a dialog for the user to select a folder and prints the path."""
    folder_path = filedialog.askdirectory()
    if folder_path:  # If a folder was selected (not canceled)
        print(f"Selected folder: {folder_path}")
        # You can now use 'folder_path' to retrieve files from this directory
    else:
        print("Folder selection canceled.")

# Create the main application window
root = tk.Tk()
root.title("File Path Selector")

# Create a button to trigger the file selection dialog
select_button = tk.Button(root, text="Select File", command=select_file)
select_button.pack(pady=10)

# Create a label to display the selected file path
path_label = tk.Label(root, text="No file selected.")
path_label.pack(pady=10)

# Create a button to trigger the folder selection
select_button = tk.Button(root, text="Select Folder", command=select_folder)
select_button.pack(pady=20)



# Run the Tkinter event loop
root.mainloop()