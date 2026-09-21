"""
Test Qwen2.5-VL on the generated Complex Refinery P&ID and Forensic Investigation Report PDF.
"""

import sys
import json
from pathlib import Path

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from app.orchestrator.model_router import model_router
import fitz

async def main():
    pdf_path = Path(r"c:\Users\HP\Desktop\SIH\KavachAI - Copy\Complex_Refinery_P&ID_and_Forensic_Investigation_Report.pdf")
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        return

    print(f"Loading PDF: {pdf_path} (Size: {pdf_path.stat().st_size} bytes)")
    doc = fitz.open(str(pdf_path))
    print(f"Total pages: {len(doc)}")
    
    page = doc[0]
    pix = page.get_pixmap(dpi=150)
    img_bytes = pix.tobytes("png")
    print(f"Rendered Page 1 to PNG: {len(img_bytes)} bytes")

    equipment_id = "P-102"
    prompt = f"""You are an industrial engineer AI analyzing a Process and Instrumentation Diagram (P&ID) or engineering drawing.
Target equipment to locate: "{equipment_id}".

Analyze the drawing thoroughly and return a JSON object with:
- "found": true if {equipment_id} appears in the diagram, else false
- "connections": array of directly connected immediate upstream and downstream equipment tags (e.g. ["STR-101", "E-103"])
- "process_sequence": array of all sequential equipment nodes in the process stream from start to finish (e.g. ["TK-101", "DS-101", "STR-101", "P-102", "E-103", "FCV-204", "F-101", "R-101"])
- "bounding_box": [ymin, xmin, ymax, xmax] normalized on a 0-1000 scale, or null
- "visual_description": detailed technical engineering observation explaining the full piping topology, fluid path, upstream source, downstream destinations, control valves, telemetry, and any alerts/vulnerabilities
- "confidence": confidence score between 0.0 and 1.0

Return strictly valid JSON."""

    print("\nQuerying Qwen2.5-VL via ModelRouter...")
    raw_response = await model_router.generate_vision(
        prompt=prompt,
        image_bytes=img_bytes,
        temperature=0.1,
        format="json",
    )

    print("\n--- QWEN2.5-VL RAW RESPONSE ---")
    print(raw_response)

if __name__ == "__main__":
    asyncio.run(main())
