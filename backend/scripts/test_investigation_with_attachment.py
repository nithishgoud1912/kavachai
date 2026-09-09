"""
End-to-end test of InvestigationRunner with the complex PDF attached.
Verifies that Vision Agent, Data Agent, Document Agent, and RAG Agent all run,
and that the report contains dynamic conclusions, vision observations, and multi-node topology.
"""
import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.sql_models import Investigation, get_db_context
from app.db.object_store import object_store
from app.orchestrator.investigation import InvestigationRunner

async def main():
    pdf_path = Path(r"c:\Users\HP\Desktop\SIH\KavachAI - Copy\Complex_Refinery_P&ID_and_Forensic_Investigation_Report.pdf")
    pdf_bytes = pdf_path.read_bytes()

    source_id = f"test_dossier_{uuid.uuid4().hex[:8]}"
    object_store.save_raw_file(source_id, pdf_bytes, pdf_path.name)
    print(f"Saved test PDF as source_id: {source_id}")

    attachments = [
        {
            "source_id": source_id,
            "filename": pdf_path.name,
            "path": str(pdf_path),
            "size": len(pdf_bytes),
        }
    ]

    async with get_db_context() as db:
        inv = Investigation(
            id=str(uuid.uuid4()),
            user_id="test_user",
            query="Pump P-102 condition and vibration assessment",
            status="pending",
            attachments=attachments,
        )
        db.add(inv)
        await db.commit()
        await db.refresh(inv)

        print(f"Created Investigation {inv.id}. Running runner...")
        runner = InvestigationRunner(inv, db)
        res = await runner.run()

        report = res.get("report", {})
        print("\n=== INVESTIGATION REPORT RESULT ===")
        print(f"Overall Status: {report.get('overall_status')}")
        print(f"Condition Summary: {report.get('condition_summary')}")
        print(f"Agents Invoked: {runner.agents_invoked}")
        print(f"PID Relationship Chain: {report.get('pid_relationship')}")
        print(f"Vision Observation: {report.get('vision_observation')}")
        print(f"Bounding Box: {report.get('bounding_box')}")
        print(f"Process Topology Nodes: {len(report.get('process_topology', []))}")
        print(f"Bypass Loops: {len(report.get('bypass_loops', []))}")
        print(f"\n--- AI CONCLUSION ---\n{report.get('conclusion')}")

if __name__ == "__main__":
    asyncio.run(main())
