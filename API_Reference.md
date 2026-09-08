# API_Reference.md — KavachAI Backend API
**Base URL (prototype):** `http://localhost:8000/api/v1`
**Format:** JSON over HTTPS/HTTP; streaming endpoints use Server-Sent Events (SSE).
**Auth (prototype):** lightweight session token from `/session`; see `SRS.md` FR-ACC-1/2 — production RBAC/SSO is future scope.

---

## 1. Conventions

- All timestamps: ISO 8601 UTC (`2026-07-14T09:12:03Z`).
- All IDs: UUID v4 strings unless noted.
- Errors follow a consistent envelope:
```json
{
  "error": {
    "code": "EVIDENCE_NOT_FOUND",
    "message": "No evidence bundle exists for investigation_id abc123",
    "status": 404
  }
}
```
- Standard HTTP status codes: `200` success, `202` accepted/processing, `400` bad request, `401` unauthorized, `403` forbidden (permission-scoped retrieval), `404` not found, `422` validation error, `500` internal error.

---

## 2. Session

### `POST /session`
Create a lightweight demo session (FR-ACC-1).
**Request**
```json
{ "name": "Priya", "department": "HSE" }
```
**Response `200`**
```json
{
  "session_id": "b1e2...",
  "name": "Priya",
  "department": "HSE",
  "issued_at": "2026-07-14T09:00:00Z"
}
```
Session token returned via `Set-Cookie` (or `Authorization: Bearer <session_id>` for the SPA client).

---

## 3. Knowledge Base Ingestion

### `POST /knowledge-base/documents`
Upload and ingest a document (FR-ING-1..6). Multipart form upload.
**Request (multipart/form-data)**
| Field | Type | Notes |
|---|---|---|
| `file` | binary | PDF / DOCX / TXT / PNG / JPG |
| `document_type` | string | `inspection_report` \| `maintenance_history` \| `sop` \| `manual` \| `pid_drawing` \| `other` |
| `equipment_ids` | string[] (optional) | e.g. `["P-102"]` — aids retrieval tagging |
| `department_scope` | string (optional) | for permission-aware retrieval, FR-RAG-2 |

**Response `202`**
```json
{
  "document_id": "doc_9f21",
  "status": "processing",
  "chunks_expected": true
}
```

### `GET /knowledge-base/documents/{document_id}`
Returns ingestion status and metadata.
```json
{
  "document_id": "doc_9f21",
  "filename": "P-102_Inspection_July.pdf",
  "document_type": "inspection_report",
  "status": "ready",
  "pages": 4,
  "chunks": 12,
  "equipment_ids": ["P-102"],
  "ingested_at": "2026-07-14T09:05:12Z"
}
```

### `POST /knowledge-base/datasets`
Upload a structured time-series dataset (FR-ING-7). Multipart, `file` = CSV/XLSX.
**Response `200`**
```json
{
  "dataset_id": "ds_4471",
  "columns": ["timestamp", "equipment_id", "metric", "value", "unit"],
  "row_count": 214,
  "status": "ready"
}
```

### `GET /knowledge-base/summary`
Returns corpus overview for the workspace footer (Screen 2 in `Design.md`).
```json
{
  "documents": 7,
  "datasets": 1,
  "pid_drawings": 1
}
```

---

## 4. Investigation (Core Flow)

### `POST /investigations`
Start a new investigation. This is the Planner entry point (FR-PLN-1).
**Request**
```json
{
  "query": "Investigate Pump P-102 and determine whether its condition has deteriorated.",
  "session_id": "b1e2..."
}
```
**Response `202`**
```json
{
  "investigation_id": "inv_7788",
  "status": "planning",
  "stream_url": "/investigations/inv_7788/stream"
}
```

