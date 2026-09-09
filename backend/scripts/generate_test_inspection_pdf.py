"""
Generate a realistic industrial inspection report PDF with an embedded P&ID schematic.
Designed to test Qwen2.5-VL visual-language reasoning in KavachAI.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def create_pid_schematic_image(output_path: Path):
    """Draw a 7-node industrial P&ID diagram with tags, equipment symbols, arrows, and bypass."""
    img = Image.new("RGB", (1100, 380), color="#F8FAFC")
    draw = ImageDraw.Draw(img)

    # 7 Equipment blocks: (x1, y1, x2, y2, Tag, Description, CategoryColor)
    blocks = [
        (20, 115, 145, 235, "T-101", "Feed Tank\n50k bbl\n1.2 bar", "#0369A1"),
        (175, 125, 285, 225, "STR-101", "Suction Strainer\nMesh 40\nDP: 0.1 bar", "#475569"),
        (315, 115, 435, 235, "P-102", "Charge Pump\nBB2 Centrif.\n450 m3/h", "#C2410C"),
        (470, 115, 595, 235, "E-103", "Pre-Heat Exch.\nShell & Tube\n140 deg C", "#2563EB"),
        (630, 125, 740, 225, "V-204", "Control Valve\nGlobe 6-inch\nFCV Modulating", "#0F766E"),
        (775, 110, 895, 240, "F-101", "Fired Heater\nCoil Duty 24MW\n360 deg C", "#B45309"),
        (930, 100, 1075, 250, "R-101", "Hydrotreater\nFixed Bed Cat.\n45 bar", "#4338CA"),
    ]

    line_color = "#0F766E"
    
    # Linear connections between nodes
    connections = [
        ((145, 175), (175, 175)),  # T-101 -> STR-101
        ((285, 175), (315, 175)),  # STR-101 -> P-102
        ((435, 175), (470, 175)),  # P-102 -> E-103
        ((595, 175), (630, 175)),  # E-103 -> V-204
        ((740, 175), (775, 175)),  # V-204 -> F-101
        ((895, 175), (930, 175)),  # F-101 -> R-101
    ]

    for (x_start, y_start), (x_end, y_end) in connections:
        draw.line([(x_start, y_start), (x_end, y_end)], fill=line_color, width=4)
        draw.polygon([(x_end, y_end), (x_end - 10, y_end - 6), (x_end - 10, y_end + 6)], fill=line_color)

    # Minimum Flow Recirculation Bypass Loop: P-102 discharge back to T-101 (top loop)
    recirc_color = "#D97706"
    draw.line([(445, 175), (445, 70), (82, 70), (82, 115)], fill=recirc_color, width=2)
    draw.polygon([(82, 115), (77, 105), (87, 105)], fill=recirc_color)
    draw.text((170, 52), "MINIMUM FLOW RECYCLE BYPASS (FIC-102)", fill=recirc_color)

    # Draw equipment cards
    for x1, y1, x2, y2, tag, desc, header_color in blocks:
        draw.rectangle([x1, y1, x2, y2], fill="#FFFFFF", outline=header_color, width=2)
        draw.rectangle([x1, y1, x2, y1 + 28], fill=header_color)
        draw.text((x1 + 8, y1 + 6), tag, fill="#FFFFFF")
        draw.text((x1 + 8, y1 + 34), desc, fill="#1E293B")

    # Warning alert badge over P-102
    draw.rectangle([310, 85, 440, 108], fill="#FEF2F2", outline="#DC2626", width=2)
    draw.text((318, 90), "! VIB BREACH 3.7 mm/s", fill="#B91C1C")

    # Title header
    draw.text((20, 18), "UNIT 101 — CRUDE CHARGE & PRE-HEAT PROCESS & INSTRUMENTATION DIAGRAM", fill="#0F172A")
    draw.text((20, 36), "Drawing No: MRPL-U101-PID-007 | Rev: 5.0 | Complete 7-Node Sequence: T-101 -> STR-101 -> P-102 -> E-103 -> V-204 -> F-101 -> R-101", fill="#64748B")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")


def build_inspection_report_pdf(output_pdf_path: Path):
    """Build a professional branded inspection report PDF with embedded P&ID."""
    temp_img_path = output_pdf_path.parent / "temp_pid_diagram.png"
    create_pid_schematic_image(temp_img_path)

    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=17,
        leading=22,
        spaceAfter=4,
        textColor='#0F172A',
        fontName="Helvetica-Bold"
    )
    sub_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor='#64748B',
        spaceAfter=14,
    )
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontSize=11,
        leading=15,
        spaceBefore=10,
        spaceAfter=4,
        textColor='#0F766E',
        fontName="Helvetica-Bold"
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor='#334155',
    )
    alert_style = ParagraphStyle(
        'Alert',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor='#991B1B',
        fontName="Helvetica-Bold"
    )

    story = []

    # 1. Header & Metadata
    story.append(Paragraph("MANGALORE REFINERY AND PETROCHEMICALS LIMITED (MRPL)", sub_style))
    story.append(Paragraph("CRUDE DISTILLATION UNIT 101 — EQUIPMENT VISUAL & TECHNICAL INSPECTION REPORT", title_style))
    story.append(Paragraph("Inspection Reference: INSP-2026-P102-Q3 | Date: September 2026 | Asset: Centrifugal Charge Pump P-102", sub_style))
    story.append(Spacer(1, 4))

    # Metadata Table
    meta_data = [
        ["Asset ID:", "P-102 (Charge Pump)", "Process Unit:", "Unit 101 — Crude Distillation"],
        ["Location:", "Pump Bay 3, Bay B", "Lead Reliability Eng:", "Vikram Sharma (Reliability Dept)"],
        ["Design Threshold:", "3.0 mm/s RMS continuous", "Current Vibration:", "3.72 mm/s RMS (BREACH)"],
        ["Upstream Equipment:", "T-101 Feed Tank (Crude)", "Downstream Node:", "V-204 Control Valve -> R-101"],
    ]
    meta_table = Table(meta_data, colWidths=[120, 150, 120, 150])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1E293B')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 2. Section: Process & Instrumentation Diagram (P&ID) Schematic
    story.append(Paragraph("1.0 Process Flow & P&ID Interconnect Schematic", h2_style))
    story.append(Paragraph(
        "The following diagram illustrates the crude charge sequence: <b>T-101 (Feed Tank)</b> supplies raw crude to <b>P-102 (Charge Pump)</b>, "
        "which discharges downstream through <b>V-204 (Flow Control Valve)</b> directly into <b>R-101 (Hydrotreater Reactor)</b>.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Embedded Image
    story.append(RLImage(str(temp_img_path), width=530, height=212))
    story.append(Spacer(1, 8))

    # 3. Section: Visual Inspection Observations & Deterioration Findings
    story.append(Paragraph("2.0 Visual Inspection & Forensic Analysis", h2_style))
    story.append(Paragraph(
        "<b>Visual Callout:</b> Centrifugal Pump P-102 exhibits notable mechanical oscillation on the drive-end bearing bracket. "
        "Discharge flange connection at LINE-102-DIS shows minor seal seepage. Upstream suction from T-101 is stable at 1.2 bar. "
        "Downstream control valve V-204 is modulating at 68% position with nominal differential pressure.",
        body_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "<b>Deterioration Summary:</b> Measured vibration velocity has escalated across three consecutive inspections: "
        "Jan 2026: <b>2.1 mm/s</b> &rarr; Apr 2026: <b>2.8 mm/s</b> &rarr; Jul 2026: <b>3.7 mm/s</b> (+76% rise). "
        "Bearing temperature has elevated from 68&deg;C to 77&deg;C. Condition exceeds advisory limit (3.0 mm/s).",
        alert_style
    ))
    story.append(Spacer(1, 6))

    # 4. Corrective Recommendations
    story.append(Paragraph("3.0 Corrective Action & Verification Checklist", h2_style))
    action_data = [
        ["#", "Action Item", "Responsible", "Target Date"],
        ["1", "Perform laser coupling realignment on P-102 drive shaft", "Mechanical Maint.", "Immediate (48 hrs)"],
        ["2", "Inspect downstream flow valve V-204 for flow-induced pulsation", "Instrumentation", "Within 3 days"],
        ["3", "Verify isolation block valves on suction line from T-101 Feed Tank", "Operations", "Next shift"],
    ]
    action_table = Table(action_data, colWidths=[20, 310, 110, 100])
    action_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F766E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(action_table)

    doc.build(story)

    # Clean up temp image
    if temp_img_path.exists():
        temp_img_path.unlink()

    print(f"Successfully created inspection report PDF at: {output_pdf_path}")


if __name__ == "__main__":
    out_dir = Path(r"c:\Users\HP\Desktop\SIH\KavachAI - Copy")
    pdf_file = out_dir / "Unit_101_P-102_Visual_Inspection_Report.pdf"
    build_inspection_report_pdf(pdf_file)
