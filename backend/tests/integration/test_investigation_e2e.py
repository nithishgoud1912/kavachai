"""Authenticated legacy investigation with real stores/PDF export and mocked inference.
The fixture supplies all claimed facts; this is not live-model acceptance evidence.
"""
import json
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.database import init_db
from app.orchestrator.model_router import model_router

@pytest.mark.asyncio
async def test_inspection_investigation_full_e2e():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app),base_url="http://test") as client:
        session=(await client.post('/api/v1/session',json={'name':'Vikram','department':'Reliability'})).json()['session_id']
        auth_headers={'Authorization':f'Bearer {session}'}
        with patch.object(model_router,'embed',AsyncMock(side_effect=lambda texts:[[0.1]*768 for _ in texts])):
            upload=await client.post('/api/v1/conversations/upload',headers=auth_headers,files={'file':('inspection.txt',b'The inspection found a loose cover on the test unit.','text/plain')})
            assert upload.status_code==200,upload.text
            source=upload.json()['source_id']
            plan={'is_in_scope':True,'sub_tasks':[{'agent':'document_agent','goal':'Read the inspection'}]}
            synthesis={'findings':[{'id':'f1','title':'Loose cover','detail':'The inspection found a loose cover.','evidence_refs':[source]}]}
            verified={'findings':[{'id':'f1','verification_status':'supported'}],'overall_confidence':80}
            with patch.object(model_router,'generate',AsyncMock(side_effect=[json.dumps(plan),json.dumps(synthesis),json.dumps(verified)])):
                result=await client.post('/api/v1/investigations',headers=auth_headers,json={'query':'Summarize the inspection','session_id':session})
            assert result.status_code==202,result.text
            id=result.json()['investigation_id']
            response=await client.get(f'/api/v1/investigations/{id}/report',headers=auth_headers)
            assert response.status_code==200,response.text
            report=response.json()
            assert report['verification_status']=='verified'
            assert report['findings'][0]['evidence'][0]['source_id']==source
            assert not report.get('pid_relationship')
            assert (await client.get(f'/api/v1/evidence/{source}',headers=auth_headers)).status_code==200
            export=await client.post(f'/api/v1/investigations/{id}/export',headers=auth_headers,json={'format':'pdf','include_audit_trail':True})
            assert export.status_code==200,export.text
            artifact=await client.get(export.json()['download_url'],headers=auth_headers)
            assert artifact.status_code==200 and artifact.content.startswith(b'%PDF')
