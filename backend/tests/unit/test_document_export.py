"""
KavachAI — Unit Tests for Document Export Service (Person 4 — Exclusive File)
Tests for backend/app/services/document_export.py

Test Cases (per team_implementation_plans.md Task 4.3):
  - test_generate_briefing_docx_creates_file()
  - test_docx_contains_classification_header()
  - test_docx_contains_signature_block()
  - test_generate_incident_xlsx_has_two_sheets()
  - test_xlsx_severity_color_coding()
  - test_generate_briefing_pptx_has_five_slides()
  - test_generate_all_exports_returns_three_items()

Run with:
  cd backend && python -m pytest tests/unit/test_document_export.py -v
"""

import os
import asyncio
import tempfile
import uuid
import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── Fixtures ─────────────────────────────────────────────────────────────────

SAMPLE_REPORT = {
    "query": "What is the vibration status of pump P-102?",
    "overall_status": "attention_required",
    "confidence": 91,
    "verification_status": "verified",
    "condition_summary": "Potential deterioration detected",
    "conclusion": (
        "Pump P-102 shows a 76% increase in vibration from 2.1 mm/s (Jan) to 3.7 mm/s (Jul), "
        "exceeding the ISO 10816-3 Zone B attention threshold of 3.0 mm/s. "
        "Immediate inspection recommended."
    ),
    "recommendations": (
        "1. Schedule laser shaft alignment inspection at next maintenance window.\n"
        "2. Conduct high-frequency vibration spectral analysis.\n"
        "3. Increase monitoring from monthly to bi-weekly."
    ),
    "findings": [
        {
            "id": "f1",
            "title": "Increasing vibration trend",
            "detail": "Jan 2.1 → Apr 2.8 → Jul 3.7 mm/s (+76%)",
            "verification_status": "supported",
            "evidence": [
                {"label": "Inspection Report 2026-07", "source_id": "doc_1120", "page": 3},
            ],
        },
        {
            "id": "f2",
            "title": "Exceeds ISO 10816-3 attention threshold",
            "detail": "Current 3.7 mm/s > spec 3.0 mm/s",
            "verification_status": "supported",
            "evidence": [
                {"label": "Pump Operating Manual §4.2", "source_id": "doc_1130", "page": 12},
            ],
        },
    ],
}


@pytest.fixture
def investigation_id() -> str:
    return f"test_{uuid.uuid4().hex[:12]}"


@pytest.fixture
def tmp_exports(tmp_path, monkeypatch):
    """Redirect exports to pytest tmp_path to avoid polluting real data/exports/."""
    # Patch _exports_dir inside the service module to use tmp_path
    def _mock_exports_dir(inv_id: str) -> Path:
        p = tmp_path / "exports" / inv_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    monkeypatch.setattr(
        "app.services.document_export._exports_dir",
        _mock_exports_dir,
    )
    return tmp_path


# ── Helper ────────────────────────────────────────────────────────────────────

