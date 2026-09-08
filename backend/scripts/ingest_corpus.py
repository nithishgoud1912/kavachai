"""
KavachAI — Corpus Ingestion Script
Implements: FR-ING-1..7, workflow.md §1 (Knowledge Base Ingestion),
            PRD §5 (Demo Corpus), Decision Q1 (Synthetic Corpus)

Generates and ingests the demo corpus:
  - 7 Document PDFs (Inspection reports Jan/Apr/Jul, Manual, Maintenance log, SOP, Process Flow)
  - 1 P&ID Drawing (PNG, T-101 -> P-102 -> V-204 -> R-101)
  - 1 Time-Series Dataset (CSV, 214 rows: vibration 2.1->2.8->3.7 mm/s, temp 68->71->77°C)

Matches exact contracts from API_Reference.md §3, §4, §5.
"""

import os
import sys
import asyncio
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PIL import Image, ImageDraw

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.database import init_db, async_session
from app.db.sql_models import Document, Dataset
from app.db.object_store import object_store
from app.db.vector_store import vector_store
from app.ingestion.extract import extract_text, get_page_count
from app.ingestion.chunk import chunk_pages
from app.ingestion.tag import tag_chunks
from app.ingestion.embed import generate_embeddings
from app.ingestion.tabular import parse_tabular_file
from sqlalchemy import select, func


CORPUS_DIR = Path("./corpus")
CORPUS_DIR.mkdir(parents=True, exist_ok=True)


def _create_pdf(filepath: Path, title: str, sections: list[tuple[str, str]]):
    """Generate a clean PDF using ReportLab."""
    doc = SimpleDocTemplate(str(filepath), pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        spaceAfter=12,
        textColor='#1E293B'
    )
    heading_style = ParagraphStyle(
        'SectionHead',
        parent=styles['Heading2'],
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=4,
        textColor='#0F766E'
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor='#334155'
    )

    story = [Paragraph(title, title_style), Spacer(1, 8)]
    for head, text in sections:
        if head:
            story.append(Paragraph(head, heading_style))
        story.append(Paragraph(text.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 6))
    
    doc.build(story)


def _create_pid_image(filepath: Path):
    """Generate a clear P&ID diagram PNG showing T-101 -> P-102 -> V-204 -> R-101."""
    img = Image.new("RGB", (900, 320), color="#F8FAFC")
    draw = ImageDraw.Draw(img)

    blocks = [
        (40, 90, 180, 210, "T-101", "Feed Tank\n(Crude Storage)"),
        (260, 110, 390, 190, "P-102", "Centrifugal Pump\n(Charge Pump)"),
        (480, 100, 610, 200, "V-204", "Control Valve\n(Flow Control)"),
        (700, 80, 850, 220, "R-101", "Reactor\n(Hydrotreater)"),
    ]

    # Draw flow lines (arrows)
    draw.line([(180, 150), (260, 150)], fill="#0F766E", width=4)
    draw.polygon([(260, 150), (250, 145), (250, 155)], fill="#0F766E")

    draw.line([(390, 150), (480, 150)], fill="#0F766E", width=4)
    draw.polygon([(480, 150), (470, 145), (470, 155)], fill="#0F766E")

    draw.line([(610, 150), (700, 150)], fill="#0F766E", width=4)
    draw.polygon([(700, 150), (690, 145), (690, 155)], fill="#0F766E")

    # Draw blocks & text
    for x1, y1, x2, y2, tag, label in blocks:
        draw.rectangle([x1, y1, x2, y2], fill="#FFFFFF", outline="#0F766E", width=2)
        draw.rectangle([x1, y1, x2, y1 + 28], fill="#0F766E")
        draw.text((x1 + 10, y1 + 6), tag, fill="#FFFFFF")
        draw.text((x1 + 10, y1 + 36), label, fill="#1E293B")

    draw.text((40, 25), "UNIT 101 — CRUDE CHARGE PROCESS & INSTRUMENTATION DIAGRAM (P&ID)", fill="#0F172A")
    draw.text((40, 48), "Drawing No: PID-U101-001 | Revision: 3.1 | Scope: T-101 -> P-102 -> V-204 -> R-101", fill="#64748B")

    img.save(str(filepath))


