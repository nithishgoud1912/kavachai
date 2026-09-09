"""
Test vision_agent.analyze_pid on the complex dossier PDF.
"""
import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.vision_agent import analyze_pid
from app.db.object_store import object_store

async def main():
    pdf_path = Path(r"c:\Users\HP\Desktop\SIH\KavachAI - Copy\Complex_Refinery_P&ID_and_Forensic_Investigation_Report.pdf")
    data = pdf_path.read_bytes()
    
    # Store in object_store
    source_id = "complex_test_dossier_001"
    object_store.save_raw_file(
        source_id=source_id,
        file_content=data,
        filename=pdf_path.name
    )
    print(f"Stored file with source_id: {source_id}")

    print("Running analyze_pid(source_id, 'P-102')...")
    res = await analyze_pid(
        pid_source_id=source_id,
        equipment_id="P-102"
    )

    print("\n--- VISION AGENT RESULT ---")
    print(f"Found: {res.found}")
    print(f"Connections: {res.connections}")
    print(f"Confidence: {res.confidence}")
    print(f"Bounding Box: {res.bounding_box}")
    print(f"Process Sequence: {res.process_sequence}")
    print(f"Visual Description: {res.visual_description}")

if __name__ == "__main__":
    asyncio.run(main())
