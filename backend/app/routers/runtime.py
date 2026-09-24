"""Observed runtime health, configurable model routing and sandbox execution."""
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from app.deps import require_permission, get_current_session
from app.db.database import get_db
from app.db.sql_models import SystemSetting, AuditEvent, WorkbenchJob
from app.orchestrator.model_router import model_router
from app.middleware.egress_monitor import egress_monitor
from app.services.code_sandbox import run_code_in_sandbox, check_docker_available
from app.services.security_audit import append_security_event
router = APIRouter(prefix='/api/v1', tags=['runtime'])

class CodeRequest(BaseModel):
    code: str = Field(min_length=1, max_length=100000)
    language: str = 'python'
    timeout: int = Field(default=30, ge=1, le=60)

@router.post('/sandbox/run')
async def run_code(body: CodeRequest, principal=Depends(require_permission('sandbox:request')), db=Depends(get_db)):
    if body.language != 'python': raise HTTPException(422, 'Only Python is provisioned')
    started=time.monotonic()
    result=await run_code_in_sandbox(body.code, body.timeout)
    await append_security_event(db,event_type='SANDBOX_EXECUTION',outcome='success' if result.success else 'failed',actor_user_id=principal.user_id,detail={'exit_code':result.exit_code})
    return dict(id=str(time.time_ns()),code=body.code,language='python',**result.to_dict(),execution_time_ms=int((time.monotonic()-started)*1000),
                memory_peak_mb=None,is_sandboxed=result.exit_code != 125,status='success' if result.success else 'timeout' if result.timed_out else 'runtime_error')

@router.get('/network-monitor')
async def network(type: str | None=None, principal=Depends(require_permission('workspace:read'))):
    return list(egress_monitor.logs) if type=='connections' else egress_monitor.get_sovereignty_report()

@router.get('/models')
async def models(type: str | None=None, session=Depends(get_current_session), db=Depends(get_db)):
    if type=='logs':
        from app.access import owner_filter
        jobs=(await db.execute(select(WorkbenchJob).where(owner_filter(WorkbenchJob,session)).order_by(WorkbenchJob.created_at.desc()).limit(50))).scalars()
        return [dict(id=f"{j.id}:{i}",timestamp=e.get('timestamp',j.created_at.isoformat()),task_id=j.id,
                     query_snippet='',detected_intent=e['data'].get('task_type',''),selected_model=e['data']['model'],
                     reason=e['data'].get('reason','Backend selection'),confidence=0)
                for j in jobs for i,e in enumerate(j.events or []) if e['type']=='model_selected']
    if type=='rules':
        return [dict(id=k,task_type=k,preferred_model_id=v,enabled=True,condition_description='Backend task capability') for k,v in model_router._model_map.items()]
    try:
        tags=(await model_router._client.get('/api/tags')).json().get('models',[])
        running=(await model_router._client.get('/api/ps')).json().get('models',[])
    except Exception as exc: raise HTTPException(503, 'Local model service unavailable') from exc
    loaded={m['name']:m for m in running}
    return [dict(id=m['name'],name=m['name'],display_name=m['name'],provider='ollama',size=str(m.get('size',0)),
                 context_length=loaded.get(m['name'],{}).get('context_length',0),capabilities=['code' if k=='coding' else 'reasoning' if k in ('text_reasoning','classification') else k for k,v in model_router._model_map.items() if v==m['name']],
                 status='loaded' if m['name'] in loaded else 'cold',vram_usage_gb=loaded.get(m['name'],{}).get('size_vram',0)/1024**3,
                 max_vram_gb=0,latency_p95_ms=0,endpoint='local Ollama',digest=m.get('digest')) for m in tags]

class ModelUpdate(BaseModel):
    rule: dict

@router.post('/models')
async def update_model(body: ModelUpdate, principal=Depends(require_permission('models:manage')), db=Depends(get_db)):
    rule=body.rule
    task=rule.get('task_type')
    model=rule.get('preferred_model_id')
    if task not in model_router._model_map or not isinstance(model,str) or not model.strip(): raise HTTPException(422,'Choose an existing backend task capability and installed model')
    if task=='embedding': raise HTTPException(409,'Embedding changes require an offline reindex into a new collection; configure EMBEDDING_MODEL and restart')
    tags=(await model_router._client.get('/api/tags')).json().get('models',[])
    if model not in [m['name'] for m in tags]: raise HTTPException(422,'Model must be provisioned locally first')
    mapping={**model_router._model_map,task:model}
    row=await db.get(SystemSetting,'routing')
    if row: row.value=mapping
    else: db.add(SystemSetting(key='routing',value=mapping))
    await db.commit()
    model_router._model_map=mapping
    await append_security_event(db,event_type='MODEL_ROUTING_UPDATED',outcome='success',actor_user_id=principal.user_id,detail={'task_type':task,'model':model})
    return rule

@router.get('/readiness')
async def readiness(session=Depends(get_current_session)):
    return {'inference_available':await model_router.is_ollama_available(),'sandbox_available':await check_docker_available(),
            'network_observer_active':egress_monitor.installed,'airgap_verified':False}

@router.get('/security-events')
async def security_events(principal=Depends(require_permission('audit:read')),db=Depends(get_db)):
    rows=(await db.execute(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(500))).scalars()
    return [dict(id=e.id,event_type=e.event_type,outcome=e.outcome,actor_user_id=e.actor_user_id,resource_id=e.resource_id,
                 created_at=e.created_at.isoformat(),detail=e.detail,event_hash=e.event_hash,previous_event_hash=e.previous_event_hash) for e in rows]
