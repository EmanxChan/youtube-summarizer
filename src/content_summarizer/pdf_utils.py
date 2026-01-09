"""PDF text extraction and cleaning utilities."""

import re
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent.parent / ".env")


def get_jina_api_key():
    """Get Jina API key from environment or Streamlit secrets."""
    key = os.environ.get('JINA_API_KEY', '')
    if key:
        return key
    try:
        import streamlit as st
        key = st.secrets.get('JINA_API_KEY', '')
        if key:
            return key
    except Exception:
        pass
    return ''


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
    """Extract text from PDF file using Jina (preferred), pdfplumber, or PyPDF2 (fallback).

    Fallback chain:
    1. Jina Reader API (best for complex PDFs, handles scanned docs better)
    2. pdfplumber (good local extraction)
    3. PyPDF2 (basic fallback)

    Args:
        file_path: Path to PDF file (str or Path)

    Returns:
        Extracted and cleaned text

    Raises:
        Exception if extraction fails with all methods
    """
    file_path = Path(file_path)
    errors = []

    # ==========================================================================
    # Method 1: Jina Reader API (Primary - handles complex PDFs well)
    # ==========================================================================
    try:
        import requests

        jina_api_key = get_jina_api_key()

        if jina_api_key or True:  # Try even without key (lower rate limits)
            print("  📖 Extracting PDF via Jina Reader...")

            jina_url = "https://r.jina.ai/"
            headers = {'User-Agent': 'ContentSummarizer/1.0'}

            if jina_api_key:
                headers['Authorization'] = f'Bearer {jina_api_key}'

            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/pdf')}
                response = requests.post(jina_url, headers=headers, files=files, timeout=60)

            if response.status_code == 200:
                content = response.text.strip()
                if len(content) >= 100:
                    print(f"  ✓ Jina PDF extraction success ({len(content)} chars)")
                    return content
                else:
                    errors.append(f"Jina returned too little content ({len(content)} chars)")
            else:
                errors.append(f"Jina returned status {response.status_code}")

    except Exception as e:
        errors.append(f"Jina error: {str(e)[:100]}")

    # ==========================================================================
    # Method 2: pdfplumber (Fallback - good local extraction)
    # ==========================================================================
    try:
        import pdfplumber
        print("  📄 Trying pdfplumber extraction...")

        with pdfplumber.open(file_path) as pdf:
            raw_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    raw_text += page_text + "\n\n"

        if len(raw_text.strip()) >= 100:
            print(f"  ✓ pdfplumber extraction success ({len(raw_text)} chars)")
            return clean_pdf_text(raw_text)
        else:
            errors.append(f"pdfplumber returned too little content ({len(raw_text)} chars)")

    except ImportError:
        errors.append("pdfplumber not installed")
    except Exception as e:
        errors.append(f"pdfplumber error: {str(e)[:100]}")

    # ==========================================================================
    # Method 3: PyPDF2 (Final fallback)
    # ==========================================================================
    try:
        import PyPDF2
        print("  📄 Trying PyPDF2 extraction...")

        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            raw_text = ""
            for page in reader.pages:
                raw_text += page.extract_text() + "\n"

        if len(raw_text.strip()) >= 100:
            print(f"  ✓ PyPDF2 extraction success ({len(raw_text)} chars)")
            return clean_pdf_text(raw_text)
        else:
            errors.append(f"PyPDF2 returned too little content ({len(raw_text)} chars)")

    except ImportError:
        errors.append("PyPDF2 not installed")
    except Exception as e:
        errors.append(f"PyPDF2 error: {str(e)[:100]}")

    # All methods failed
    error_summary = "; ".join(errors[:3])
    raise Exception(f"PDF extraction failed with all methods: {error_summary}")
