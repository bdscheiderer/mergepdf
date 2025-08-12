# merge all pdf files in same folder
import sys
from PyPDF2 import PdfMerger
from pathlib import Path


def main():

    ''' Get current path and print as a string '''
    print(f"\nCurrent path: {str(Path.cwd())}\n")

    ''' Get list of pdf files in path (case insenstive) '''
    allpdfs = get_pdf_list()
    length = len(allpdfs)

    ''' Check if no or only one pdf found and if so, exit with warning'''
    if length == 0:
        print("Warning: no PDF files found.\n")
        sys.exit()
    if length == 1:
        print("Warning: only one PDF file found.\n")
        sys.exit()

    ''' Print found pdf files '''
    print(f"{length} PDF files found:")
    for file in allpdfs:
        print(file)
    print()

    ''' Merge pdf files '''
    merged_file_name = pdf_merge(allpdfs)
    print(f"All files successfully merged to: {merged_file_name}\n")


def get_pdf_list():
    ''' Case-insensitive globbing for files ending with .pdf or .PDF '''
    allpdfs = [a for a in Path('.').glob("*.pdf", case_sensitive=False)]
    return(allpdfs)


def pdf_merge(allpdfs):
    ''' Merges all the pdf files in current directory '''
    merger = PdfMerger()
    merged_file_name = "merged_pdfs.pdf"  # to do file name?
    [merger.append(pdf) for pdf in allpdfs]
    with open(merged_file_name, "wb") as new_file:
        merger.write(new_file)
    return merged_file_name

if __name__ == "__main__":
    main()