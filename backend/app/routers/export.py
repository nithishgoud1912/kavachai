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
    Design.md constraint: Warm Minimal palette (#2d2a26, #c45d3e, #eee8df).
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=45,
        bottomMargin=45,
    )
    styles = getSampleStyleSheet()

    c_primary = colors.HexColor("#2d2a26")
    c_accent = colors.HexColor("#c45d3e")
    c_text2 = colors.HexColor("#655f56")
    c_border = colors.HexColor("#e2dacd")
    c_green = colors.HexColor("#2d7a4d")

    title_style = ParagraphStyle(
        'KavachAITitle', parent=styles['Title'],
        fontName='Helvetica-Bold',
        textColor=c_accent,
        fontSize=18,
        leading=22,
        alignment=0,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'KavachAISubtitle', parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=c_text2,
        spaceAfter=10,
    )
    heading_style = ParagraphStyle(
        'KavachAIHeading', parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        textColor=c_accent,
        fontSize=11,
        leading=15,
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        'KavachAIBody', parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_primary,
    )
    meta_style = ParagraphStyle(
        'KavachAIMeta', parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=c_text2,
    )

    elements = []

    # Title & Subtitle
    elements.append(Paragraph("KavachAI Investigation Report", title_style))
    elements.append(Paragraph("Sovereign Industrial Agentic AI Workbench · Confidential Plant Operations", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=c_accent, spaceBefore=0, spaceAfter=8))

    # Query & Status Box
    status_str = report.get('overall_status', 'N/A').upper().replace('_', ' ')
    conf_str = f"{report.get('confidence', 0)}%"
    verif_str = report.get('verification_status', 'N/A').upper()

    header_data = [
        [
            Paragraph(f"<b>Query:</b> <i>{report.get('query', '')}</i>", body_style),
        ],
        [
            Paragraph(
                f"<b>Status:</b> <font color='#c45d3e'><b>{status_str}</b></font> &nbsp;|&nbsp; "
                f"<b>Confidence:</b> <font color='#2d7a4d'><b>{conf_str}</b></font> &nbsp;|&nbsp; "
                f"<b>Verification:</b> <font color='#2d7a4d'><b>{verif_str}</b></font>",
                body_style
            ),
        ]
    ]
    header_table = Table(header_data, colWidths=[523])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8f6f1")),
        ('BOX', (0,0), (-1,-1), 0.75, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    # Findings
    elements.append(Paragraph("Key Findings & Grounded Evidence", heading_style))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=c_border, spaceBefore=0, spaceAfter=6))
    
    for i, finding in enumerate(report.get("findings", [])):
        f_title = finding.get('title', '')
        f_detail = finding.get('detail', '')
        f_status = finding.get('verification_status', '').upper()
        
        evidence_items = []
        for ev in finding.get('evidence', []):
            lbl = ev.get('label', ev.get('source_id', 'Evidence'))
            p = f", p. {ev.get('page')}" if ev.get('page') else ""
            s = f", §{ev.get('section')}" if ev.get('section') else ""
            evidence_items.append(f"{lbl}{p}{s}")
        ev_str = " &bull; ".join(evidence_items) if evidence_items else "Internal Telemetry"

        finding_data = [
            [
                Paragraph(f"<b>{i+1}. {f_title}</b>", body_style),
                Paragraph(f"<font color='#2d7a4d'><b>[{f_status}]</b></font>", ParagraphStyle('R', parent=body_style, alignment=2)),
            ],
            [
                Paragraph(f"{f_detail}", body_style),
                Paragraph("", body_style),
            ],
            [
                Paragraph(f"<font color='#655f56'><b>Evidence:</b> {ev_str}</font>", meta_style),
                Paragraph("", meta_style),
            ]
        ]
        finding_table = Table(finding_data, colWidths=[440, 83])
        finding_table.setStyle(TableStyle([
            ('SPAN', (0,1), (1,1)),
            ('SPAN', (0,2), (1,2)),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fdfcfa")),
            ('BOX', (0,0), (-1,-1), 0.5, c_border),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(finding_table)
        elements.append(Spacer(1, 6))

    elements.append(Spacer(1, 6))

    # Conclusion
    elements.append(Paragraph("Synthesized Conclusion", heading_style))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=c_border, spaceBefore=0, spaceAfter=6))
    
    concl_data = [[
        Paragraph(f"<b>Engineering Summary:</b><br/>{report.get('conclusion', '')}", body_style)
    ]]
    concl_table = Table(concl_data, colWidths=[523])
    concl_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fbf9f5")),
        ('BOX', (0,0), (-1,-1), 1, c_accent),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(concl_table)
    elements.append(Spacer(1, 10))

    # Sign-off footer
    elements.append(Paragraph(
        "CONFIDENTIAL · Verified by KavachAI On-Premise Inference Engine · Zero External Network Transmission",
        meta_style
    ))

    doc.build(elements)

