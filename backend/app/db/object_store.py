"""
KavachAI — Object Store (Local Filesystem)
Implements: FR-ING-6 (raw file storage, addressable by source_id)

Supports: save_raw_file, get_raw_file, get_file_page (for PDF page renders needed
by GET /evidence/{source_id} and Source Viewer)
"""

import os
import shutil
from pathlib import Path
from typing import Optional

import pymupdf  # PyMuPDF — implements FR-ING-2

from app.config import settings


class ObjectStore:
    """Local filesystem object store for raw source files."""

    def __init__(self):
        self.base_path = Path(settings.OBJECT_STORE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _file_path(self, source_id: str) -> Path:
        """Get the filesystem path for a source_id."""
        return self.base_path / source_id

    def save_raw_file(self, source_id: str, file_content: bytes, filename: str) -> str:
        """
        Save a raw file to the object store.
        Implements: FR-ING-6

        Args:
            source_id: unique identifier for this file
            file_content: raw file bytes
            filename: original filename (preserved for metadata)

        Returns:
            The storage path (relative)
        """
        # Create a directory per source_id to hold the file + any derived artifacts
        source_dir = self._file_path(source_id)
        source_dir.mkdir(parents=True, exist_ok=True)

        file_path = source_dir / filename
        file_path.write_bytes(file_content)

        return str(file_path.relative_to(self.base_path))

    def get_raw_file(self, source_id: str) -> Optional[tuple[bytes, str]]:
        """
        Retrieve raw file content by source_id.

        Returns:
            (file_bytes, filename) or None if not found
        """
        source_dir = self._file_path(source_id)
        if not source_dir.exists():
            return None

        # Find the first file in the source directory (the raw file)
        files = [f for f in source_dir.iterdir() if f.is_file() and not f.name.startswith(".")]
        if not files:
            return None

        raw_file = files[0]
        return raw_file.read_bytes(), raw_file.name

    def get_file_page(self, source_id: str, page: int) -> Optional[bytes]:
        """
        Render a specific page of a PDF as PNG image.
        Needed by GET /evidence/{source_id} and Source Viewer (Design.md §5.6).

        Args:
            source_id: the document's source_id
            page: 1-indexed page number

        Returns:
            PNG bytes of the rendered page, or None
        """
        result = self.get_raw_file(source_id)
        if result is None:
            return None

        file_bytes, filename = result
        if not filename.lower().endswith(".pdf"):
            return None

        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            if page < 1 or page > len(doc):
                doc.close()
                return None

            pdf_page = doc[page - 1]  # 0-indexed
            pix = pdf_page.get_pixmap(dpi=150)
            png_bytes = pix.tobytes("png")
            doc.close()
            return png_bytes
        except Exception:
            return None

    def get_page_count(self, source_id: str) -> Optional[int]:
        """Get the number of pages in a PDF document."""
        result = self.get_raw_file(source_id)
        if result is None:
            return None

        file_bytes, filename = result
        if not filename.lower().endswith(".pdf"):
            return None

        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            count = len(doc)
            doc.close()
            return count
        except Exception:
            return None

    def exists(self, source_id: str) -> bool:
        """Check if a source_id exists in the store."""
        return self._file_path(source_id).exists()

    def delete(self, source_id: str) -> bool:
        """Delete a source and all its artifacts."""
        source_dir = self._file_path(source_id)
        if source_dir.exists():
            shutil.rmtree(source_dir)
            return True
        return False


# Singleton instance
object_store = ObjectStore()
