"""
KavachAI — Unit Tests: Tiered OCR Pipeline
Tests the cascading OCR extraction logic.
All tests use mocking to avoid needing actual OCR engines.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestExtractTextOriginal:
    """Test that the original extract_text() function remains unchanged."""

    def test_txt_extraction(self):
        from app.ingestion.extract import extract_text
        content = b"Hello world, this is a test document."
        result = extract_text(content, "test.txt")
        assert len(result) == 1
        assert result[0]["page"] == 1
        assert "Hello world" in result[0]["text"]

    def test_unsupported_format_returns_empty(self):
        from app.ingestion.extract import extract_text
        result = extract_text(b"data", "file.xyz")
        assert result == []

    def test_image_returns_empty(self):
        from app.ingestion.extract import extract_text
        result = extract_text(b"data", "photo.png")
        assert result == []


class TestExtractTextWithOcr:
    """Test the new async tiered OCR pipeline."""

    @pytest.mark.asyncio
    async def test_non_pdf_non_image_falls_through(self):
        """Non-PDF/non-image files should fall through to standard extract_text."""
        from app.ingestion.extract import extract_text_with_ocr
        content = b"Some text file content here."
        result = await extract_text_with_ocr(content, "readme.txt")
        assert len(result) == 1
        assert "Some text" in result[0]["text"]

    @pytest.mark.asyncio
    async def test_tier1_pdf_with_embedded_text(self):
        """PDF with embedded text should return at Tier 1 without OCR."""
        from app.ingestion.extract import extract_text_with_ocr
        with patch("app.ingestion.extract._extract_pdf") as mock_extract:
            mock_extract.return_value = [
                {"page": 1, "text": "A" * 100, "metadata": {}}
            ]
            result = await extract_text_with_ocr(b"fake-pdf", "doc.pdf", enable_vlm=False)
            assert len(result) == 1
            assert len(result[0]["text"]) > 50

    @pytest.mark.asyncio
    async def test_tier2_tesseract_fallback(self):
        """If Tier 1 has no text, Tier 2 (Tesseract) should be attempted."""
        from app.ingestion.extract import extract_text_with_ocr
        with patch("app.ingestion.extract._extract_pdf", return_value=[]):
            with patch(
                "app.ingestion.extract._ocr_tesseract",
                new_callable=AsyncMock,
                return_value=[{"page": 1, "text": "B" * 50, "metadata": {"ocr_engine": "tesseract"}}],
            ):
                result = await extract_text_with_ocr(b"scanned-pdf", "scan.pdf", enable_vlm=False)
                assert len(result) == 1
                assert result[0]["metadata"]["ocr_engine"] == "tesseract"

    @pytest.mark.asyncio
    async def test_tier3_easyocr_fallback(self):
        """If Tiers 1 and 2 fail, Tier 3 (EasyOCR) should be attempted."""
        from app.ingestion.extract import extract_text_with_ocr
        with patch("app.ingestion.extract._extract_pdf", return_value=[]):
            with patch("app.ingestion.extract._ocr_tesseract", new_callable=AsyncMock, return_value=[]):
                with patch(
                    "app.ingestion.extract._ocr_easyocr",
                    new_callable=AsyncMock,
                    return_value=[{"page": 1, "text": "C" * 50, "metadata": {"ocr_engine": "easyocr"}}],
                ):
                    result = await extract_text_with_ocr(b"handwritten.pdf", "hw.pdf", enable_vlm=False)
                    assert len(result) == 1
                    assert result[0]["metadata"]["ocr_engine"] == "easyocr"

    @pytest.mark.asyncio
    async def test_tier4_vlm_fallback(self):
        """If all prior tiers fail, Tier 4 (VLM) should be attempted when enabled."""
        from app.ingestion.extract import extract_text_with_ocr
        with patch("app.ingestion.extract._extract_pdf", return_value=[]):
            with patch("app.ingestion.extract._ocr_tesseract", new_callable=AsyncMock, return_value=[]):
                with patch("app.ingestion.extract._ocr_easyocr", new_callable=AsyncMock, return_value=[]):
                    with patch(
                        "app.ingestion.extract._ocr_vlm",
                        new_callable=AsyncMock,
                        return_value=[{"page": 1, "text": "VLM extracted text", "metadata": {"ocr_engine": "vlm_qwen25vl"}}],
                    ):
                        result = await extract_text_with_ocr(b"diagram.pdf", "pid.pdf", enable_vlm=True)
                        assert len(result) == 1
                        assert result[0]["metadata"]["ocr_engine"] == "vlm_qwen25vl"

    @pytest.mark.asyncio
    async def test_vlm_disabled_skips_tier4(self):
        """When enable_vlm=False, Tier 4 should not be attempted."""
        from app.ingestion.extract import extract_text_with_ocr
        with patch("app.ingestion.extract._extract_pdf", return_value=[]):
            with patch("app.ingestion.extract._ocr_tesseract", new_callable=AsyncMock, return_value=[]):
                with patch("app.ingestion.extract._ocr_easyocr", new_callable=AsyncMock, return_value=[]):
                    with patch("app.ingestion.extract._ocr_vlm", new_callable=AsyncMock) as mock_vlm:
                        result = await extract_text_with_ocr(b"data", "scan.pdf", enable_vlm=False)
                        mock_vlm.assert_not_called()


class TestContentToImages:
    """Test the _content_to_images helper."""

    def test_image_file_returns_single_image(self):
        from app.ingestion.extract import _content_to_images
        from PIL import Image
        import io

        # Create a small test image
        img = Image.new("RGB", (10, 10), "red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        images = _content_to_images(buf.getvalue(), ".png")
        assert len(images) == 1

    def test_unsupported_suffix_returns_empty(self):
        from app.ingestion.extract import _content_to_images
        images = _content_to_images(b"data", ".xyz")
        assert images == []