### `GET /investigations/{investigation_id}/stream` (SSE)
Streams the live agent timeline (Screen 3, `Design.md`). Each event:
```
event: agent_update
data: {
  "agent": "document_agent",
  "status": "complete",
  "message": "Found 4 inspection reports",
  "elapsed_ms": 1100
}
```
Event `agent` values: `planner`, `document_agent`, `data_agent`, `vision_agent`, `rag_agent`, `verification_agent`.
Event `status` values: `pending`, `working`, `complete`, `skipped`, `failed`.
Terminal event:
```
event: investigation_complete
data: { "investigation_id": "inv_7788", "report_url": "/investigations/inv_7788/report" }
```
Or, for out-of-scope queries (FR-PLN-2/FR-VER-4):
```
event: insufficient_evidence
data: { "investigation_id": "inv_7788", "message": "No relevant evidence found in the knowledge base." }
```

### `GET /investigations/{investigation_id}/report`
Fetch the final structured report (FR-RPT-1).
```json
{
  "investigation_id": "inv_7788",
  "query": "Investigate Pump P-102 and determine whether its condition has deteriorated.",
  "overall_status": "attention_required",
  "condition_summary": "Potential deterioration detected",
  "findings": [
    {
      "id": "f1",
      "title": "Increasing vibration",
      "detail": "Jan 2.1 → Apr 2.8 → Jul 3.7 mm/s (+76%)",
      "verification_status": "supported",
      "evidence": [
        { "type": "document", "source_id": "doc_1120", "label": "Inspection Report", "page": 4 },
        { "type": "document", "source_id": "doc_1121", "label": "Inspection Report", "page": 12 },
        { "type": "document", "source_id": "doc_1122", "label": "Inspection Report", "page": 17 }
      ]
    },
    {
      "id": "f2",
      "title": "Exceeds attention threshold",
      "detail": "Current 3.7 mm/s > spec 3.0 mm/s",
      "verification_status": "supported",
      "evidence": [
        { "type": "document", "source_id": "doc_1130", "label": "Pump Operating Manual", "page": null, "section": "4.2" }
      ]
    }
  ],
  "pid_relationship": ["T-101", "P-102", "V-204", "R-101"],
  "conclusion": "The available evidence indicates that P-102's condition has deteriorated over the observed period. Engineering inspection is recommended. The evidence does NOT establish imminent failure.",
  "confidence": 91,
  "verification_status": "verified",
  "generated_at": "2026-07-14T09:12:40Z"
}
```
`verification_status` (report-level): `verified` | `partially_verified` | `unverified`.
`findings[].verification_status`: `supported` | `partially_supported` | `unsupported` (per FR-VER-1).

### `GET /investigations/{investigation_id}/plan`
Returns the Planner's decomposition, for the timeline UI and for audit purposes.
```json
{
  "investigation_id": "inv_7788",
  "sub_tasks": [
    { "agent": "document_agent", "goal": "Find inspection reports mentioning P-102" },
    { "agent": "data_agent", "goal": "Compute vibration trend for P-102, Jan–Jul" },
    { "agent": "vision_agent", "goal": "Identify P-102 connectivity in P&ID" },
    { "agent": "rag_agent", "goal": "Retrieve operating threshold for this pump model" }
  ]
}
```

---

## 5. Evidence / Source Retrieval

### `GET /evidence/{source_id}`
Powers the Source Viewer panel (Screen 5, `Design.md`).
```json
{
  "source_id": "doc_1122",
  "type": "document",
  "filename": "P-102_Inspection_July.pdf",
  "page": 17,
  "excerpt": "Pump P-102 — Vibration: 3.7 mm/s. Temperature: 77°C. Status: Abnormal.",
  "view_url": "/files/doc_1122/page/17"
}
```
For dataset evidence:
```json
{
  "source_id": "ds_4471",
  "type": "dataset",
  "rows": [
    { "timestamp": "2026-01-10", "equipment_id": "P-102", "metric": "vibration", "value": 2.1, "unit": "mm/s" },
    { "timestamp": "2026-04-11", "equipment_id": "P-102", "metric": "vibration", "value": 2.8, "unit": "mm/s" },
    { "timestamp": "2026-07-09", "equipment_id": "P-102", "metric": "vibration", "value": 3.7, "unit": "mm/s" }
  ]
}
```
For vision/P&ID evidence:
```json
{
  "source_id": "pid_2201",
  "type": "pid_drawing",
  "filename": "Refinery_Plant_PID.pdf",
  "highlighted_component": "P-102",
  "connections": ["T-101", "V-204"],
  "view_url": "/files/pid_2201/annotated"
}
```

