"""
Test planner output on 'Pump P-102 condition and vibration assessment'
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.planner import plan
from app.agents.base import CorpusSummary

async def main():
    corpus = CorpusSummary(
        documents=1,
        datasets=1,
        pid_drawings=1,
        equipment_ids=["P-102"],
        document_types=["inspection_report", "pid_drawing"]
    )
    query = "Pump P-102 condition and vibration assessment"
    attachments = [{"filename": "Complex_Refinery_P&ID_and_Forensic_Investigation_Report.pdf", "source_id": "test_src"}]

    print(f"Testing planner for: '{query}'")
    res = await plan(query, corpus, attached_files=attachments)
    print(f"In scope: {res.is_in_scope}")
    print(f"Sub-tasks count: {len(res.sub_tasks)}")
    for st in res.sub_tasks:
        print(f" - [{st.agent.value}] {st.goal}")

if __name__ == "__main__":
    asyncio.run(main())