def _create_telemetry_csv(filepath: Path):
    """
    Generate telemetry CSV with exactly 214 rows (per API_Reference.md §3 line 90).
    Spans Jan 1, 2026 to Jul 18, 2026 for equipment P-102:
      - vibration: 2.1 -> 2.8 -> 3.7 mm/s
      - temperature: 68.0 -> 71.0 -> 77.0 °C
    """
    rows = []
    start_date = datetime(2026, 1, 1, 8, 0, 0)
    
    # 107 daily intervals * 2 metrics = 214 rows
    for i in range(107):
        current_time = start_date + timedelta(days=i * 1.86)
        ts = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        progress = i / 106.0

        if progress < 0.5:
            vib = 2.1 + (progress / 0.5) * (2.8 - 2.1)
            temp = 68.0 + (progress / 0.5) * (71.0 - 68.0)
        else:
            p2 = (progress - 0.5) / 0.5
            vib = 2.8 + p2 * (3.7 - 2.8)
            temp = 71.0 + p2 * (77.0 - 71.0)

        rows.append({
            "timestamp": ts,
            "equipment_id": "P-102",
            "metric": "vibration",
            "value": round(vib, 2),
            "unit": "mm/s",
        })
        rows.append({
            "timestamp": ts,
            "equipment_id": "P-102",
            "metric": "temperature",
            "value": round(temp, 1),
            "unit": "C",
        })

    df = pd.DataFrame(rows[:214])
    df.to_csv(filepath, index=False)


