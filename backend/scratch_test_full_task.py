import asyncio
import traceback
from app.db.database import async_session
from app.db.sql_models import WorkbenchJob
from app.agents.document_agent import retrieve
from app.agents.base import EvidenceBundle, EvidenceItem
from app.agents.synthesis import synthesize
from app.agents.verification import verify
from app.services.report_service import build_report
from app.services.document_export import generate_briefing_docx

async def run_full_test():
    async with async_session() as db:
        job = await db.get(WorkbenchJob, "64620eaf-cf6f-4e0c-a8a9-b392fb15b677")
        payload = job.payload
        query = payload['query']
        selected = [a['source_id'] for a in payload['attachments'] if a.get('source_id')]
        print(f"1. Retrieving chunks for query: '{query}' with sources: {selected}")
        chunks = await retrieve(query, {'source_ids': selected}, n_results=12)
        print(f"   Retrieved {len(chunks)} chunks")

        evidence = [EvidenceItem(type='document', source_id=c.source_id, label=c.source_id, page=c.page) for c in chunks]
        bundle = EvidenceBundle(document_findings=chunks, evidence_items=evidence)

        print("2. Synthesizing findings...")
        report = None
        revision_query = query
        for attempt in range(3):
            print(f"   Attempt {attempt+1} synthesis...")
            draft = await synthesize(bundle, revision_query)
            print(f"   Attempt {attempt+1} verification ({len(draft.findings)} findings)...")
            verification = await verify(draft, bundle)
            supported = any(f.verification_status.value == 'supported' for f in verification.findings)
            print(f"   Supported: {supported}, confidence: {verification.overall_confidence}")
            if supported:
                report = build_report(job.id, query, verification, bundle)
                print("   Report built successfully!")
                break
            revision_query = query + '\nRevise previous draft to address unsupported claims.'

        if not report:
            print("FAILED: Report could not be grounded")
            return

        print("3. Generating Office deliverable (docx)...")
        path = await generate_briefing_docx(job.id, report['conclusion'], report)
        print(f"SUCCESS! Deliverable generated at: {path}")

if __name__ == "__main__":
    asyncio.run(run_full_test())
