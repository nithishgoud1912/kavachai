"""
Generate an advanced, multi-page, highly complex industrial technical dossier & P&ID schematic PDF.
Features an 8-node interconnected process train with bypasses, control loops, sensor tables,
and cascading risk analysis for testing deep visual-language reasoning in KavachAI with Qwen2.5-VL.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def create_complex_8node_pid_image(output_path: Path):
    """Draw a rich, 8-node process schematic with instrumentation, bypass loops, and transmitters."""
    w, h = 1350, 480
    img = Image.new("RGB", (w, h), color="#F8FAFC")
    draw = ImageDraw.Draw(img)

    # 8 Nodes: (x1, y1, x2, y2, Tag, Description, Color)
    nodes = [
        (25, 170, 145, 305, "TK-101A", "Crude Storage\n50,000 bbl\n1.2 bar · 40°C", "#0284C7"),
        (175, 170, 290, 305, "DS-101", "Desalter Unit\nElectrostatic\n3.8 bar · 99% Salt", "#475569"),
        (320, 180, 425, 295, "STR-101", "Basket Strainer\nDual Mesh 40\nDP: 0.12 bar", "#64748B"),
        (455, 170, 580, 305, "P-102", "Charge Pump\nAPI 610 BB2\n450 m3/h · 14.2 bar", "#DC2626"),
        (615, 165, 745, 310, "E-103A-D", "Pre-Heat Bank\nShell & Tube 4-Pass\n165°C Effluent", "#2563EB"),
        (780, 180, 885, 295, "FCV-204", "Control Valve\nPneumatic Globe\nModulating 68%", "#0D9488"),
        (920, 160, 1055, 315, "F-101", "Fired Heater\nCoil Duty 28 MW\n360°C Charge", "#D97706"),
        (1090, 150, 1315, 325, "R-101", "Hydrotreater\nFixed Bed Co-Mo\n45 bar · 375°C", "#4F46E5"),
    ]

    main_flow = "#0F766E"

    # Main linear flow connections
    edges = [
        ((145, 238), (175, 238)),  # TK-101A -> DS-101
        ((290, 238), (320, 238)),  # DS-101 -> STR-101
        ((425, 238), (455, 238)),  # STR-101 -> P-102
        ((580, 238), (615, 238)),  # P-102 -> E-103A-D
        ((745, 238), (780, 238)),  # E-103A-D -> FCV-204
        ((885, 238), (920, 238)),  # FCV-204 -> F-101
        ((1055, 238), (1090, 238)), # F-101 -> R-101
    ]

    for (x1, y1), (x2, y2) in edges:
        draw.line([(x1, y1), (x2, y2)], fill=main_flow, width=5)
        draw.polygon([(x2, y2), (x2 - 12, y2 - 7), (x2 - 12, y2 + 7)], fill=main_flow)

    # Minimum Flow Recirculation Bypass Loop (FIC-102) from P-102 discharge back to TK-101A
    bypass_recirc = "#C2410C"
    draw.line([(590, 238), (590, 95), (85, 95), (85, 170)], fill=bypass_recirc, width=3)
    draw.polygon([(85, 170), (79, 158), (91, 158)], fill=bypass_recirc)
    draw.text((180, 75), "MINIMUM FLOW RECYCLE BYPASS LINE (FIC-102 RECIRCULATION TO TANK)", fill=bypass_recirc)

    # Exchanger Thermal Trim Bypass (TCV-103) around E-103 to FCV-204
    trim_color = "#2563EB"
    draw.line([(598, 238), (598, 385), (762, 385), (762, 238)], fill=trim_color, width=2)
    draw.polygon([(762, 238), (757, 250), (767, 250)], fill=trim_color)
    draw.text((615, 395), "THERMAL TRIM BYPASS (TCV-103)", fill=trim_color)

    # Draw instrument transmitters (Circles)
    transmitters = [
        (372, 140, "DPI-101", "#64748B"),
        (517, 130, "VIB-102", "#DC2626"),
        (517, 345, "TI-102", "#0284C7"),
        (832, 140, "ZT-204", "#0D9488"),
        (987, 120, "TIC-101", "#D97706"),
        (1202, 110, "PIC-101", "#4F46E5"),
    ]

    for cx, cy, tag, col in transmitters:
        draw.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill="#FFFFFF", outline=col, width=2)
        draw.text((cx - 18, cy - 6), tag, fill=col)

    # Draw equipment cards
    for x1, y1, x2, y2, tag, desc, col in nodes:
        draw.rectangle([x1, y1, x2, y2], fill="#FFFFFF", outline=col, width=2)
        draw.rectangle([x1, y1, x2, y1 + 30], fill=col)
        draw.text((x1 + 8, y1 + 7), tag, fill="#FFFFFF")
        draw.text((x1 + 8, y1 + 38), desc, fill="#1E293B")

    # Critical Alert Callout Box on P-102
    draw.rectangle([450, 60, 600, 88], fill="#FEF2F2", outline="#DC2626", width=2)
    draw.text((458, 66), "! FAULT: VIB 3.72 mm/s", fill="#B91C1C")

    # Header banner
    draw.text((25, 20), "UNIT 101/102 — CRUDE CHARGE & HYDROTREATING PROCESS & INSTRUMENTATION SCHEMATIC", fill="#0F172A")
    draw.text((25, 42), "Drawing No: MRPL-U101-PID-008 | Rev: 6.2 | Scope: TK-101A -> DS-101 -> STR-101 -> P-102 -> E-103 -> FCV-204 -> F-101 -> R-101", fill="#64748B")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")


def build_complex_dossier_pdf(output_pdf: Path):
    """Generate a multi-page comprehensive industrial audit & forensic report."""
    temp_img_path = output_pdf.parent / "temp_complex_8node_pid.png"
    create_complex_8node_pid_image(temp_img_path)

    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    doc_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=15,
        leading=19,
        spaceAfter=3,
        textColor='#0F172A',
        fontName="Helvetica-Bold"
    )
    doc_sub = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=12,
        textColor='#64748B',
        spaceAfter=10,
    )
    sec_head = ParagraphStyle(
        'SecHead',
        parent=styles['Heading2'],
        fontSize=10.5,
        leading=14,
        spaceBefore=8,
        spaceAfter=3,
        textColor='#0F766E',
        fontName="Helvetica-Bold"
    )
    body = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=12,
        textColor='#334155',
    )
    critical_alert = ParagraphStyle(
        'CriticalAlert',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=12,
        textColor='#991B1B',
        fontName="Helvetica-Bold"
    )

    story = []

    # Page 1: Executive Summary & Overview
    story.append(Paragraph("MANGALORE REFINERY AND PETROCHEMICALS LIMITED (MRPL) — RELIABILITY ENGINEERING DIVISION", doc_sub))
    story.append(Paragraph("TECHNICAL AUDIT & FORENSIC INVESTIGATION DOSSIER: UNIT 101/102 CRUDE CHARGE TRAIN", doc_title))
    story.append(Paragraph("Audit Dossier Ref: MRPL-AUDIT-2026-P102-SYS | Classification: Restricted Confidential | Lead: Reliability Directorate", doc_sub))

    # Summary Metadata
    summary_meta = [
        ["Primary Asset Monitored:", "P-102 (Centrifugal Crude Charge Pump)", "Process Unit:", "Unit 101/102 Distillation & Hydrotreater"],
        ["Immediate Upstream Node:", "STR-101 (Dual Basket Strainer) / DS-101", "Immediate Downstream Node:", "E-103A-D (Pre-Heat Exchanger Bank)"],
        ["Terminal Source Tank:", "TK-101A (Crude Storage, 50k bbl)", "Terminal Reaction Node:", "R-101 (Hydrotreating Desulfurizer)"],
        ["Vibration Advisory Limit:", "3.0 mm/s RMS (ISO 10816-3 Class III)", "Current Measured Status:", "3.72 mm/s RMS (ATTENTION REQUIRED)"],
    ]
    meta_table = Table(summary_meta, colWidths=[130, 140, 130, 140])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1E293B')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # Section 1.0: Complete 8-Node Process Architecture
    story.append(Paragraph("1.0 Process Flow & P&ID Interconnect Schematic (Complete 8-Node Topology)", sec_head))
    story.append(Paragraph(
        "The crude charge and hydrotreating sequence consists of an integrated 8-node train: "
        "<b>TK-101A</b> (Feed Storage) &rarr; <b>DS-101</b> (Electrostatic Desalter) &rarr; <b>STR-101</b> (Basket Strainer) &rarr; "
        "<b>P-102</b> (Charge Pump) &rarr; <b>E-103A-D</b> (Pre-Heat Bank) &rarr; <b>FCV-204</b> (Flow Control Valve) &rarr; "
        "<b>F-101</b> (Fired Furnace) &rarr; <b>R-101</b> (Hydrotreater Reactor). "
        "Additionally, a minimum flow recirculation bypass loop (<b>FIC-102</b>) protects P-102 by routing excess discharge back to TK-101A, "
        "while thermal trim loop <b>TCV-103</b> bypasses E-103 during high-temperature swings.",
        body
    ))
    story.append(Spacer(1, 6))

    # Insert Large 8-Node Image
    story.append(RLImage(str(temp_img_path), width=540, height=192))
    story.append(Spacer(1, 8))

    # Section 2.0: Multi-Point Telemetry Table
    story.append(Paragraph("2.0 Multi-Point Condition Monitoring & Telemetry Profile", sec_head))
    telemetry_data = [
        ["Tag", "Component Description", "Operating Parameter", "Design Baseline", "Quarterly Actual", "Alarm Status"],
        ["TK-101A", "Feed Storage Tank", "Liquid Head / Pressure", "1.2 - 1.5 bar", "1.22 bar", "NORMAL"],
        ["DS-101", "Electrostatic Desalter", "Salt Concentration", "< 5.0 ppm", "2.1 ppm", "NORMAL"],
        ["STR-101", "Suction Basket Strainer", "Differential Pressure", "< 0.25 bar", "0.14 bar", "NORMAL"],
        ["P-102", "Crude Charge Pump", "Vibration Velocity (RMS)", "< 3.0 mm/s", "3.72 mm/s", "ATTENTION (BREACH)"],
        ["P-102", "Drive-End Bearing DE", "Bearing Temperature", "< 70.0 °C", "77.4 °C", "ELEVATED"],
        ["E-103", "Pre-Heat Exchanger Bank", "Crude Outlet Temp", "140 - 170 °C", "165.2 °C", "NORMAL"],
        ["FCV-204", "Flow Control Valve", "Stem Travel / Mod.", "50 - 75 %", "68.4 %", "NORMAL"],
        ["F-101", "Fired Charge Heater", "Coil Outlet Temp COT", "355 - 365 °C", "361.0 °C", "NORMAL"],
        ["R-101", "Hydrotreater Reactor", "Catalyst Bed Temp", "370 - 380 °C", "375.1 °C", "NORMAL"],
    ]
    tele_table = Table(telemetry_data, colWidths=[55, 125, 120, 75, 75, 90])
    tele_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F766E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TEXTCOLOR', (5, 4), (5, 5), colors.HexColor('#B91C1C')),
        ('FONTNAME', (5, 4), (5, 5), 'Helvetica-Bold'),
    ]))
    story.append(tele_table)
    story.append(Spacer(1, 6))

    # Section 3.0: Forensic Engineering Analysis
    story.append(Paragraph("3.0 Forensic Analysis & Cascading Trip Propagation", sec_head))
    story.append(Paragraph(
        "<b>Failure Mode:</b> Drive-end bearing degradation on Pump P-102 has introduced 1X rotational frequency harmonics. "
        "Vibration has climbed from 2.1 mm/s (Jan) to 2.8 mm/s (Apr) to 3.72 mm/s (Jul), representing a +76.2% acceleration.<br/>"
        "<b>Cascading Risk:</b> If P-102 experiences sudden unannounced bearing seizure, crude flow to furnace F-101 will immediately drop, "
        "triggering low-flow burner trips. Stagnant crude within F-101 tubes will experience thermal cracking and internal tube coking within 120 seconds. "
        "Reactor R-101 will face rapid hydrogen quenching and thermal shock.",
        critical_alert
    ))
    story.append(Spacer(1, 6))

    # Section 4.0: Corrective Action Directives
    story.append(Paragraph("4.0 Mandated Corrective Protocols", sec_head))
    action_items = [
        ["Phase", "Directive", "Target Node", "Action Timeframe"],
        ["Priority 1", "Switch to Standby Pump P-102B; isolate P-102A suction & discharge valves", "P-102A/B", "Within 12 Hours"],
        ["Priority 2", "Inspect suction strainer STR-101 basket for metal shavings or foreign particulate", "STR-101", "Next Shift"],
        ["Priority 3", "Calibrate minimum flow recirculation valve FIC-102 to ensure 120 m3/h anti-cavitation loop", "FIC-102", "Within 48 Hours"],
        ["Priority 4", "Execute dynamic laser alignment on P-102 drive coupling and replace DE bearings", "P-102", "Scheduled Outage"],
    ]
    action_table = Table(action_items, colWidths=[60, 270, 90, 120])
    action_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(action_table)

    doc.build(story)

    if temp_img_path.exists():
        temp_img_path.unlink()

    print(f"Successfully built complex technical dossier PDF at: {output_pdf}")


if __name__ == "__main__":
    out_dir = Path(r"c:\Users\HP\Desktop\SIH\KavachAI - Copy")
    pdf_path = out_dir / "Complex_Refinery_P&ID_and_Forensic_Investigation_Report.pdf"
    build_complex_dossier_pdf(pdf_path)