def generate_demo_corpus():
    """Generates the 9 synthetic demo corpus files in ./corpus."""
    print("Generating synthetic demo corpus files...")

    # 1. P-102 Jan Inspection
    _create_pdf(
        CORPUS_DIR / "P-102_Inspection_Jan.pdf",
        "CENTRIFUGAL PUMP P-102 ROUTINE INSPECTION REPORT (JANUARY 2026)",
        [
            ("1.0 Equipment Identification",
             "Asset ID: P-102\nEquipment Description: Centrifugal Crude Charge Pump\nUnit: Unit 101 — Crude Distillation\nInspection Date: 2026-01-15\nLead Reliability Engineer: R. Sharma"),
            ("2.0 Measured Operating Parameters",
             "Pump P-102 baseline condition post-overhaul:\n- Overall Vibration Velocity (RMS): 2.1 mm/s (Acceptable, baseline normal)\n- Drive End Bearing Temperature: 68°C\n- Non-Drive End Bearing Temperature: 65°C\n- Discharge Pressure: 14.2 bar\n- Suction Pressure: 2.1 bar"),
            ("3.0 Findings & Status",
             "Pump P-102 — Vibration: 2.1 mm/s. Temperature: 68°C. Status: Normal. Operating well within manufacturer baseline.")
        ]
    )

    # 2. P-102 Apr Inspection
    _create_pdf(
        CORPUS_DIR / "P-102_Inspection_Apr.pdf",
        "CENTRIFUGAL PUMP P-102 ROUTINE INSPECTION REPORT (APRIL 2026)",
        [
            ("1.0 Equipment Identification",
             "Asset ID: P-102\nEquipment Description: Centrifugal Crude Charge Pump\nUnit: Unit 101 — Crude Distillation\nInspection Date: 2026-04-18\nLead Reliability Engineer: R. Sharma"),
            ("2.0 Measured Operating Parameters",
             "Pump P-102 quarterly condition monitoring:\n- Overall Vibration Velocity (RMS): 2.8 mm/s (Moderate elevation noted)\n- Drive End Bearing Temperature: 71°C\n- Non-Drive End Bearing Temperature: 69°C\n- Discharge Pressure: 14.0 bar\n- Suction Pressure: 2.0 bar"),
            ("3.0 Findings & Status",
             "Pump P-102 — Vibration: 2.8 mm/s. Temperature: 71°C. Status: Acceptable. Slight elevation noted from Jan baseline (2.1 mm/s -> 2.8 mm/s). Continued quarterly monitoring advised.")
        ]
    )

    # 3. P-102 Jul Inspection
    _create_pdf(
        CORPUS_DIR / "P-102_Inspection_Jul.pdf",
        "CENTRIFUGAL PUMP P-102 CONDITION INSPECTION REPORT (JULY 2026)",
        [
            ("1.0 Equipment Identification",
             "Asset ID: P-102\nEquipment Description: Centrifugal Crude Charge Pump\nUnit: Unit 101 — Crude Distillation\nInspection Date: 2026-07-14\nLead Vibration Specialist: A. Verma"),
            ("2.0 Measured Operating Parameters",
             "Pump P-102 urgent assessment following vibration telemetry alert:\n- Overall Vibration Velocity (RMS): 3.7 mm/s (ABNORMAL — Threshold Exceeded)\n- Drive End Bearing Temperature: 77°C (Elevated)\n- Non-Drive End Bearing Temperature: 74°C\n- Discharge Pressure: 13.8 bar\n- Acoustic Analysis: Audible bearing rumble detected"),
            ("3.0 Findings & Recommendations",
             "Pump P-102 — Vibration: 3.7 mm/s. Temperature: 77°C. Status: Abnormal. Measured overall vibration of 3.7 mm/s breaches the manufacturer attention threshold of 3.0 mm/s specified in Section 4.2 of the operating manual. Increasing vibration: Jan 2.1 -> Apr 2.8 -> Jul 3.7 mm/s (+76%). Engineering inspection recommended. The evidence does NOT establish imminent catastrophic failure.")
        ]
    )

    # 4. Pump Operating Manual
    _create_pdf(
        CORPUS_DIR / "P-102_Pump_Operating_Manual.pdf",
        "HEAVY-DUTY CENTRIFUGAL PUMP HCP-200 OPERATING MANUAL (P-102)",
        [
            ("Section 1.0 Design & Specifications",
             "Model: HCP-200 Heavy Duty Centrifugal Pump\nDesign Service: Unit 101 Crude Charge P-102\nRated Flow: 450 m3/h | Rated Head: 160 m"),
            ("Section 4.0 Operating Limits and Standards",
             "Safe continuous operating limits for Model HCP-200."),
            ("Section 4.2 Vibration and Temperature Limits",
             "Operating threshold for this pump model:\n- Continuous acceptable vibration velocity (RMS): below 2.8 mm/s.\n- The attention threshold for continuous operation of Pump P-102 is 3.0 mm/s. When vibration velocity exceeds 3.0 mm/s, an immediate engineering inspection and spectrum analysis must be initiated.\n- Emergency trip threshold: 4.5 mm/s.\n- Maximum allowable bearing operating temperature: 85°C; advisory threshold: 75°C.")
        ]
    )

    # 5. Maintenance History
    _create_pdf(
        CORPUS_DIR / "P-102_Maintenance_History.pdf",
        "EQUIPMENT WORK ORDER AND MAINTENANCE HISTORY LOG (P-102)",
        [
            ("Asset Summary",
             "Equipment ID: P-102\nDescription: Centrifugal Crude Charge Pump\nCommissioned: 2021\nOperating Hours: 4,200 hours since last major overhaul"),
            ("Historical Maintenance Records",
             "- WO-2025-089 (Nov 12, 2025): Full bearing replacement, mechanical seal overhaul, dynamic balancing. Baseline vibration verified at 2.0 mm/s.\n- WO-2026-014 (Jan 20, 2026): Routine mechanical seal inspection, flushed seal plan 11. Normal status.\n- WO-2026-042 (May 10, 2026): Lube oil top-up and filter change on bearing housing.")
        ]
    )

    # 6. Fire Emergency SOP
    _create_pdf(
        CORPUS_DIR / "SOP_Emergency_Fire_Evacuation.pdf",
        "STANDARD OPERATING PROCEDURE: HSE-SOP-012 FIRE EMERGENCY",
        [
            ("Document Details",
             "Procedure Code: HSE-SOP-012 | Department: HSE | Revision: 4.2"),
            ("Section 3.0 Emergency Actions",
             "What should an employee do during a fire emergency:\n1. Immediately raise the alarm by activating the nearest Manual Call Point (MCP) or calling plant control on extension 5555.\n2. Stop hot work and initiate emergency machinery shutdown only if safe to do so within 10 seconds.\n3. Evacuate the facility immediately using designated emergency exit routes. Never use elevators during a fire evacuation.\n4. Proceed directly to designated Emergency Assembly Point B (North Lawn).\n5. Report to your assigned Department HSE Warden for roll call.\n6. Do not re-enter the facility until the Incident Commander has officially given the all-clear signal.")
        ]
    )

    # 7. Process Flow Interconnection
    _create_pdf(
        CORPUS_DIR / "Unit_101_Interconnect_Description.pdf",
        "PROCESS FLOW SPECIFICATION: UNIT 101 CRUDE CHARGE TRAIN",
        [
            ("1.0 Train Overview",
             "Unit 101 handles primary crude feedstock desulfurization and charging."),
            ("2.0 Interconnection Topology",
             "Equipment connections in Unit 101:\n- Feed Tank T-101 buffers incoming crude storage.\n- Feed Tank T-101 feeds into Centrifugal Pump P-102.\n- Pump P-102 discharges pressurized crude to downstream Control Valve V-204.\n- Control Valve V-204 feeds into Desulfurization Reactor R-101.\nProcess flow connectivity chain: T-101 -> P-102 -> V-204 -> R-101.")
        ]
    )

    # 8. P&ID Drawing (PNG)
    _create_pid_image(CORPUS_DIR / "pid_unit_101.png")

    # 9. Time-series Telemetry CSV
    _create_telemetry_csv(CORPUS_DIR / "P-102_telemetry_jan_jul.csv")

    print("Synthetic demo corpus files created successfully in ./corpus.")


