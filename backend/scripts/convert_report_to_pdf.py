import os
import re
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
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
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#91887b"))
        
        # Header (on pages after the first)
        if self._pageNumber > 1:
            self.drawString(36, 756, "KavachAI — Application Verification & Evaluation Report")
            self.setStrokeColor(colors.HexColor("#e2dacd"))
            self.setLineWidth(0.5)
            self.line(36, 750, 576, 750)
            
        # Footer
        self.setStrokeColor(colors.HexColor("#e2dacd"))
        self.setLineWidth(0.5)
        self.line(36, 38, 576, 38)
        self.drawString(36, 26, "CONFIDENTIAL & SOVEREIGN · MRPL SIH26117")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 26, page_str)
        self.restoreState()

def md_to_pdf(md_path, pdf_path):
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    
    # Custom Warm Minimal styles
    c_primary = colors.HexColor("#2d2a26")
    c_accent = colors.HexColor("#c45d3e")
    c_text2 = colors.HexColor("#655f56")
    c_text3 = colors.HexColor("#91887b")
    c_surface = colors.HexColor("#f7f4ee")
    c_border = colors.HexColor("#e2dacd")
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_accent,
        spaceAfter=12,
    )
    
    h1_style = ParagraphStyle(
        'DocH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=c_accent,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )
    
    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=c_primary,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=c_primary,
        spaceAfter=5,
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_text2,
        spaceAfter=3,
    )

    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3,
    )

    code_style = ParagraphStyle(
        'DocCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=6.5,
        leading=8.5,
        textColor=colors.HexColor("#1e293b"),
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=c_primary,
    )

    story = []
    lines = content.split("\n")
    i = 0
    n = len(lines)

    def clean_inline(text):
        # Convert markdown bold/italic/code to reportlab tags
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
        text = re.sub(r'`(.+?)`', r'<font face="Courier" color="#c45d3e"><b>\1</b></font>', text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'<u>\1</u>', text)
        return text

    while i < n:
        line = lines[i]

        # Skip main title if already added or process
        if line.startswith("# "):
            raw_title = clean_inline(line[2:].strip())
            story.append(Paragraph(raw_title, title_style))
            i += 1
            continue

        if line.startswith("## "):
            raw_h1 = clean_inline(line[3:].strip())
            story.append(Paragraph(raw_h1, h1_style))
            story.append(HRFlowable(width="100%", thickness=0.75, color=c_border, spaceBefore=2, spaceAfter=6))
            i += 1
            continue

        if line.startswith("### "):
            raw_h2 = clean_inline(line[4:].strip())
            story.append(Paragraph(raw_h2, h2_style))
            i += 1
            continue

        if line.startswith("```"):
            # Code block / ASCII diagram
            code_lines = []
            i += 1
            while i < n and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1 # skip closing
            code_text = "\n".join(code_lines)
            
            p_code = Preformatted(code_text, code_style)
            # Wrap in a subtle card table
            code_table = Table([[p_code]], colWidths=[540])
            code_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8f6f0")),
                ('BOX', (0,0), (-1,-1), 0.5, c_border),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('RIGHTPADDING', (0,0), (-1,-1), 8),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(code_table)
            story.append(Spacer(1, 6))
            continue

        if line.strip().startswith("|") and line.strip().endswith("|"):
            # Markdown table
            table_rows = []
            while i < n and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                row_str = lines[i].strip()
                # Check if separator row (|---|---|)
                if re.match(r'^\|(\s*:?-+:?\s*\|)+$', row_str):
                    i += 1
                    continue
                cells = [c.strip() for c in row_str.split("|")[1:-1]]
                table_rows.append(cells)
                i += 1
            
            if table_rows:
                num_cols = len(table_rows[0])
                total_w = 540
                col_w = [total_w / num_cols] * num_cols
                # Adjust column widths for common tables
                if num_cols == 5:
                    col_w = [65, 100, 110, 175, 90]
                elif num_cols == 3:
                    col_w = [140, 140, 260]

                formatted_data = []
                for row_idx, row in enumerate(table_rows):
                    f_row = []
                    for c_text in row:
                        style = table_header_style if row_idx == 0 else table_cell_style
                        f_row.append(Paragraph(clean_inline(c_text), style))
                    formatted_data.append(f_row)

                t = Table(formatted_data, colWidths=col_w)
                t_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), c_accent),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
                    ('BOX', (0, 0), (-1, -1), 0.5, c_border),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ]
                for r in range(1, len(formatted_data)):
                    if r % 2 == 0:
                        t_style.append(('BACKGROUND', (0, r), (-1, r), colors.HexColor("#fbf9f5")))
                t.setStyle(TableStyle(t_style))
                story.append(t)
                story.append(Spacer(1, 6))
            continue

        if line.startswith("- ") or line.startswith("* "):
            raw_bullet = "&bull;  " + clean_inline(line[2:].strip())
            story.append(Paragraph(raw_bullet, bullet_style))
            i += 1
            continue

        if re.match(r'^\d+\.\s', line):
            raw_num = clean_inline(line.strip())
            story.append(Paragraph(raw_num, bullet_style))
            i += 1
            continue

        if line.startswith("---"):
            story.append(HRFlowable(width="100%", thickness=0.5, color=c_border, spaceBefore=4, spaceAfter=6))
            i += 1
            continue

        stripped = line.strip()
        if stripped:
            if stripped.startswith("**System:**") or stripped.startswith("**Problem"):
                story.append(Paragraph(clean_inline(stripped), meta_style))
            else:
                story.append(Paragraph(clean_inline(stripped), body_style))
        else:
            story.append(Spacer(1, 3))
        i += 1

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF generated successfully at: {pdf_path}")

if __name__ == "__main__":
    src_md = Path(sys.argv[1] if len(sys.argv) > 1 else "application_verification_report.md").resolve()
    dst_pdf = Path(sys.argv[2] if len(sys.argv) > 2 else "application_verification_report.pdf").resolve()
    md_to_pdf(src_md, dst_pdf)
