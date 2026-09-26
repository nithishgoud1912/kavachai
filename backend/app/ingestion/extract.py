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
    elif suffix == ".xlsx":
        from app.ingestion.spreadsheet import extract_spreadsheet
        return extract_spreadsheet(file_content, filename)
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

    for table in doc.tables:
        full_text.extend(" | ".join(cell.text for cell in row.cells) for row in table.rows)
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
    import asyncio
    from app.ingestion.limits import validate_container
    validate_container(file_content, filename)
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        # Extract one page at a time so embedded text on page 1 cannot hide scans later.
        import pymupdf
        pages = []
        with pymupdf.open(stream=file_content, filetype="pdf") as document:
            for i, page in enumerate(document):
                text = page.get_text().strip()
                if len(text) >= 50:
                    pages.append({"page": i + 1, "text": text, "metadata": {"ocr_engine": "embedded"}})
                    continue
                if page.rect.width * page.rect.height > 10000000:
                    raise ValueError("PDF page exceeds rendering limit")
                image = await asyncio.to_thread(lambda p=page: p.get_pixmap(dpi=120).tobytes("png"))
                extracted = await extract_text_with_ocr(image, "page.png", enable_vlm)
                if not extracted or not any(p.get("text", "").strip() for p in extracted):
                    logger.warning("Page %d of %s has no text extractable by OCR; treating as visual graphic.", i + 1, filename)
                    pages.append({
                        "page": i + 1,
                        "text": f"[Page {i + 1}: Visual/non-text content]",
                        "metadata": {"ocr_engine": "none", "visual_content": True},
                    })
                    continue
                for result in extracted:
                    result["page"] = i + 1
                pages.extend(extracted)
        return pages
    if suffix not in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"}:
        return await asyncio.to_thread(extract_text, file_content, filename)
    for extractor in (_ocr_tesseract, _ocr_easyocr):
        pages = await extractor(file_content, filename, suffix)
        if pages and any(p.get("text", "").strip() for p in pages):
            return pages
    return await _ocr_vlm(file_content, filename, suffix) if enable_vlm else []


async def _ocr_tesseract(
    file_content: bytes, filename: str, suffix: str
) -> List[Dict[str, Any]]:
    """Tier 2: Tesseract OCR for clean printed text."""
    try:
        import pytesseract
        import asyncio
        from app.config import settings
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        from PIL import Image
        import io

        images = _content_to_images(file_content, suffix)
        pages = []
        for i, img in enumerate(images):
            text = await asyncio.to_thread(pytesseract.image_to_string, img, timeout=60)
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

        reader = easyocr.Reader(["en"], gpu=False, verbose=False, download_enabled=False)
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