DOC_SPECS = [
    {
        "filename": "P-102_Inspection_Jan.pdf",
        "source_id": "doc_1120",
        "document_type": "inspection_report",
        "equipment_ids": ["P-102"],
        "department_scope": "maintenance",
    },
    {
        "filename": "P-102_Inspection_Apr.pdf",
        "source_id": "doc_1121",
        "document_type": "inspection_report",
        "equipment_ids": ["P-102"],
        "department_scope": "maintenance",
    },
    {
        "filename": "P-102_Inspection_Jul.pdf",
        "source_id": "doc_1122",
        "document_type": "inspection_report",
        "equipment_ids": ["P-102"],
        "department_scope": "maintenance",
    },
    {
        "filename": "P-102_Pump_Operating_Manual.pdf",
        "source_id": "doc_1130",
        "document_type": "manual",
        "equipment_ids": ["P-102"],
        "department_scope": "operations",
    },
    {
        "filename": "P-102_Maintenance_History.pdf",
        "source_id": "doc_1140",
        "document_type": "maintenance_history",
        "equipment_ids": ["P-102"],
        "department_scope": "maintenance",
    },
    {
        "filename": "SOP_Emergency_Fire_Evacuation.pdf",
        "source_id": "doc_sop01",
        "document_type": "sop",
        "equipment_ids": [],
        "department_scope": "HSE",
    },
    {
        "filename": "Unit_101_Interconnect_Description.pdf",
        "source_id": "doc_pfd01",
        "document_type": "other",
        "equipment_ids": ["T-101", "P-102", "V-204", "R-101"],
        "department_scope": "operations",
    },
    {
        "filename": "pid_unit_101.png",
        "source_id": "pid_101",
        "document_type": "pid_drawing",
        "equipment_ids": ["T-101", "P-102", "V-204", "R-101"],
        "department_scope": "operations",
    },
]


