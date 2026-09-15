# Import PyMuPDF's fitz module for working with PDF files
import fitz


# Define a function to extract text from a PDF file
def extract_text_from_pdf(file_path: str) -> str:
    
    # Open the PDF file using PyMuPDF
    document = fitz.open(file_path)

    # Create a list to store the extracted text from each page
    extracted_text = []

    # Loop through each page in the PDF
    for page in document:
        
        # Extract text from the current page and add it to the list
        extracted_text.append(page.get_text())

    # Close the PDF after processing all pages
    document.close()

    # Combine the text from all pages and return it as a single string
    return "\n".join(extracted_text)
