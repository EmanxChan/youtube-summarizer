"""PDF text extraction and cleaning utilities."""

import re
from pathlib import Path


def clean_pdf_text(raw_text):
    """Clean and format PDF extracted text into proper paragraphs.
    
    Args:
        raw_text: Raw text extracted from PDF
        
    Returns:
        Cleaned text with proper paragraph breaks
    """
    # Remove excessive whitespace while preserving intentional breaks
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', raw_text)
    
    # Remove spaces around newlines
    text = re.sub(r' *\n *', '\n', text)
    
    # Replace multiple newlines with double newline (paragraph break)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Split into lines
    lines = text.split('\n')
    
    # Rebuild paragraphs
    paragraphs = []
    current_paragraph = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            if current_paragraph:
                # End current paragraph
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
            continue
        
        # Check if line ends with sentence-ending punctuation
        ends_sentence = line.endswith(('.', '!', '?', ':', ';'))
        
        # Add line to current paragraph
        current_paragraph.append(line)
        
        # If line ends with punctuation and is reasonably long, might be paragraph end
        if ends_sentence and len(line) > 40:
            paragraphs.append(' '.join(current_paragraph))
            current_paragraph = []
    
    # Add any remaining paragraph
    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph))
    
    # Join paragraphs with double newline
    cleaned_text = '\n\n'.join(paragraphs)
    
    return cleaned_text


def extract_text_from_pdf(file_path):
    """Extract text from PDF file using pdfplumber (preferred) or PyPDF2 (fallback).
    
    Args:
        file_path: Path to PDF file (str or Path)
        
    Returns:
        Extracted and cleaned text
        
    Raises:
        Exception if extraction fails with both methods
    """
    file_path = Path(file_path)
    
    try:
        # Try pdfplumber first (better text extraction)
        import pdfplumber
        
        with pdfplumber.open(file_path) as pdf:
            raw_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    raw_text += page_text + "\n\n"
        
        return clean_pdf_text(raw_text)
        
    except (ImportError, Exception) as e:
        # Fallback: use PyPDF2
        try:
            import PyPDF2
            
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                raw_text = ""
                for page in reader.pages:
                    raw_text += page.extract_text() + "\n"
            
            return clean_pdf_text(raw_text)
            
        except Exception as fallback_error:
            raise Exception(f"PDF extraction failed with both methods. pdfplumber: {e}, PyPDF2: {fallback_error}")
