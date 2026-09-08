"""
KavachAI — Export Router
Implements: FR-RPT-4 (export report as PDF), workflow.md §3 (Workflow C)
Endpoint: POST /investigations/{id}/export (API_Reference.md §6)
"""

import uuid
import os
import re
import time
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.sql_models import Investigation, Session as SessionModel
from app.models.report import ExportRequest, ExportResponse
from app.deps import get_current_session, get_optional_session

router = APIRouter(prefix="/api/v1", tags=["export"])

EXPORTS_DIR = Path("./data/exports").resolve()
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

FILENAME_REGEX = re.compile(r"^exp_[a-zA-Z0-9_\-]+\.pdf$")


def _cleanup_old_exports(max_age_hours: int = 24, max_files: int = 100):
    """
    Clean up exported PDFs older than max_age_hours or if total count exceeds max_files.
    """
    try:
        now = time.time()
        max_age_sec = max_age_hours * 3600
        pdf_files = list(EXPORTS_DIR.glob("*.pdf"))

        # Sort by modification time ascending (oldest first)
        pdf_files.sort(key=lambda p: p.stat().st_mtime)

        for p in pdf_files:
            file_age = now - p.stat().st_mtime
            if file_age > max_age_sec or len(pdf_files) > max_files:
                try:
                    p.unlink(missing_ok=True)
                    pdf_files.remove(p)
                except OSError:
                    pass
    except Exception:
        pass


@router.post("/investigations/{investigation_id}/export", response_model=ExportResponse)
async def export_report(
    investigation_id: str,
    body: ExportRequest,
    background_tasks: BackgroundTasks,
    current_session: SessionModel = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Export investigation report as PDF.
    Implements: FR-RPT-4, workflow.md §3
    """
    result = await db.execute(
        select(Investigation).where(Investigation.id == investigation_id)
    )
    investigation = result.scalar_one_or_none()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if not investigation.report:
        raise HTTPException(status_code=404, detail="Report not available")

    # Trigger background cleanup of old export files
    background_tasks.add_task(_cleanup_old_exports)

    export_id = f"exp_{uuid.uuid4().hex[:8]}"

    if body.format == "pdf":
        pdf_path = EXPORTS_DIR / f"{export_id}.pdf"
        _generate_pdf(investigation.report, pdf_path)

        return ExportResponse(
            export_id=export_id,
            download_url=f"/api/v1/exports/{export_id}.pdf",
        )

    raise HTTPException(status_code=422, detail=f"Unsupported format: {body.format}")


@router.get("/exports/{filename}")
async def download_export(
    filename: str,
    current_session: Optional[SessionModel] = Depends(get_optional_session),
):
    """
    Serve exported PDF files with strict path-traversal protection.
    """
    # Reject path traversal and invalid characters
    if not FILENAME_REGEX.match(filename):
        raise HTTPException(status_code=400, detail="Invalid export filename format")

    file_path = (EXPORTS_DIR / filename).resolve()

    # Ensure resolved path is strictly within the exports directory
    if not str(file_path).startswith(str(EXPORTS_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Export file not found")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=filename,
    )


def _generate_pdf(report: dict, output_path: Path):
    """
    Generate a PDF report using ReportLab.
    Design.md constraint: no blue hyperlink styling — use gold/teal palette.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    styles = getSampleStyleSheet()

    # Custom styles (Design.md palette — no blue)
    title_style = ParagraphStyle(
        'KavachAITitle', parent=styles['Title'],
        textColor=colors.HexColor("#f0c45a"),  # --accent gold
        fontSize=18,
    )
    heading_style = ParagraphStyle(
        'KavachAIHeading', parent=styles['Heading2'],
        textColor=colors.HexColor("#eae8e4"),  # --text
    )
    body_style = ParagraphStyle(
        'KavachAIBody', parent=styles['Normal'],
        textColor=colors.HexColor("#a09da6"),  # --text-2
    )

    elements = []

    # Title
    elements.append(Paragraph("KavachAI Investigation Report", title_style))
    elements.append(Spacer(1, 12))

    # Query
    elements.append(Paragraph(f"Query: {report.get('query', '')}", body_style))
    elements.append(Spacer(1, 8))

    # Status & Confidence
    elements.append(Paragraph(
        f"Status: {report.get('overall_status', 'N/A')} | "
        f"Confidence: {report.get('confidence', 0)}% | "
        f"Verification: {report.get('verification_status', 'N/A')}",
        body_style
    ))
    elements.append(Spacer(1, 16))

    # Findings
    elements.append(Paragraph("Key Findings", heading_style))
    for finding in report.get("findings", []):
        elements.append(Paragraph(
            f"<b>{finding.get('title', '')}</b>: {finding.get('detail', '')} "
            f"[{finding.get('verification_status', '')}]",
            body_style
        ))
        elements.append(Spacer(1, 4))

    elements.append(Spacer(1, 16))

    # Conclusion
    elements.append(Paragraph("Conclusion", heading_style))
    elements.append(Paragraph(report.get("conclusion", ""), body_style))

    doc.build(elements)
