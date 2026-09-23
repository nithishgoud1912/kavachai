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

    IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"}

    suffix = Path(filename).suffix.lower()

    if suffix in IMAGE_SUFFIXES:
        return []
    elif suffix == ".pdf":
        return _extract_pdf(file_content)
    elif suffix == ".docx":
        return _extract_docx(file_content)
    elif suffix in TEXT_SUFFIXES:
        return _extract_text(file_content, filename)
    else:
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


# ---------------------------------------------------------------------------
# Tiered OCR Pipeline (Phase 3.2)
# ---------------------------------------------------------------------------

async def extract_text_with_ocr(
    file_content: bytes,
    filename: str,
    enable_vlm: bool = True,
) -> List[Dict[str, Any]]:
    """
    Async tiered OCR extraction pipeline.
    Cascades through extraction methods until text is obtained:

      Tier 1: Embedded PDF text (PyMuPDF) — fast, no OCR needed
      Tier 2: Tesseract OCR (CPU) — good for clean printed text
      Tier 3: EasyOCR — better for complex/handwritten text
      Tier 4: Qwen2.5-VL via ModelRouter — for diagrams/schematics

    Preserves backward compatibility: sync extract_text() remains unchanged.

    Args:
        file_content: raw file bytes
        filename: original filename
        enable_vlm: whether to attempt VLM extraction for images/scanned PDFs

    Returns:
        List of pages: [{page: int, text: str, metadata: {...}}]
    """
    suffix = Path(filename).suffix.lower()
    IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"}

    # For non-PDF, non-image files, use standard extraction
    if suffix not in (".pdf",) and suffix not in IMAGE_SUFFIXES:
        return extract_text(file_content, filename)

    # --- Tier 1: Try embedded text extraction first (PDF only) ---
    if suffix == ".pdf":
        pages = _extract_pdf(file_content)
        if pages and any(len(p["text"].strip()) > 50 for p in pages):
            logger.info("Tier 1 (embedded text) succeeded for %s", filename)
            return pages

    # --- Tier 2: Tesseract OCR ---
    tier2_pages = await _ocr_tesseract(file_content, filename, suffix)
    if tier2_pages and any(len(p["text"].strip()) > 30 for p in tier2_pages):
        logger.info("Tier 2 (Tesseract) succeeded for %s", filename)
        return tier2_pages

    # --- Tier 3: EasyOCR ---
    tier3_pages = await _ocr_easyocr(file_content, filename, suffix)
    if tier3_pages and any(len(p["text"].strip()) > 30 for p in tier3_pages):
        logger.info("Tier 3 (EasyOCR) succeeded for %s", filename)
        return tier3_pages

    # --- Tier 4: VLM (Qwen2.5-VL via ModelRouter) ---
    if enable_vlm:
        tier4_pages = await _ocr_vlm(file_content, filename, suffix)
        if tier4_pages:
            logger.info("Tier 4 (VLM) succeeded for %s", filename)
            return tier4_pages

    # Fallback: return whatever we have from Tier 1
    logger.warning("All OCR tiers failed for %s, returning Tier 1 result", filename)
    if suffix == ".pdf":
        return _extract_pdf(file_content)
    return []


async def _ocr_tesseract(
    file_content: bytes, filename: str, suffix: str
) -> List[Dict[str, Any]]:
    """Tier 2: Tesseract OCR for clean printed text."""
    try:
        import pytesseract
        from PIL import Image
        import io

        images = _content_to_images(file_content, suffix)
        pages = []
        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img)
            if text.strip():
                pages.append({
                    "page": i + 1,
                    "text": text.strip(),
                    "metadata": {"ocr_engine": "tesseract"},
                })
        return pages
    except ImportError:
        logger.warning("pytesseract not installed, skipping Tier 2")
        return []
    except Exception as e:
        logger.warning("Tesseract OCR failed for %s: %s", filename, e)
        return []


async def _ocr_easyocr(
    file_content: bytes, filename: str, suffix: str
) -> List[Dict[str, Any]]:
    """Tier 3: EasyOCR for complex/handwritten text."""
    try:
        import easyocr
        import io
        import asyncio

        reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        images = _content_to_images(file_content, suffix)
        pages = []

        for i, img in enumerate(images):
            # EasyOCR works on numpy arrays or file paths
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            # Run in executor since EasyOCR is CPU-bound
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, reader.readtext, img_bytes.getvalue()
            )

            text_parts = [r[1] for r in results if r[1].strip()]
            text = "\n".join(text_parts)
            if text.strip():
                pages.append({
                    "page": i + 1,
                    "text": text.strip(),
                    "metadata": {
                        "ocr_engine": "easyocr",
                        "detection_count": len(results),
                    },
                })
        return pages
    except ImportError:
        logger.warning("easyocr not installed, skipping Tier 3")
        return []
    except Exception as e:
        logger.warning("EasyOCR failed for %s: %s", filename, e)
        return []


async def _ocr_vlm(
    file_content: bytes, filename: str, suffix: str
) -> List[Dict[str, Any]]:
    """Tier 4: Vision Language Model (Qwen2.5-VL) for diagrams/schematics."""
    try:
        from app.orchestrator.model_router import model_router

        IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"}

        if suffix in IMAGE_SUFFIXES:
            # Direct image → VLM
            prompt = (
                "Extract ALL text visible in this image. Include labels, annotations, "
                "numbers, equipment IDs, and any written content. Return only the "
                "extracted text, organized by spatial position."
            )
            text = await model_router.generate_vision(
                prompt=prompt,
                image_bytes=file_content,
                format=None,
            )
            if text and text.strip():
                return [{
                    "page": 1,
                    "text": text.strip(),
                    "metadata": {"ocr_engine": "vlm_qwen25vl"},
                }]
        elif suffix == ".pdf":
            # Convert PDF pages to images and run VLM on each
            images = _content_to_images(file_content, suffix)
            pages = []
            for i, img in enumerate(images[:5]):  # Limit to 5 pages for VLM
                import io
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="PNG")
                prompt = (
                    "Extract ALL text, labels, equipment IDs, annotations, and "
                    "technical content visible in this document page."
                )
                text = await model_router.generate_vision(
                    prompt=prompt,
                    image_bytes=img_bytes.getvalue(),
                    format=None,
                )
                if text and text.strip():
                    pages.append({
                        "page": i + 1,
                        "text": text.strip(),
                        "metadata": {"ocr_engine": "vlm_qwen25vl"},
                    })
            return pages
        return []
    except Exception as e:
        logger.warning("VLM OCR failed for %s: %s", filename, e)
        return []


def _content_to_images(file_content: bytes, suffix: str) -> list:
    """Convert file content (PDF or image bytes) to a list of PIL Images."""
    from PIL import Image
    import io

    IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"}

    if suffix in IMAGE_SUFFIXES:
        img = Image.open(io.BytesIO(file_content))
        return [img]
    elif suffix == ".pdf":
        images = []
        try:
            doc = pymupdf.open(stream=file_content, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Render page at 2x resolution for better OCR
                mat = pymupdf.Matrix(2, 2)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)
            doc.close()
        except Exception as e:
            logger.warning("PDF to image conversion failed: %s", e)
        return images
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
