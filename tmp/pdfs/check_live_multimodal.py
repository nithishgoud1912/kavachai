"""Read only synthetic fixtures; exercise installed local model boundaries."""
import asyncio
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'backend'))
os.environ['OLLAMA_HOST'] = 'http://127.0.0.1:11434'
from app.services.inspection_analysis import inspect_attachments, analyse_table
from app.orchestrator.model_router import model_router
from app.db.object_store import object_store
from app.agents.base import EvidenceBundle, EvidenceItem, DocumentChunk
from app.agents.synthesis import synthesize
from app.agents.verification import verify


async def main():
    report = root / 'output/pdf/MRPL_Style_Synthetic_P102A_Inspection_Report.pdf'
    image = root / 'output/pdf/P102A_visual_inspection_sheet.png'
    with patch.object(object_store, 'get_raw_file', return_value=(report.read_bytes(), report.name)):
        inputs = inspect_attachments([{'source_id':'synthetic-report'}])
    print(json.dumps({'visual_pages':[target.page for target in inputs.visuals],
                      'numeric_tables':[(table.name, table.numeric_columns) for table in inputs.tables]}), flush=True)
    checks, chunks = {}, []
    try:
        print('Invoking vision model on the synthetic plate...', flush=True)
        visual = await model_router.generate_vision(
            'Describe the equipment labels, the lower-right guard fixing point, the marked checklist answer and the liquid collection values. Report uncertainty. Under 150 words.',
            image.read_bytes(), format=None, max_tokens=300)
        checks['vision'] = {'model':model_router.get_model('vision'), 'returned_chars':len(visual), 'observation':visual}
        chunks.append(DocumentChunk(source_id='synthetic-report',page=3,score=1,chunk_text='Model-derived visual observation: '+visual))
        print('Vision returned.', flush=True)
    except Exception as exc:
        checks['vision'] = {'error':str(exc), 'detail':getattr(getattr(exc.__context__, 'response', None), 'text', '')}
        print(json.dumps(checks['vision']), flush=True)
    if '--vision-only' in sys.argv:
        await model_router.close()
        (root/'tmp/pdfs/live_vision_result.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
        print(json.dumps(checks),flush=True)
        return
    try:
        print('Invoking coding model for the synthetic measurement table...', flush=True)
        calculated = await analyse_table(inputs.tables[0], 'Calculate mean vibration and first-to-last percentage change. Do not combine different assets or periods.')
        checks['coding'] = {'model':model_router.get_model('coding'), 'calculated_results':calculated['results']}
        chunks.append(DocumentChunk(source_id='synthetic-report',page=2,score=1,chunk_text='COMPUTED DATA: '+json.dumps(calculated)))
        print('Coder plan validated and calculated.', flush=True)
    except Exception as exc:
        checks['coding'] = {'error':str(exc)}
        print(json.dumps(checks['coding']), flush=True)
    try:
        print('Invoking reasoning and verification on combined evidence...', flush=True)
        bundle = EvidenceBundle(document_findings=chunks, evidence_items=[
            EvidenceItem(type='document',source_id=c.source_id,label=f'Synthetic inspection page {c.page}',page=c.page) for c in chunks])
        draft = await synthesize(bundle, 'Summarize only the synthetic recorded observations and computed vibration results; cite exact E IDs. State limitations.')
        verified = await verify(draft,bundle)
        checks['reasoning'] = {'model':model_router.get_model('text_reasoning'), 'draft_findings':len(draft.findings),
                               'statuses':[f.verification_status.value for f in verified.findings]}
        print(json.dumps(checks['reasoning']), flush=True)
    except Exception as exc:
        checks['reasoning'] = {'error':str(exc)}
        print(json.dumps(checks['reasoning']), flush=True)
    await model_router.close()
    (root/'tmp/pdfs/live_multimodal_result.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print(json.dumps(checks), flush=True)


asyncio.run(main())
