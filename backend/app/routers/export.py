"""
KavachAI — Export Router
Implements: FR-RPT-4 (export report as PDF), workflow.md §3 (Workflow C)
Endpoint: POST /investigations/{id}/export (API_Reference.md §6)
"""

import uuid
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.sql_models import Investigation
from app.models.report import ExportRequest, ExportResponse

router = APIRouter(prefix="/api/v1", tags=["export"])

EXPORTS_DIR = Path("./data/exports")
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/investigations/{investigation_id}/export", response_model=ExportResponse)
async def export_report(
    investigation_id: str,
    body: ExportRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Export investigation report as PDF.
    Implements: FR-RPT-4, workflow.md §3

    Design.md note: no default blue hyperlink styling in PDF.
    """
    result = await db.execute(
        select(Investigation).where(Investigation.id == investigation_id)
    )
    investigation = result.scalar_one_or_none()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if not investigation.report:
        raise HTTPException(status_code=404, detail="Report not available")

    export_id = f"exp_{uuid.uuid4().hex[:4]}"

    if body.format == "pdf":
        pdf_path = EXPORTS_DIR / f"{export_id}.pdf"
        _generate_pdf(investigation.report, pdf_path)

        return ExportResponse(
            export_id=export_id,
            download_url=f"/api/v1/exports/{export_id}.pdf",
        )

    raise HTTPException(status_code=422, detail=f"Unsupported format: {body.format}")


@router.get("/exports/{filename}")
async def download_export(filename: str):
    """Serve exported files."""
    file_path = EXPORTS_DIR / filename
    if not file_path.exists():
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
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch

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
    elements.append(Paragraph(f"KavachAI Investigation Report", title_style))
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
