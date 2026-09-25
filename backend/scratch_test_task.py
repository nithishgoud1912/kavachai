import asyncio
import traceback
from app.db.database import async_session
from app.db.sql_models import WorkbenchJob
from app.agents.document_agent import retrieve
from app.agents.base import EvidenceBundle, EvidenceItem
from app.agents.synthesis import synthesize

async def run_test():
    async with async_session() as db:
        job = await db.get(WorkbenchJob, "64620eaf-cf6f-4e0c-a8a9-b392fb15b677")
        payload = job.payload
        query = payload['query']
        selected = [a['source_id'] for a in payload['attachments'] if a.get('source_id')]
        print(f"Selected sources: {selected}")
        
        print("Retrieving chunks...")
        chunks = await retrieve(query, {'source_ids': selected}, n_results=12)
        print(f"Retrieved {len(chunks)} chunks")
        for i, c in enumerate(chunks):
            print(f"  Chunk {i}: len={len(c.chunk_text)}, source={c.source_id}")

        evidence = [EvidenceItem(type='document', source_id=c.source_id, label=c.source_id, page=c.page) for c in chunks]
        bundle = EvidenceBundle(document_findings=chunks, evidence_items=evidence)

        print("\nCalling synthesize...")
        try:
            draft = await synthesize(bundle, query)
            print("Synthesize succeeded!")
            print("Condition summary:", draft.condition_summary)
            print("Findings count:", len(draft.findings))
        except Exception as e:
            print("Synthesize failed with exception:")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