def run_async(coro):
    """Run an async coroutine synchronously in tests."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Tests: DOCX ───────────────────────────────────────────────────────────────

class TestGenerateBriefingDocx:

    def test_generate_briefing_docx_creates_file(self, investigation_id, tmp_exports):
        """File must exist and end with .docx after generation."""
        from app.services.document_export import generate_briefing_docx

        filepath = run_async(
            generate_briefing_docx(investigation_id, "Test content", report=SAMPLE_REPORT)
        )

        assert filepath.endswith(".docx"), "Output file must be a .docx"
        assert os.path.isfile(filepath), f"File does not exist: {filepath}"
        assert os.path.getsize(filepath) > 0, "Generated .docx must not be empty"

    def test_docx_contains_classification_header(self, investigation_id, tmp_exports):
        """Document must contain CONFIDENTIAL classification marking."""
        from docx import Document
        from app.services.document_export import generate_briefing_docx

        filepath = run_async(
            generate_briefing_docx(investigation_id, "Test content", report=SAMPLE_REPORT)
        )

        doc = Document(filepath)
        full_text = "\n".join(p.text for p in doc.paragraphs)
        assert "CONFIDENTIAL" in full_text, (
            "CONFIDENTIAL classification header missing from .docx"
        )

    def test_docx_contains_mrpl_header(self, investigation_id, tmp_exports):
        """Document must contain MRPL organisation header."""
        from docx import Document
        from app.services.document_export import generate_briefing_docx

        filepath = run_async(
            generate_briefing_docx(investigation_id, "Test content", report=SAMPLE_REPORT)
        )

        doc = Document(filepath)
        full_text = "\n".join(p.text for p in doc.paragraphs)
        assert "MANGALORE REFINERY" in full_text, (
            "MRPL organisation header missing from .docx"
        )

    def test_docx_contains_signature_block(self, investigation_id, tmp_exports):
        """Document must contain approval signature fields."""
        from docx import Document
        from app.services.document_export import generate_briefing_docx

        filepath = run_async(
            generate_briefing_docx(investigation_id, "Test content", report=SAMPLE_REPORT)
        )

        doc = Document(filepath)
        # Check tables for signature fields
        sig_found = False
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if "Approving Officer" in cell.text or "HOD" in cell.text or "General Manager" in cell.text:
                        sig_found = True
                        break
        assert sig_found, "Signature / approval block table missing from .docx"

    def test_docx_contains_investigation_id(self, investigation_id, tmp_exports):
        """Document must embed the investigation ID."""
        from docx import Document
        from app.services.document_export import generate_briefing_docx

        filepath = run_async(
            generate_briefing_docx(investigation_id, "Test content", report=SAMPLE_REPORT)
        )

        doc = Document(filepath)
        # Check all text (paragraphs + tables)
        all_text = "\n".join(p.text for p in doc.paragraphs)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    all_text += cell.text

        assert investigation_id in all_text, (
            f"Investigation ID '{investigation_id}' not found in .docx content"
        )

    def test_docx_works_without_report(self, investigation_id, tmp_exports):
        """generate_briefing_docx must not crash when report=None."""
        from app.services.document_export import generate_briefing_docx

        filepath = run_async(
            generate_briefing_docx(investigation_id, "Minimal content only", report=None)
        )
        assert os.path.isfile(filepath)


# ── Tests: XLSX ───────────────────────────────────────────────────────────────

class TestGenerateIncidentXlsx:

    def test_generate_incident_xlsx_creates_file(self, investigation_id, tmp_exports):
        """File must exist and end with .xlsx after generation."""
        from app.services.document_export import generate_incident_xlsx

        filepath = run_async(
            generate_incident_xlsx(investigation_id, report=SAMPLE_REPORT)
        )

        assert filepath.endswith(".xlsx"), "Output file must be a .xlsx"
        assert os.path.isfile(filepath), f"File does not exist: {filepath}"
        assert os.path.getsize(filepath) > 0, "Generated .xlsx must not be empty"

    def test_generate_incident_xlsx_has_three_sheets(self, investigation_id, tmp_exports):
        """Workbook must have exactly 3 sheets: Incident Log, Telemetry Data, Vibration Calculator."""
        from openpyxl import load_workbook
        from app.services.document_export import generate_incident_xlsx

        filepath = run_async(
            generate_incident_xlsx(investigation_id, report=SAMPLE_REPORT)
        )

        wb = load_workbook(filepath)
        sheet_names = wb.sheetnames
        assert "Incident Log" in sheet_names, "Sheet 'Incident Log' missing"
        assert "Telemetry Data" in sheet_names, "Sheet 'Telemetry Data' missing"
        assert "Vibration Calculator" in sheet_names, "Sheet 'Vibration Calculator' missing"
        assert len(sheet_names) == 3, f"Expected 3 sheets, got: {sheet_names}"

    def test_xlsx_incident_log_has_header_row(self, investigation_id, tmp_exports):
        """Incident Log sheet must have a styled header row with expected column names."""
        from openpyxl import load_workbook
        from app.services.document_export import generate_incident_xlsx

        filepath = run_async(
            generate_incident_xlsx(investigation_id, report=SAMPLE_REPORT)
        )

        wb = load_workbook(filepath)
        ws = wb["Incident Log"]

        # Row 1 is title, row 2 is header
        header_values = [ws.cell(row=2, column=ci).value for ci in range(1, 8)]
        assert "Finding Title" in header_values, (
            f"'Finding Title' column not found in header row: {header_values}"
        )
        assert "Verification Status" in header_values, (
            f"'Verification Status' column not found: {header_values}"
        )

    def test_xlsx_severity_color_coding(self, investigation_id, tmp_exports):
        """Severity column cells must have fill colours applied."""
        from openpyxl import load_workbook
        from app.services.document_export import generate_incident_xlsx

        report_with_findings = dict(SAMPLE_REPORT)
        filepath = run_async(
            generate_incident_xlsx(investigation_id, report=report_with_findings)
        )

        wb = load_workbook(filepath)
        ws = wb["Incident Log"]

        # Find severity column (column 6 in our layout, after title row offset)
        has_fill = False
        for row in ws.iter_rows(min_row=3, max_col=8):  # skip title + header
            for cell in row:
                if cell.fill and cell.fill.fgColor and cell.fill.fgColor.rgb not in ("00000000", "FFFFFFFF", None):
                    has_fill = True
                    break

        assert has_fill, "No colour fills detected in Incident Log — severity colour coding missing"

    def test_xlsx_telemetry_sheet_has_headers(self, investigation_id, tmp_exports):
        """Telemetry Data sheet must have correct column headers."""
        from openpyxl import load_workbook
        from app.services.document_export import generate_incident_xlsx

        filepath = run_async(
            generate_incident_xlsx(investigation_id, report=SAMPLE_REPORT)
        )

        wb = load_workbook(filepath)
        ws = wb["Telemetry Data"]

        header_values = [ws.cell(row=2, column=ci).value for ci in range(1, 9)]
        assert "Equipment ID" in header_values, "'Equipment ID' missing from Telemetry Data header"
        assert "Breach?" in header_values, "'Breach?' column missing from Telemetry Data"

    def test_xlsx_works_without_report(self, investigation_id, tmp_exports):
        """generate_incident_xlsx must not crash when report=None (uses default sample data)."""
        from app.services.document_export import generate_incident_xlsx

        filepath = run_async(
            generate_incident_xlsx(investigation_id, report=None)
        )
        assert os.path.isfile(filepath)


# ── Tests: PPTX ───────────────────────────────────────────────────────────────

class TestGenerateBriefingPptx:

    def test_generate_briefing_pptx_creates_file(self, investigation_id, tmp_exports):
        """File must exist and end with .pptx after generation."""
        from app.services.document_export import generate_briefing_pptx

        filepath = run_async(
            generate_briefing_pptx(investigation_id, report=SAMPLE_REPORT)
        )

        assert filepath.endswith(".pptx"), "Output file must be a .pptx"
        assert os.path.isfile(filepath), f"File does not exist: {filepath}"
        assert os.path.getsize(filepath) > 0, "Generated .pptx must not be empty"

    def test_generate_briefing_pptx_has_five_slides(self, investigation_id, tmp_exports):
        """Presentation must have exactly 5 slides."""
        from pptx import Presentation
        from app.services.document_export import generate_briefing_pptx

        filepath = run_async(
            generate_briefing_pptx(investigation_id, report=SAMPLE_REPORT)
        )

        prs = Presentation(filepath)
        assert len(prs.slides) == 5, (
            f"Expected 5 slides, got {len(prs.slides)}"
        )

    def test_pptx_title_slide_contains_mrpl(self, investigation_id, tmp_exports):
        """Title slide must mention MRPL."""
        from pptx import Presentation
        from app.services.document_export import generate_briefing_pptx

        filepath = run_async(
            generate_briefing_pptx(investigation_id, report=SAMPLE_REPORT)
        )

        prs = Presentation(filepath)
        slide_1 = prs.slides[0]

        all_text = " ".join(
            shape.text_frame.text
            for shape in slide_1.shapes
            if shape.has_text_frame
        )
        assert "MANGALORE REFINERY" in all_text, (
            "Title slide does not contain MRPL organisation name"
        )

    def test_pptx_contains_investigation_query(self, investigation_id, tmp_exports):
        """Title slide must show the investigation query."""
        from pptx import Presentation
        from app.services.document_export import generate_briefing_pptx

        filepath = run_async(
            generate_briefing_pptx(investigation_id, report=SAMPLE_REPORT)
        )

        prs = Presentation(filepath)
        slide_1 = prs.slides[0]

        all_text = " ".join(
            shape.text_frame.text
            for shape in slide_1.shapes
            if shape.has_text_frame
        )
        assert "P-102" in all_text or "vibration" in all_text.lower(), (
            "Investigation query not reflected in title slide"
        )

    def test_pptx_works_without_report(self, investigation_id, tmp_exports):
        """generate_briefing_pptx must not crash when report=None."""
        from app.services.document_export import generate_briefing_pptx

        filepath = run_async(
            generate_briefing_pptx(investigation_id, report=None)
        )
        assert os.path.isfile(filepath)


# ── Tests: generate_all_exports ───────────────────────────────────────────────

class TestGenerateAllExports:

    def test_generate_all_exports_returns_three_items(self, investigation_id, tmp_exports):
        """generate_all_exports must return a list of exactly 3 export dicts."""
        from app.services.document_export import generate_all_exports

        results = run_async(
            generate_all_exports(investigation_id, report=SAMPLE_REPORT)
        )

        assert isinstance(results, list), "Return value must be a list"
        assert len(results) == 3, f"Expected 3 exports, got {len(results)}"

    def test_generate_all_exports_format_keys(self, investigation_id, tmp_exports):
        """Each export dict must have 'format', 'path', and 'label' keys."""
        from app.services.document_export import generate_all_exports

        results = run_async(
            generate_all_exports(investigation_id, report=SAMPLE_REPORT)
        )

        formats_returned = {item["format"] for item in results}
        assert formats_returned == {"docx", "xlsx", "pptx"}, (
            f"Expected formats {{docx, xlsx, pptx}}, got {formats_returned}"
        )

        for item in results:
            assert "format" in item, "Missing 'format' key"
            assert "path" in item,   "Missing 'path' key"
            assert "label" in item,  "Missing 'label' key"

    def test_generate_all_exports_all_files_exist(self, investigation_id, tmp_exports):
        """All three generated files must exist on disk."""
        from app.services.document_export import generate_all_exports

        results = run_async(
            generate_all_exports(investigation_id, report=SAMPLE_REPORT)
        )

        for item in results:
            assert os.path.isfile(item["path"]), (
                f"Export file missing for format '{item['format']}': {item['path']}"
            )
            assert os.path.getsize(item["path"]) > 0, (
                f"Export file is empty for format '{item['format']}'"
            )

    def test_generate_all_exports_works_without_report(self, investigation_id, tmp_exports):
        """generate_all_exports must not crash when report=None."""
        from app.services.document_export import generate_all_exports

        results = run_async(
            generate_all_exports(investigation_id, report=None)
        )
        assert len(results) == 3
