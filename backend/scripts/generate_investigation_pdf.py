import sys
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        # Running Top Header
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#c45d3e"))
        self.drawString(36, 804, "KavachAI")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#655f56"))
        self.drawString(80, 804, "— Sovereign Industrial AI Workbench · Formal Investigation Report")
        
        self.setStrokeColor(colors.HexColor("#e2dacd"))
        self.setLineWidth(0.5)
        self.line(36, 796, 559, 796)

        # Running Footer
        self.line(36, 42, 559, 42)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#91887b"))
        self.drawString(36, 30, "CONFIDENTIAL & SOVEREIGN · Mangalore Refinery and Petrochemicals Limited (MRPL)")
        self.drawRightString(559, 30, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def generate_investigation_report_pdf(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=54,
        bottomMargin=54,
    )
    
    styles = getSampleStyleSheet()
    
    c_primary = colors.HexColor("#2d2a26")   # Deep charcoal
    c_accent = colors.HexColor("#c45d3e")    # Terracotta rust
    c_text2 = colors.HexColor("#655f56")     # Warm neutral secondary
    c_text3 = colors.HexColor("#91887b")     # Muted text
    c_border = colors.HexColor("#e2dacd")    # Warm stone border
    c_surface = colors.HexColor("#faf8f5")   # Warm canvas
    c_warn = colors.HexColor("#c45d3e")      # Attention required
    c_green = colors.HexColor("#2d7a4d")     # Verified green
    
    title_style = ParagraphStyle(
        'InvTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_primary,
        spaceAfter=4,
    )
    
    subtitle_style = ParagraphStyle(
        'InvSubtitle', parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=c_text2,
        spaceAfter=12,
    )

    section_heading = ParagraphStyle(
        'InvSectionHeading', parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_accent,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        'InvBody', parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=c_primary,
    )

    body_bold = ParagraphStyle(
        'InvBodyBold', parent=body_style,
        fontName='Helvetica-Bold',
    )

    meta_label = ParagraphStyle(
        'InvMetaLabel', parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=c_text3,
    )

    meta_val = ParagraphStyle(
        'InvMetaVal', parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_primary,
    )

    meta_style = ParagraphStyle(
        'InvMetaText', parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=c_text2,
    )

    badge_style = ParagraphStyle(
        'InvBadge', parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1, # Center
    )

    table_header_style = ParagraphStyle(
        'InvTH', parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    table_cell_style = ParagraphStyle(
        'InvTC', parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=c_primary,
    )

    table_cell_mono = ParagraphStyle(
        'InvTCMono', parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#8a381e"),
    )

    story = []
    
    # ── Header Block ──
    story.append(Paragraph("KavachAI Investigation Report", title_style))
    story.append(Paragraph("Sovereign Industrial Agentic AI Workbench · Local Inference Verification", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_accent, spaceBefore=0, spaceAfter=10))

    # ── Metadata Box ──
    meta_data = [
        [
            Paragraph("INVESTIGATION ID", meta_label),
            Paragraph("TARGET EQUIPMENT", meta_label),
            Paragraph("INVESTIGATION DATE", meta_label),
            Paragraph("OVERALL STATUS", meta_label),
        ],
        [
            Paragraph("<b>inv_p102_det_089</b>", meta_val),
            Paragraph("<b>Pump P-102 (Booster)</b>", meta_val),
            Paragraph("September 8, 2026", meta_val),
            Paragraph("ATTENTION REQUIRED", badge_style),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[130, 130, 130, 133])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8f6f1")),
        ('BOX', (0,0), (-1,-1), 0.75, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND', (3,1), (3,1), c_accent), # Highlight status badge
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # ── Query Box ──
    query_data = [
        [Paragraph("<b>Investigation Query:</b>", meta_label)],
        [Paragraph("<i>“Investigate Pump P-102 and determine whether its condition has deteriorated.”</i>", ParagraphStyle('Q', parent=body_style, fontSize=9.5, leading=14, textColor=colors.HexColor("#1e293b")))]
    ]
    query_table = Table(query_data, colWidths=[523])
    query_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fdfcfa")),
        ('BOX', (0,0), (-1,-1), 0.75, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(query_table)
    story.append(Spacer(1, 10))

    # ── Investigation Confidence & Verification Summary ──
    conf_data = [
        [
            Paragraph("<b>Overall Status:</b> <font color='#c45d3e'><b>ATTENTION REQUIRED</b></font>", body_style),
            Paragraph("<b>Confidence Score:</b> <font color='#2d7a4d'><b>95%</b></font>", body_style),
            Paragraph("<b>Verification Status:</b> <font color='#2d7a4d'><b>VERIFIED (100% Grounded)</b></font>", body_style),
        ]
    ]
    conf_table = Table(conf_data, colWidths=[180, 140, 203])
    conf_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f5f0e8")),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(conf_table)
    story.append(Spacer(1, 10))

    # ── Key Findings Section ──
    story.append(Paragraph("Key Findings & Evidence Traceability", section_heading))
    story.append(HRFlowable(width="100%", thickness=0.5, color=c_border, spaceBefore=0, spaceAfter=6))
    
    findings_data = [
        [
            Paragraph("#", table_header_style),
            Paragraph("Finding Description", table_header_style),
            Paragraph("Extracted Metric / Value", table_header_style),
            Paragraph("Source Evidence", table_header_style),
            Paragraph("Status", table_header_style),
        ],
        [
            Paragraph("1", table_cell_style),
            Paragraph("<b>Increasing Vibration Velocity:</b> Baseline vibration rose steadily over observed 6-month period.", table_cell_style),
            Paragraph("Jan: 2.1 mm/s<br/>Apr: 2.8 mm/s<br/><b>Jul: 3.7 mm/s (+76.2%)</b>", table_cell_mono),
            Paragraph("P-102_Inspection_Jul.pdf, p. 2<br/>P-102_telemetry_jan_jul.csv", table_cell_style),
            Paragraph("<font color='#2d7a4d'><b>✓ Supported</b></font>", table_cell_style),
        ],
        [
            Paragraph("2", table_cell_style),
            Paragraph("<b>Exceeds Continuous Threshold:</b> July reading exceeds manufacturer continuous operation advisory limit.", table_cell_style),
            Paragraph("Current: <b>3.7 mm/s</b><br/>Spec Limit: <b>3.0 mm/s</b>", table_cell_mono),
            Paragraph("P-102_Pump_Operating_Manual.pdf, p. 4, §3.2", table_cell_style),
            Paragraph("<font color='#2d7a4d'><b>✓ Supported</b></font>", table_cell_style),
        ],
        [
            Paragraph("3", table_cell_style),
            Paragraph("<b>Drive-End Bearing Temperature Rise:</b> Temperature trend confirms friction increase.", table_cell_style),
            Paragraph("Jan: 68°C<br/>Apr: 71°C<br/><b>Jul: 77°C (+13.2%)</b>", table_cell_mono),
            Paragraph("P-102_Inspection_Jul.pdf, p. 3<br/>ds_4471 (Telemetry)", table_cell_style),
            Paragraph("<font color='#2d7a4d'><b>✓ Supported</b></font>", table_cell_style),
        ],
        [
            Paragraph("4", table_cell_style),
            Paragraph("<b>Topological Downstream Risk:</b> Pump P-102 feeds directly into Hydrocracker Reactor via Control Valve.", table_cell_style),
            Paragraph("Path: <b>T-101 &rarr; P-102 &rarr; V-204 &rarr; R-101</b>", table_cell_mono),
            Paragraph("pid_unit_101.png<br/>Unit_101_Interconnect_Description.pdf", table_cell_style),
            Paragraph("<font color='#2d7a4d'><b>✓ Supported</b></font>", table_cell_style),
        ],
    ]
    
    findings_table = Table(findings_data, colWidths=[20, 180, 115, 140, 68])
    findings_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_accent),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#fdfcfa")),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#f8f6f0")),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#fdfcfa")),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor("#f8f6f0")),
    ]))
    story.append(findings_table)
    story.append(Spacer(1, 10))

    # ── Telemetry Sensor Progression Table ──
    story.append(Paragraph("Deterministic Telemetry Progression (Data Agent Log)", section_heading))
    story.append(HRFlowable(width="100%", thickness=0.5, color=c_border, spaceBefore=0, spaceAfter=6))
    
    trend_data = [
        [
            Paragraph("Date / Milestone", table_header_style),
            Paragraph("Vibration (RMS mm/s)", table_header_style),
            Paragraph("Bearing Temp (°C)", table_header_style),
            Paragraph("Advisory Threshold", table_header_style),
            Paragraph("Condition Status", table_header_style),
        ],
        [
            Paragraph("January 10, 2026 (Baseline)", table_cell_style),
            Paragraph("2.1 mm/s", table_cell_mono),
            Paragraph("68.0 °C", table_cell_mono),
            Paragraph("3.0 mm/s", table_cell_style),
            Paragraph("<font color='#2d7a4d'><b>NORMAL</b></font>", table_cell_style),
        ],
        [
            Paragraph("April 11, 2026 (Inspection 2)", table_cell_style),
            Paragraph("2.8 mm/s", table_cell_mono),
            Paragraph("71.4 °C", table_cell_mono),
            Paragraph("3.0 mm/s", table_cell_style),
            Paragraph("<font color='#c45d3e'><b>ELEVATED</b></font>", table_cell_style),
        ],
        [
            Paragraph("July 09, 2026 (Inspection 3)", table_cell_style),
            Paragraph("<b>3.7 mm/s (+76%)</b>", table_cell_mono),
            Paragraph("<b>77.2 °C (+13%)</b>", table_cell_mono),
            Paragraph("3.0 mm/s", table_cell_style),
            Paragraph("<font color='#ba3838'><b>EXCEEDED LIMIT</b></font>", table_cell_style),
        ],
    ]
    trend_table = Table(trend_data, colWidths=[140, 100, 95, 95, 93])
    trend_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2d2a26")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#fcf0eb")), # Highlight July
    ]))
    story.append(trend_table)
    story.append(Spacer(1, 10))

    # ── Conclusion Box ──
    story.append(Paragraph("Conclusion & Engineering Action Plan", section_heading))
    story.append(HRFlowable(width="100%", thickness=0.5, color=c_border, spaceBefore=0, spaceAfter=6))
    
    concl_data = [
        [
            Paragraph(
                "<b>Synthesized Finding:</b><br/>"
                "The available multimodal evidence indicates a clear condition deterioration on Booster Pump P-102 over the observed 6-month period. "
                "Vibration velocity has increased from a 2.1 mm/s baseline to 3.7 mm/s (+76.2%), crossing the 3.0 mm/s continuous operation threshold specified in the Operating Manual. "
                "Concurrently, drive-end bearing temperature has climbed from 68°C to 77°C.<br/><br/>"
                "<b>Recommendation & Next Steps:</b><br/>"
                "1. Schedule laser shaft alignment and coupling inspection for Pump P-102 during the upcoming maintenance window.<br/>"
                "2. Conduct high-frequency spectral vibration analysis to isolate bearing outer-race frequency vs. unbalance.<br/>"
                "3. Perform ultrasonic lubrication check on drive-end bearings.<br/>"
                "4. <i>Note: The evidence indicates condition degradation requiring engineering attention, but does NOT establish imminent catastrophic failure.</i>",
                body_style
            )
        ]
    ]
    concl_table = Table(concl_data, colWidths=[523])
    concl_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fbf9f5")),
        ('BOX', (0,0), (-1,-1), 1, c_accent),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(concl_table)
    story.append(Spacer(1, 12))

    # ── Verification & Forensic Sign-Off ──
    sign_data = [
        [
            Paragraph("<b>Automated Verification:</b> PASSED (Confidence: 95%)<br/>"
                      "<b>Agents Involved:</b> Planner, Document, Data, Vision, Verification<br/>"
                      "<b>Local Inference Host:</b> 127.0.0.1:11434 (Qwen 2.5 3B)", meta_style),
            Paragraph("<b>Audit Checksum:</b> <code>sha256:7f4c029...e957</code><br/>"
                      "<b>Data Sovereignty:</b> Air-Gapped / Zero External Egress<br/>"
                      "<b>Sign-off:</b> KavachAI Sovereign Verification Engine", meta_style),
        ]
    ]
    sign_table = Table(sign_data, colWidths=[260, 263])
    sign_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8f6f1")),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(sign_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Investigation report generated successfully at: {output_path}")

if __name__ == "__main__":
    out_file = Path(sys.argv[1] if len(sys.argv) > 1 else "KavachAI_Investigation_Report.pdf").resolve()
    generate_investigation_report_pdf(out_file)
