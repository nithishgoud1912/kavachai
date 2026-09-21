"""
KavachAI — Exports Router (Person 4 — Exclusive File)
Provides REST API endpoints for downloading investigation deliverables:
  GET  /api/v1/exports/{investigation_id}/{format}  — download single format
  POST /api/v1/exports/{investigation_id}/generate-all — generate all formats

Person 4 owns this file exclusively.
Person 1 (main.py integrator) will add:
    from app.routers import exports
    app.include_router(exports.router)
"""

import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.sql_models import Investigation
from app.deps import get_current_session, get_optional_session
from app.db.sql_models import Session as SessionModel
from app.services.document_export import (
    generate_briefing_docx,
    generate_incident_xlsx,
    generate_briefing_pptx,
    generate_all_exports,
)

router = APIRouter(prefix="/api/v1/exports", tags=["exports"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIME_TYPES = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

FILE_NAMES = {
    "docx": "note_for_approval.docx",
    "xlsx": "incident_log.xlsx",
    "pptx": "briefing_deck.pptx",
}

EXPORT_LABELS = {
    "docx": "Note for Approval (NFA)",
    "xlsx": "Incident Log & Telemetry Matrix",
    "pptx": "Executive Briefing Deck (PPTX)",
}

SUPPORTED_FORMATS = set(MIME_TYPES.keys())

# Resolve backend data directory
BACKEND_DIR  = Path(__file__).resolve().parent.parent.parent
EXPORTS_BASE = (BACKEND_DIR / "data" / "exports").resolve()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _export_path(investigation_id: str, fmt: str) -> Path:
    return EXPORTS_BASE / investigation_id / FILE_NAMES[fmt]


async def _get_investigation(
    investigation_id: str,
    session: SessionModel,
    db: AsyncSession,
) -> Investigation:
    """
    Fetch investigation by ID, scoped to the calling session.
    Raises 404 if not found or not owned by this session.
    """
    result = await db.execute(
        select(Investigation).where(
            Investigation.id == investigation_id,
            Investigation.session_id == session.id,
        )
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found or you do not have access to it.",
        )
    return inv


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/{investigation_id}/{format}",
    summary="Download investigation deliverable",
    description=(
        "Download the investigation report as a specified file format.\n\n"
        "Supported formats: `docx` (Note for Approval), `xlsx` (Incident Log + Telemetry), "
        "`pptx` (Executive Briefing Deck).\n\n"
        "If the file has not yet been generated, it is created on-the-fly and cached."
    ),
)
async def export_investigation(
    investigation_id: str,
    format: str,
    session: SessionModel = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /api/v1/exports/{investigation_id}/{format}

    Download an investigation deliverable.
    Generates the file if not already cached.

    Path Params:
        investigation_id: UUID of the investigation.
        format: One of 'docx', 'xlsx', 'pptx'.

    Auth:
        Session token via Authorization: Bearer <token> or X-Session-ID header.

    Returns:
        File download response with appropriate MIME type.
    """
    # Validate format
    if format not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported format '{format}'. Must be one of: {', '.join(sorted(SUPPORTED_FORMATS))}",
        )

    # Authenticate & authorise
    inv = await _get_investigation(investigation_id, session, db)

    # Check if file is already cached
    cached_path = _export_path(investigation_id, format)

    if not cached_path.exists():
        # Generate fresh deliverable
        report: dict = inv.report if inv.report else {}

        generators = {
            "docx": lambda: generate_briefing_docx(
                investigation_id,
                report.get("conclusion", report.get("condition_summary", "")),
                report=report,
            ),
            "xlsx": lambda: generate_incident_xlsx(investigation_id, report=report),
            "pptx": lambda: generate_briefing_pptx(investigation_id, report=report),
        }

        try:
            filepath = await generators[format]()
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate {format.upper()} export: {str(exc)}",
            )
    else:
        filepath = str(cached_path)

    # Serve file
    return FileResponse(
        path=filepath,
        media_type=MIME_TYPES[format],
        filename=f"kavachai_mrpl_{investigation_id[:8]}.{format}",
        headers={
            "Content-Disposition": (
                f'attachment; filename="kavachai_mrpl_{investigation_id[:8]}.{format}"'
            ),
            "X-KavachAI-Sovereignty": "Air-Gapped | Zero External Egress",
            "X-KavachAI-Format": EXPORT_LABELS[format],
        },
    )


@router.post(
    "/{investigation_id}/generate-all",
    summary="Generate all deliverable formats",
    description=(
        "Pre-generate and cache all three deliverable formats (DOCX, XLSX, PPTX) "
        "for an investigation. Returns download URLs for all three."
    ),
)
async def generate_all(
    investigation_id: str,
    session: SessionModel = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """
    POST /api/v1/exports/{investigation_id}/generate-all

    Generate all export formats (DOCX, XLSX, PPTX) for an investigation.
    Files are cached in data/exports/{investigation_id}/.

    Auth:
        Session token via Authorization: Bearer <token> or X-Session-ID header.

    Returns:
        {
          "investigation_id": "...",
          "exports": [
            {"format": "docx", "download_url": "...", "label": "Note for Approval"},
            {"format": "xlsx", "download_url": "...", "label": "Incident Log & Telemetry"},
            {"format": "pptx", "download_url": "...", "label": "Executive Briefing Deck"},
          ]
        }
    """
    inv = await _get_investigation(investigation_id, session, db)

    report: dict = inv.report if inv.report else {}

    try:
        export_results = await generate_all_exports(investigation_id, report=report)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Export generation failed: {str(exc)}",
        )

    return {
        "investigation_id": investigation_id,
        "exports": [
            {
                "format":       item["format"],
                "download_url": f"/api/v1/exports/{investigation_id}/{item['format']}",
                "label":        item["label"],
                "path":         item["path"],
            }
            for item in export_results
        ],
    }


@router.get(
    "/{investigation_id}/status",
    summary="Check which export formats are cached",
    description="Returns which deliverable formats have already been generated and cached.",
)
async def export_status(
    investigation_id: str,
    session: SessionModel = Depends(get_optional_session),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /api/v1/exports/{investigation_id}/status

    Returns cache status for each export format.

    Returns:
        {
          "investigation_id": "...",
          "formats": {
            "docx": {"cached": true,  "download_url": "...", "label": "..."},
            "xlsx": {"cached": false, "download_url": "...", "label": "..."},
            "pptx": {"cached": true,  "download_url": "...", "label": "..."},
          }
        }
    """
    formats_status = {}
    for fmt in sorted(SUPPORTED_FORMATS):
        cached = _export_path(investigation_id, fmt).exists()
        formats_status[fmt] = {
            "cached":       cached,
            "download_url": f"/api/v1/exports/{investigation_id}/{fmt}",
            "label":        EXPORT_LABELS[fmt],
        }

    return {
        "investigation_id": investigation_id,
        "formats": formats_status,
    }
