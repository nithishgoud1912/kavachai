"""
KavachAI — PDF/Document Text Extraction
Implements: FR-ING-2 (text extraction preserving page/section metadata)

Uses PyMuPDF (fitz) for PDF extraction, python-docx for DOCX, plain read for TXT.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Any, Optional
from docx import Document as DocxDocument


def extract_text(file_content: bytes, filename: str) -> List[Dict[str, Any]]:
    """
    Extract text from a file, preserving page/section metadata.
    Implements: FR-ING-2

    Args:
        file_content: raw file bytes
        filename: original filename (determines extraction method)

    Returns:
        List of pages: [{page: int, text: str, metadata: {...}}]
    """
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(file_content)
    elif suffix == ".docx":
        return _extract_docx(file_content)
    elif suffix in (".txt", ".text", ".md"):
        return _extract_text(file_content, filename)
    else:
        # Unsupported format — return empty
        return []


def _extract_pdf(file_content: bytes) -> List[Dict[str, Any]]:
    """
    Extract text from PDF preserving page numbers.
    Implements: FR-ING-2 (PyMuPDF preserves page metadata)
    """
    pages = []
    doc = fitz.open(stream=file_content, filetype="pdf")

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")

        if text.strip():  # Skip empty pages
            pages.append({
                "page": page_num + 1,  # 1-indexed
                "text": text.strip(),
                "metadata": {
                    "width": page.rect.width,
                    "height": page.rect.height,
                },
            })

    doc.close()
    return pages


def _extract_docx(file_content: bytes) -> List[Dict[str, Any]]:
    """Extract text from DOCX. Treated as single page since DOCX has no fixed page concept."""
    import io
    doc = DocxDocument(io.BytesIO(file_content))

    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text)

    if full_text:
        return [{
            "page": 1,
            "text": "\n".join(full_text),
            "metadata": {"format": "docx"},
        }]

    return []


def _extract_text(file_content: bytes, filename: str) -> List[Dict[str, Any]]:
    """Extract text from plain text files."""
    try:
        text = file_content.decode("utf-8")
    except UnicodeDecodeError:
        text = file_content.decode("latin-1")

    if text.strip():
        return [{
            "page": 1,
            "text": text.strip(),
            "metadata": {"format": "txt"},
        }]

    return []


def get_page_count(file_content: bytes, filename: str) -> int:
    """Get the number of pages in a document."""
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        doc = fitz.open(stream=file_content, filetype="pdf")
        count = len(doc)
        doc.close()
        return count

    return 1  # Non-PDF documents treated as single page
