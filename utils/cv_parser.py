import pdfplumber
import logging

def read_pdf(filepath: str) -> str:
    """Extracts text from a PDF file."""
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""  # Handle None returns
                text += "\n"
    except Exception as e:
        logging.error(f"Error reading PDF file: {e}")
    return text
    




    
