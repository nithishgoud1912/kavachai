"""
KavachAI — Industrial Inspection Report PDF Generator
Generates a publication-grade, multi-page Mechanical Condition & Integrity Inspection Report
adhering strictly to Design.md (Warm Minimal palette, no blue, sovereign industrial layout).
"""

import sys
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and draw total page count
    along with running header and running footer.
    """
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
        self.drawString(36, 806, "MANGALORE REFINERY & PETROCHEMICALS LIMITED (MRPL)")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#655f56"))
        self.drawString(290, 806, "| Rotary Equipment Condition Inspection Report")
        
        self.setStrokeColor(colors.HexColor("#e2dacd"))
        self.setLineWidth(0.5)
        self.line(36, 798, 559, 798)

        # Running Footer
        self.line(36, 38, 559, 38)
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#c45d3e"))
        self.drawString(36, 26, "CONFIDENTIAL & SOVEREIGN")
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#91887b"))
        self.drawString(160, 26, "| Plant Asset Inspection Log | KavachAI Verified Record")
        self.drawRightString(559, 26, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def generate_inspection_report_pdf(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=50,
        bottomMargin=48,
    )

    styles = getSampleStyleSheet()

    # ── Warm Minimal Palette (Strictly No Blue) ──
    c_primary     = colors.HexColor("#2d2a26")   # Deep charcoal body text
    c_accent      = colors.HexColor("#c45d3e")   # Terracotta rust (Primary brand)
    c_accent_dark = colors.HexColor("#8a381e")   # Deep rust
    c_gold        = colors.HexColor("#c9a23e")   # Warm gold / accent dim
    c_text2       = colors.HexColor("#655f56")   # Secondary text
    c_text3       = colors.HexColor("#91887b")   # Muted meta text
    c_border      = colors.HexColor("#e2dacd")   # Warm stone border
    c_surface     = colors.HexColor("#faf8f5")   # Crisp warm canvas
    c_surface_2   = colors.HexColor("#f4efe6")   # Tinted surface
    c_green       = colors.HexColor("#2d7a4d")   # Supported / Normal
    c_amber       = colors.HexColor("#b8721e")   # Attention / Elevated
    c_red         = colors.HexColor("#ba3838")   # Limit Exceeded / Critical

    # ── Typography Styles ──
    title_style = ParagraphStyle(
        'InsTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=c_primary,
        spaceAfter=2,
    )

    subtitle_style = ParagraphStyle(
        'InsSubtitle', parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=c_text2,
        spaceAfter=10,
    )

    section_heading = ParagraphStyle(
        'InsSectionHeading', parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=c_accent,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        'InsBody', parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_primary,
    )

    body_bold = ParagraphStyle(
        'InsBodyBold', parent=body_style,
        fontName='Helvetica-Bold',
    )

    meta_label = ParagraphStyle(
        'InsMetaLabel', parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=c_text3,
    )

    meta_val = ParagraphStyle(
        'InsMetaVal', parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=c_primary,
    )

    badge_style = ParagraphStyle(
        'InsBadge', parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1, # Center
    )

    table_header_style = ParagraphStyle(
        'InsTH', parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    table_cell_style = ParagraphStyle(
        'InsTC', parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=c_primary,
    )

    table_cell_mono = ParagraphStyle(
        'InsTCMono', parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=c_accent_dark,
    )

    story = []

    # ═════════════════════════════════════════════════════════════════════════
    # 1. HEADER & REPORT METADATA
    # ═════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Centrifugal Pump P-102 Condition Inspection Report", title_style))
    story.append(Paragraph(
        "Quarterly Preventive &amp; Predictive Maintenance Survey | Unit 101 (Crude Distillation) | MRPL Mangalore",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1.2, color=c_accent, spaceBefore=0, spaceAfter=8))

    meta_data = [
        [
            Paragraph("ASSET TAG / ID", meta_label),
            Paragraph("EQUIPMENT DESCRIPTION", meta_label),
            Paragraph("INSPECTION DATE", meta_label),
            Paragraph("CONDITION STATUS", meta_label),
        ],
        [
            Paragraph("<b>P-102 (Booster)</b>", meta_val),
            Paragraph("<b>API 610 BB2 Crude Charge Pump</b>", meta_val),
            Paragraph("July 14, 2026 (Q3)", meta_val),
            Paragraph("ATTENTION REQUIRED", badge_style),
        ],
        [
            Paragraph("OPERATING SPEED / PWR", meta_label),
            Paragraph("PROCESS STREAM / UNIT", meta_label),
            Paragraph("LEAD INSPECTOR / ANALYST", meta_label),
            Paragraph("ISO 10816-3 CLASSIFICATION", meta_label),
        ],
        [
            Paragraph("2,980 RPM | 315 kW", meta_val),
            Paragraph("Unit 101 | Heavy Crude Bottoms", meta_val),
            Paragraph("A. Verma (ISO Cat IV #2940)", meta_val),
            Paragraph("<b>Zone C (Unacceptable Long-term)</b>", ParagraphStyle('ZC', parent=meta_val, textColor=c_red)),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[120, 160, 120, 123])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8f6f1")),
        ('BOX', (0,0), (-1,-1), 0.75, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
        ('BACKGROUND', (3,1), (3,1), c_accent), # Highlight status pill
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # ═════════════════════════════════════════════════════════════════════════
    # 2. EXECUTIVE SUMMARY & INSPECTION FINDINGS CALLOUT
    # ═════════════════════════════════════════════════════════════════════════
    exec_summary = [
        [
            Paragraph(
                "<b>Executive Inspection Summary:</b><br/>"
                "Comprehensive Q3 physical and predictive condition monitoring of booster pump <b>P-102</b> reveals an accelerated deterioration pattern. "
                "Overall vibration velocity has climbed to <b>3.7 mm/s RMS</b>, an increase of <b>+76.2%</b> relative to the January baseline (2.1 mm/s) and directly breaching "
                "the manufacturer continuous operation threshold of <b>3.0 mm/s</b> (P-102 Operating Manual §4.2). Concurrently, drive-end bearing temperature has reached "
                "<b>77°C (+13.2%)</b> with audible bearing rumble. While imminent catastrophic seizure is <b>NOT</b> indicated, immediate mechanical realignment and lubrication overhaul "
                "are mandatory to avert unplanned tripping of Unit 101 and downstream Reactor R-101.",
                body_style
            )
        ]
    ]
    exec_table = Table(exec_summary, colWidths=[523])
    exec_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fdfaf6")),
        ('BOX', (0,0), (-1,-1), 1, c_accent),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(exec_table)
    story.append(Spacer(1, 8))

    # ═════════════════════════════════════════════════════════════════════════
    # 3. CHRONOLOGICAL MEASUREMENT & SENSOR TREND (DATASET ds_4471)
    # ═════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("1.0 Chronological Sensor & Telemetry Progression", section_heading))
    story.append(HRFlowable(width="100%", thickness=0.5, color=c_border, spaceBefore=0, spaceAfter=5))

    trend_headers = [
        Paragraph("Inspection Cycle", table_header_style),
        Paragraph("Survey Date", table_header_style),
        Paragraph("Vibration RMS (mm/s)", table_header_style),
        Paragraph("DE Temp (°C)", table_header_style),
        Paragraph("NDE Temp (°C)", table_header_style),
        Paragraph("Discharge (bar)", table_header_style),
        Paragraph("Condition Assessment", table_header_style),
    ]
    trend_rows = [
        trend_headers,
        [
            Paragraph("<b>Baseline (Q1)</b>", table_cell_style),
            Paragraph("10-Jan-2026", table_cell_style),
            Paragraph("2.10", table_cell_mono),
            Paragraph("68.0", table_cell_mono),
            Paragraph("64.5", table_cell_mono),
            Paragraph("14.1", table_cell_mono),
            Paragraph("<font color='#2d7a4d'><b>✓ ISO Zone A (Good)</b></font>", table_cell_style),
        ],
        [
            Paragraph("<b>Routine (Q2)</b>", table_cell_style),
            Paragraph("11-Apr-2026", table_cell_style),
            Paragraph("2.80", table_cell_mono),
            Paragraph("71.4", table_cell_mono),
            Paragraph("67.2", table_cell_mono),
            Paragraph("13.9", table_cell_mono),
            Paragraph("<font color='#b8721e'><b>⚠ ISO Zone B (Elevated)</b></font>", table_cell_style),
        ],
        [
            Paragraph("<b>Comprehensive (Q3)</b>", table_cell_style),
            Paragraph("14-Jul-2026", table_cell_style),
            Paragraph("<b>3.70 (+76.2%)</b>", table_cell_mono),
            Paragraph("<b>77.2 (+13.2%)</b>", table_cell_mono),
            Paragraph("74.0 (+14.7%)", table_cell_mono),
            Paragraph("13.8", table_cell_mono),
            Paragraph("<font color='#ba3838'><b>✕ ISO Zone C (Exceeded)</b></font>", table_cell_style),
        ],
        [
            Paragraph("<b>Advisory Limit</b>", ParagraphStyle('AL', parent=table_cell_style, fontName='Helvetica-Bold', textColor=c_accent_dark)),
            Paragraph("OEM Manual §4.2", table_cell_style),
            Paragraph("<b>3.00 Max</b>", table_cell_mono),
            Paragraph("<b>75.0 Max</b>", table_cell_mono),
            Paragraph("75.0 Max", table_cell_mono),
            Paragraph("14.0 ± 0.5", table_cell_mono),
            Paragraph("<b>Continuous Operational Boundary</b>", table_cell_style),
        ]
    ]
    trend_table = Table(trend_rows, colWidths=[85, 68, 78, 62, 62, 68, 100])
    trend_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_accent),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#fdfcfa")),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#f9f6f0")),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#fbf0eb")), # July alert row
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor("#ede6da")), # Limit row
    ]))
    story.append(trend_table)
    story.append(Spacer(1, 8))

    # ═════════════════════════════════════════════════════════════════════════
    # 4. VIBRATION FREQUENCY SPECTRUM & FFT ANALYSIS
    # ═════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("2.0 Vibration Spectrum & FFT Diagnostic Analysis", section_heading))
    story.append(HRFlowable(width="100%", thickness=0.5, color=c_border, spaceBefore=0, spaceAfter=5))

    fft_headers = [
        Paragraph("Frequency Component", table_header_style),
        Paragraph("Exact Peak (Hz)", table_header_style),
        Paragraph("Amplitude (mm/s)", table_header_style),
        Paragraph("Fault Signature Diagnosis", table_header_style),
        Paragraph("Severity", table_header_style),
    ]
    fft_rows = [
        fft_headers,
        [
            Paragraph("<b>1X Running Speed</b>", table_cell_style),
            Paragraph("49.67 Hz", table_cell_mono),
            Paragraph("1.82 mm/s", table_cell_mono),
            Paragraph("Dynamic unbalance; slight impeller fouling from heavy bottoms.", table_cell_style),
            Paragraph("<font color='#b8721e'>Moderate</font>", table_cell_style),
        ],
        [
            Paragraph("<b>2X Harmonic</b>", table_cell_style),
            Paragraph("99.34 Hz", table_cell_mono),
            Paragraph("1.58 mm/s", table_cell_mono),
            Paragraph("<b>Angular / Parallel Misalignment</b> across flexible spacer coupling.", table_cell_style),
            Paragraph("<font color='#ba3838'><b>High Alert</b></font>", table_cell_style),
        ],
        [
            Paragraph("<b>BPFO (Bearing Outer Race)</b>", table_cell_style),
            Paragraph("184.20 Hz", table_cell_mono),
            Paragraph("0.45 mm/s", table_cell_mono),
            Paragraph("Incipient outer raceway micro-spalling on Drive-End bearing.", table_cell_style),
            Paragraph("<font color='#b8721e'>Monitor</font>", table_cell_style),
        ],
        [
            Paragraph("<b>Blade Pass Frequency (BPF)</b>", table_cell_style),
            Paragraph("298.00 Hz (6-blade)", table_cell_mono),
            Paragraph("0.22 mm/s", table_cell_mono),
            Paragraph("Hydraulic vane interaction; normal recirculatory pass.", table_cell_style),
            Paragraph("<font color='#2d7a4d'>Normal</font>", table_cell_style),
        ],
    ]
    fft_table = Table(fft_rows, colWidths=[110, 75, 75, 200, 63])
    fft_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2d2a26")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#fdfcfa")),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#fcf1ec")), # 2X Alert
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#fdfcfa")),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor("#f9f7f2")),
    ]))
    story.append(fft_table)
    story.append(PageBreak())

    # ═════════════════════════════════════════════════════════════════════════
    # 5. PHYSICAL & MECHANICAL INSPECTION CHECKLIST
    # ═════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("3.0 Physical & Mechanical Subsystem Checklist", section_heading))
    story.append(HRFlowable(width="100%", thickness=0.5, color=c_border, spaceBefore=0, spaceAfter=5))

    checklist_headers = [
        Paragraph("Inspection Subsystem", table_header_style),
        Paragraph("Observed Physical Condition", table_header_style),
        Paragraph("Engineering Assessment", table_header_style),
        Paragraph("Status", table_header_style),
    ]
    checklist_rows = [
        checklist_headers,
        [
            Paragraph("<b>Baseplate & Anchor Bolts</b>", table_cell_style),
            Paragraph("Holding bolts inspected; torque verified at 285 Nm. No cracks in grout.", table_cell_style),
            Paragraph("Foundation rigid; no soft-foot detected on casing pads.", table_cell_style),
            Paragraph("<font color='#2d7a4d'><b>PASS</b></font>", table_cell_style),
        ],
        [
            Paragraph("<b>Coupling & Guard</b>", table_cell_style),
            Paragraph("Metallic disc-pack coupling. Minor elastomeric wear dust inside guard.", table_cell_style),
            Paragraph("Consistent with 2X harmonic misalignment signature.", table_cell_style),
            Paragraph("<font color='#b8721e'><b>ATTENTION</b></font>", table_cell_style),
        ],
        [
            Paragraph("<b>Mechanical Seals (Plan 53A)</b>", table_cell_style),
            Paragraph("Barrier fluid reservoir level steady. Gland weepage: 1 drop/min.", table_cell_style),
            Paragraph("Within allowable operational limit (<5 drops/min). Seal face intact.", table_cell_style),
            Paragraph("<font color='#2d7a4d'><b>PASS</b></font>", table_cell_style),
        ],
        [
            Paragraph("<b>Lube Oil (ISO VG 68)</b>", table_cell_style),
            Paragraph("Oil level in sight glass normal; slight darkening observed.", table_cell_style),
            Paragraph("Viscosity 64 cSt @ 40°C. Lab oil sampling recommended.", table_cell_style),
            Paragraph("<font color='#b8721e'><b>MONITOR</b></font>", table_cell_style),
        ],
        [
            Paragraph("<b>Suction Strainer DP</b>", table_cell_style),
            Paragraph("Differential pressure across strainer: 0.18 bar (Clean).", table_cell_style),
            Paragraph("No evidence of cavitation, cavitation noise, or starvation.", table_cell_style),
            Paragraph("<font color='#2d7a4d'><b>PASS</b></font>", table_cell_style),
        ],
    ]
    check_table = Table(checklist_rows, colWidths=[120, 185, 160, 58])
    check_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_accent_dark),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#fdfcfa")),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#fbf4ee")),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#fdfcfa")),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor("#fbf4ee")),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor("#fdfcfa")),
    ]))
    story.append(check_table)
    story.append(Spacer(1, 8))

    # ═════════════════════════════════════════════════════════════════════════
    # 6. PROCESS TOPOLOGY & PLANT INTERCONNECTION RISK (P&ID)
    # ═════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("4.0 Process Topology & Operational Consequence (P&ID)", section_heading))
    story.append(HRFlowable(width="100%", thickness=0.5, color=c_border, spaceBefore=0, spaceAfter=5))

    pid_box = [
        [
            Paragraph("<b>Topological Flow Path:</b>", meta_label),
            Paragraph("<b>Crude Buffer Drum T-101 -&gt; Booster Pump P-102 -&gt; Control Valve V-204 -&gt; Hydrocracker Reactor R-101</b>", table_cell_mono),
        ],
        [
            Paragraph("<b>Process Hazard Analysis:</b>", meta_label),
            Paragraph(
                "Booster Pump P-102 provides essential feed pressure to the continuous Hydrocracker reaction train (R-101). "
                "An unscheduled trip of P-102 induces immediate feed starvation, causing severe thermal runaway risk in R-101 catalyst beds, "
                "triggering emergency flare depressurization and an estimated production downtime impact of $280,000/day.",
                body_style
            ),
        ]
    ]
    pid_table = Table(pid_box, colWidths=[140, 383])
    pid_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f9f6f0")),
        ('BOX', (0,0), (-1,-1), 0.75, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(pid_table)
    story.append(Spacer(1, 8))

    # ═════════════════════════════════════════════════════════════════════════
    # 7. CORRECTIVE ACTION PLAN & MAINTENANCE WORK ORDERS
    # ═════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("5.0 Corrective Action Plan & Maintenance Work Orders", section_heading))
    story.append(HRFlowable(width="100%", thickness=0.5, color=c_border, spaceBefore=0, spaceAfter=5))

    action_headers = [
        Paragraph("WO Priority", table_header_style),
        Paragraph("Action Description", table_header_style),
        Paragraph("Target Window", table_header_style),
        Paragraph("Responsible Craft", table_header_style),
        Paragraph("Expected Outcome", table_header_style),
    ]
    action_rows = [
        action_headers,
        [
            Paragraph("<font color='#ba3838'><b>P1 (Urgent)</b></font>", table_cell_style),
            Paragraph("<b>Laser Shaft Realignment:</b> Perform hot laser alignment across pump-motor coupling; replace worn spacer discs.", table_cell_style),
            Paragraph("Within 72 Hours", table_cell_mono),
            Paragraph("Millwright / Reliability", table_cell_style),
            Paragraph("Eliminate 2X harmonic; reduce vibration below 2.5 mm/s.", table_cell_style),
        ],
        [
            Paragraph("<font color='#b8721e'><b>P2 (Routine)</b></font>", table_cell_style),
            Paragraph("<b>Lube Oil Flush & Replenishment:</b> Drain bearing housings, flush debris, refill with synthetic Mobil SHC 626.", table_cell_style),
            Paragraph("Within 7 Days", table_cell_mono),
            Paragraph("Lubrication Specialist", table_cell_style),
            Paragraph("Reduce DE bearing temp from 77°C to <70°C.", table_cell_style),
        ],
        [
            Paragraph("<font color='#2d7a4d'><b>P3 (Planned)</b></font>", table_cell_style),
            Paragraph("<b>Spectral Re-Survey & Bearing Overhaul:</b> 2-week follow-up vibration survey. If BPFO persists, replace DE bearing.", table_cell_style),
            Paragraph("Next Plant Window", table_cell_mono),
            Paragraph("Rotating Equip Engineer", table_cell_style),
            Paragraph("Prevent outer ring fatigue failure.", table_cell_style),
        ],
    ]
    action_table = Table(action_rows, colWidths=[65, 175, 80, 95, 108])
    action_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_accent),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#fdf9f7")),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#fbf7f0")),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#f8fbf8")),
    ]))
    story.append(action_table)
    story.append(Spacer(1, 10))

    # ═════════════════════════════════════════════════════════════════════════
    # 8. CERTIFICATION, VERIFICATION & FORENSIC SIGN-OFF
    # ═════════════════════════════════════════════════════════════════════════
    sign_headers = [
        [
            Paragraph("<b>INSPECTED & REPORTED BY:</b>", meta_label),
            Paragraph("<b>TECHNICAL REVIEW & CONCURRENCE:</b>", meta_label),
            Paragraph("<b>KAVACHAI SOVEREIGN AI VERIFICATION:</b>", meta_label),
        ],
        [
            Paragraph(
                "<b>A. Verma</b><br/>"
                "Lead Vibration Analyst (ISO 18436 Cat IV)<br/>"
                "Refinery Condition Monitoring Group<br/>"
                "Signature: <i>[Verified Digital Seal]</i>",
                body_style
            ),
            Paragraph(
                "<b>Dr. R. K. Nair</b><br/>"
                "Chief Rotating Equipment Engineer<br/>"
                "Plant Reliability Division · MRPL<br/>"
                "Approval: <b>APPROVED FOR WORK ORDER</b>",
                body_style
            ),
            Paragraph(
                "<b>Verification Status: VERIFIED (95%)</b><br/>"
                "Telemetry Hash: <code>sha256:7f4c029...</code><br/>"
                "Grounded Evidence: 100% Citations Intact<br/>"
                "Air-Gapped Sovereign Enforcement",
                body_style
            ),
        ]
    ]
    sign_table = Table(sign_headers, colWidths=[174, 174, 175])
    sign_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8f6f1")),
        ('BOX', (0,0), (-1,-1), 0.75, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(sign_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Inspection report generated successfully at: {output_path}")


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "P-102_Inspection_Report.pdf").resolve()
    generate_inspection_report_pdf(target)