---

## 6. Report Export

### `POST /investigations/{investigation_id}/export`
**Request**
```json
{ "format": "pdf" }
```
**Response `200`**
```json
{ "export_id": "exp_331", "download_url": "/exports/exp_331.pdf" }
```

---

## 7. Audit Log

### `GET /audit-log?limit=50&offset=0`
```json
{
  "entries": [
    {
      "investigation_id": "inv_7788",
      "user": "Priya",
      "department": "HSE",
      "query": "Investigate Pump P-102 and determine whether its condition has deteriorated.",
      "agents_invoked": ["planner", "document_agent", "data_agent", "vision_agent", "rag_agent", "verification_agent"],
      "verification_status": "verified",
      "confidence": 91,
      "timestamp": "2026-07-14T09:12:40Z"
    }
  ],
  "total": 1
}
```
(FR-AUD-1/2 — entries are append-only; no `DELETE`/`PATCH` endpoint is exposed for this resource by design.)

---

## 8. Internal Agent Contracts

These are not public HTTP endpoints but the internal function/service contracts each agent implements, so any agent's underlying model can be swapped without touching the orchestrator (NFR-MNT-2).

### 8.1 Planner Agent
```
plan(query: str, corpus_summary: CorpusSummary) -> InvestigationPlan
InvestigationPlan = {
  sub_tasks: [{ agent: AgentName, goal: str }],
  is_in_scope: bool
}
```

### 8.2 Document Agent
```
retrieve(sub_task_goal: str, filters: {equipment_ids?, document_types?, department_scope?})
  -> [{ chunk_text: str, source_id: str, page: int, score: float }]
```

### 8.3 Data Agent
```
analyze(metric: str, equipment_id: str, dataset_id: str)
  -> { trend: "increasing"|"decreasing"|"stable", pct_change: float,
       data_points: [{timestamp, value, unit}], threshold_breach: bool|null }
```
Implemented with deterministic code (pandas), never delegated to the LLM (FR-DAT-2 / FR-SYN-3).

### 8.4 Vision Agent
```
analyze_pid(pid_source_id: str, equipment_id: str)
  -> { found: bool, connections: [str], confidence: float }
```

### 8.5 RAG Agent
```
retrieve_spec(query: str, equipment_id: str, filters: {department_scope?})
  -> [{ chunk_text: str, source_id: str, page: int|null, section: str|null }]
```

### 8.6 Synthesis (LLM)
```
synthesize(evidence_bundle: EvidenceBundle) -> DraftFindings
```
Receives only the structured `EvidenceBundle` assembled from §8.2–8.5 outputs — never raw, unretrieved documents (FR-SYN-1).

### 8.7 Verification Agent
```
verify(draft_findings: DraftFindings, evidence_bundle: EvidenceBundle)
  -> { findings: [Finding], overall_confidence: int, overall_status: "verified"|"partially_verified"|"unverified" }
```

---

## 9. Model Router (internal, future-facing interface)

Documented now so the architecture supports it later without rework (see `PRD.md` Future Scope):
```
route(task_type: "text_reasoning"|"vision"|"embedding"|"classification")
  -> ModelEndpoint   # always resolves to a local Ollama endpoint in this deployment
```
No agent calls a model directly; all model calls pass through this router, which is the sole point where "which model handles this" is decided — and the sole point that must be audited to guarantee `NFR-SEC-1` (no external inference calls).
