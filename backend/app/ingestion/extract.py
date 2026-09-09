"""
KavachAI — PDF/Document Text Extraction
Implements: FR-ING-2 (text extraction preserving page/section metadata)

Uses PyMuPDF (fitz) for PDF extraction, python-docx for DOCX, plain read for TXT.
"""

import pymupdf
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from docx import Document as DocxDocument

logger = logging.getLogger("kavachai.extract")


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
    TEXT_SUFFIXES = {
        ".txt", ".text", ".md", ".csv", ".json", ".log",
        ".tsv", ".yaml", ".yml", ".py", ".sql", ".ini", ".conf",
    }

    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(file_content)
    elif suffix == ".docx":
        return _extract_docx(file_content)
    elif suffix in TEXT_SUFFIXES:
        return _extract_text(file_content, filename)
    else:
        # Fallback: attempt to decode as text before giving up
        try:
            return _extract_text(file_content, filename)
        except Exception:
            return []


def _extract_pdf(file_content: bytes) -> List[Dict[str, Any]]:
    """
    Extract text from PDF preserving page numbers.
    Implements: FR-ING-2 (PyMuPDF preserves page metadata)
    """
    pages = []
    try:
        doc = pymupdf.open(stream=file_content, filetype="pdf")

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")

            # Fallback to block extraction if layout is complex or table-heavy
            if not text.strip():
                blocks = page.get_text("blocks")
                if blocks:
                    text = "\n".join(b[4] for b in blocks if len(b) > 4 and b[4].strip())

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
    except Exception as e:
        logger.warning(f"PyMuPDF failed to extract text from PDF: {e}")
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
        try:
            doc = pymupdf.open(stream=file_content, filetype="pdf")
            count = len(doc)
            doc.close()
            return count
        except Exception:
            return 1

    return 1  # Non-PDF documents treated as single page