async def ingest_corpus():
    """Ingest the generated demo corpus into DB, vector store, object store."""
    print("\nStarting ingestion pipeline for KavachAI demo corpus...")
    await init_db()

    async with async_session() as db:
        # Ingest documents
        for spec in DOC_SPECS:
            filepath = CORPUS_DIR / spec["filename"]
            if not filepath.exists():
                print(f"  [SKIP] {spec['filename']} not found.")
                continue

            with open(filepath, "rb") as f:
                file_content = f.read()

            source_id = spec["source_id"]
            filename = spec["filename"]
            doc_type = spec["document_type"]
            equip_ids = spec["equipment_ids"]
            dept_scope = spec["department_scope"]

            # 1. Object store
            object_store.save_raw_file(source_id, file_content, filename)

            # 2. Extract & chunk
            page_count = get_page_count(file_content, filename)
            pages = extract_text(file_content, filename)

            chunk_count = 0
            if pages:
                chunks = chunk_pages(pages)
                tagged = tag_chunks(chunks, source_id, filename, doc_type, equip_ids, dept_scope)
                texts = [c["text"] for c in tagged]
                embeddings = await generate_embeddings(texts)
                chunk_ids = [f"{source_id}_chunk_{i}" for i in range(len(tagged))]
                metadatas = [c["metadata"] for c in tagged]
                vector_store.upsert_chunks(chunk_ids, texts, embeddings, metadatas)
                chunk_count = len(tagged)

            # 3. Check existing SQL document or insert
            existing = await db.execute(select(Document).where(Document.source_id == source_id))
            doc = existing.scalar_one_or_none()
            if not doc:
                doc = Document(
                    source_id=source_id,
                    filename=filename,
                    document_type=doc_type,
                    status="ready",
                    pages=page_count,
                    chunks=chunk_count,
                    equipment_ids=equip_ids,
                    department_scope=dept_scope,
                )
                db.add(doc)
            else:
                doc.status = "ready"
                doc.chunks = chunk_count
                doc.pages = page_count

            print(f"  [OK] Ingested document: {filename} ({doc_type}, {chunk_count} chunks, ID: {source_id})")

        # Commit document insertions before opening tabular sqlite connection
        await db.commit()

        # Ingest CSV Dataset
        csv_path = CORPUS_DIR / "P-102_telemetry_jan_jul.csv"
        if csv_path.exists():
            with open(csv_path, "rb") as f:
                csv_bytes = f.read()

            dataset_id = "ds_4471"
            object_store.save_raw_file(dataset_id, csv_bytes, "P-102_telemetry_jan_jul.csv")
            parsed = parse_tabular_file(csv_bytes, "P-102_telemetry_jan_jul.csv", dataset_id)

            existing_ds = await db.execute(select(Dataset).where(Dataset.id == dataset_id))

            ds = existing_ds.scalar_one_or_none()
            if not ds:
                ds = Dataset(
                    id=dataset_id,
                    filename="P-102_telemetry_jan_jul.csv",
                    columns=parsed["columns"],
                    row_count=parsed["row_count"],
                    status="ready",
                    table_name=parsed["table_name"],
                )
                db.add(ds)
            else:
                ds.status = "ready"
                ds.row_count = parsed["row_count"]

            print(f"  [OK] Ingested dataset: P-102_telemetry_jan_jul.csv ({parsed['row_count']} rows, ID: {dataset_id})")

        await db.commit()

        # Summary Verification (API_Reference.md §3)
        doc_res = await db.execute(
            select(func.count(Document.id)).where(
                Document.status == "ready", Document.document_type != "pid_drawing"
            )
        )
        doc_count = doc_res.scalar() or 0

        pid_res = await db.execute(
            select(func.count(Document.id)).where(
                Document.status == "ready", Document.document_type == "pid_drawing"
            )
        )
        pid_count = pid_res.scalar() or 0

        ds_res = await db.execute(select(func.count(Dataset.id)).where(Dataset.status == "ready"))
        ds_count = ds_res.scalar() or 0

        print("\n" + "=" * 60)
        print("Knowledge Base Ingestion Summary:")
        print(f"  Documents:    {doc_count} (Expected: 7)")
        print(f"  Datasets:     {ds_count} (Expected: 1)")
        print(f"  PID Drawings: {pid_count} (Expected: 1)")
        print("=" * 60)

        if doc_count == 7 and ds_count == 1 and pid_count == 1:
            print("Phase 1 Ingestion DoD: ALL PASSED")
            return True
        else:
            print("Phase 1 Ingestion DoD: COUNTS DO NOT MATCH")
            return False


if __name__ == "__main__":
    generate_demo_corpus()
    success = asyncio.run(ingest_corpus())
    if not success:
        sys.exit(1)
