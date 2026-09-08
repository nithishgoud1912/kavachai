# KavachAI — Backend Build Plan
### Sovereign Industrial Agentic AI Workbench — Internal Round Prototype
Source of truth: `PRD.md`, `SRS.md`, `API_Reference.md`, `workflow.md`, `Design.md` (design only informs API shape, not backend logic).

---

## 0. How to use this document

This is a **sequential, phase-gated execution plan**. Each phase has: goal → inputs it depends on → concrete tasks → files/modules to produce → the requirement IDs it satisfies → a "definition of done" checklist. Do not start a phase until the previous phase's definition of done is met.

### 0.1 Non-negotiable ground rules for whoever (human or AI) executes this plan
1. **Never assume a missing detail — ask.** If a requirement doc doesn't specify something concretely (a filename, a model name, a port, a threshold value, a corpus file), stop and ask the user. Do not invent plausible-sounding values and continue silently. Section 1 below lists every question that MUST be answered before Phase 0 starts, and each phase repeats any question specific to it.
2. **No silent scope creep and no silent scope cuts.** Build exactly what `PRD.md` §6 (P0/P1) and `SRS.md` §3 specify. Do not add production auth, cloud hosting, or extra agents. Do not skip a P0 requirement because it seems hard — flag it to the user instead of quietly dropping it.
3. **Traceability first.** Every module/function you write should have a comment referencing the FR/NFR ID(s) it implements (e.g. `# implements FR-DAT-2`). This is how you and the user verify nothing was missed.
4. **The LLM never does arithmetic and never sees raw documents.** This is a hard architectural constraint (FR-SYN-1, FR-SYN-3, FR-DAT-2) — not a style preference. If you're tempted to let the LLM "just compute the percentage change," stop; that's the Data Agent's job.
5. **All inference stays local.** No agent, router, or fallback path may call an external API (OpenAI/Gemini/Anthropic/etc.) for anything touching corpus content or query text (NFR-SEC-1). If a local model is unavailable, fail loudly to the developer, don't silently fall back to a cloud API.
6. **Build vertically, not horizontally.** Get one full scenario (the P-102 investigation) working end-to-end through every layer before polishing any single layer. This matches `PRD.md` §10's own timeline.
7. **Test each agent as an independently callable unit** (NFR-MNT-1) before wiring it into the orchestrator — each has an explicit input/output contract in `API_Reference.md` §8.
8. **When in doubt about UI-facing shape, the contract in `API_Reference.md` wins.** Don't redesign response shapes; the frontend will be built against exactly what's documented there.

---

## 1. Required decisions BEFORE Phase 0 (ask the user — do not guess)

These are gaps or open questions left in the source docs. Do not proceed past Phase 0 until each is answered and recorded at the top of the repo's README.

| # | Question | Why it matters | Where it's ambiguous |
|---|---|---|---|
| 1 | Exact demo corpus files: do they exist yet, or must you (the builder) fabricate a synthetic 5–10 document corpus? If fabricating, what equipment IDs, dates, and numeric values should the P-102 scenario use? | The entire primary demo scenario's numbers (2.1→2.8→3.7 mm/s, 68→71→77°C, 3.0 mm/s threshold) must exist somewhere in real ingested documents — they can't be hardcoded in agent code. | `PRD.md` §5 lists required document *types* but not actual file contents; `SRS.md` §6.1 says "prepared in advance." |
| 2 | Final LLM choice and exact size/quantization (Qwen 2.5 7B vs 14B, GGUF quant level) | Directly affects latency budget (NFR-PERF-1/2) and whether the demo machine can run it | `PRD.md` §11 explicitly flags this as an open question pending hardware benchmarking |
| 3 | What hardware will actually run the demo (GPU model/VRAM, or CPU-only)? | Determines model size, batch settings, and whether Vision Agent (P1) is feasible live or must fall back to a pre-computed graph | `PRD.md` §9 Risks, `SRS.md` §2.4 |
| 4 | Embedding model name/dimension | Needed to size the Chroma/FAISS collection and confirm it runs under the chosen Ollama setup | `SRS.md` §8 says "a local embedding model compatible with the chosen runtime" — no name given |
| 5 | Vision/VLM: build live P1 feature, or ship the "pre-computed knowledge graph" fallback for the demo? | Changes whether Phase 6 is a real VLM integration or a static lookup table | `PRD.md` §11 lists this as explicitly open |
| 6 | Vector DB: Chroma or FAISS? | `SRS.md` §4.4 lists both as acceptable; API/workflow don't care which, but code must pick one | `SRS.md` §4.4, `workflow.md` §1 |
| 7 | Deployment target: bare-metal Python process, or containerized (Docker) for the demo machine? | NFR-PORT-1 says "containerized where practical" — practicality depends on the demo machine (see Q3) | `SRS.md` §5.6 |
| 8 | Exact port numbers, CORS origins, and whether HTTPS or plain HTTP is used for the prototype | `API_Reference.md` shows `http://localhost:8000` as prototype base URL but doesn't confirm this is final | `API_Reference.md` header |
| 9 | Who builds/owns the frontend, and is it built in parallel? | Determines whether you need a mock frontend/Postman collection to self-test streaming, or a real one exists | Not covered in any doc — `Design.md` only specifies UI, not who builds it or when |
| 10 | Session persistence: in-memory dict, SQLite table, or Redis for the prototype's lightweight sessions? | `API_Reference.md` §2 only shows the request/response shape, not storage | `API_Reference.md` §2, `SRS.md` §2.1 |
| 11 | Graph store scope: exactly which equipment relationships need to be pre-loaded for the demo (beyond T-101→P-102→V-204→R-101)? | `SRS.md` §4.4 calls for NetworkX "scoped to demo corpus" but doesn't enumerate the full graph | `SRS.md` §2.1, §4.4 |

**Do not fabricate answers to these and keep building.** Where a fabricated demo corpus is genuinely necessary (Q1), draft it, show it to the user for approval, and only then wire it into ingestion — because every number quoted in `API_Reference.md`'s example report must trace back to a real ingested source.

---

## 2. Tech stack (already locked by SRS §8 / §4.4 — do not re-litigate)

| Layer | Choice | Notes |
|---|---|---|
| Language/framework | Python 3.11+, FastAPI | async, needed for SSE |
| LLM serving | Ollama (local) | Qwen 2.5 family — exact size per Q2 above |
| Vector DB | ChromaDB or FAISS | pick one per Q6 |
| Relational DB | SQLite (prototype) | users/sessions, doc metadata, audit log |
| Object store | Local filesystem, addressable by `source_id` | raw files for Source Viewer |
| Graph store | NetworkX in-process | scoped equipment graph |
| PDF/text extraction | PyMuPDF (`fitz`) | preserves page metadata |
| Tabular analytics | pandas | deterministic, never LLM |
| Streaming | Server-Sent Events via FastAPI `StreamingResponse`/`EventSourceResponse` | per `API_Reference.md` §4 |

---

## 3. Repository layout

```
backend/
├── README.md                     # records answers to Section 1 decisions
├── pyproject.toml / requirements.txt
├── .env.example                  # OLLAMA_HOST, MODEL_NAME, DB paths, etc — no secrets committed
├── app/
│   ├── main.py                   # FastAPI app, route registration, CORS
│   ├── config.py                 # settings (pydantic BaseSettings), reads .env
│   ├── deps.py                   # shared FastAPI dependencies (session auth, db session)
│   ├── models/                   # pydantic request/response schemas (mirror API_Reference.md exactly)
│   │   ├── session.py
│   │   ├── ingestion.py
│   │   ├── investigation.py
│   │   ├── evidence.py
│   │   ├── report.py
│   │   └── audit.py
│   ├── db/
│   │   ├── sql_models.py         # SQLAlchemy models: sessions, documents, datasets, investigations, audit_log
│   │   ├── vector_store.py       # Chroma/FAISS wrapper: upsert_chunk, query
│   │   ├── object_store.py       # save_raw_file, get_raw_file(source_id)
│   │   └── graph_store.py        # NetworkX wrapper: equipment relationship graph
│   ├── ingestion/
│   │   ├── extract.py            # PyMuPDF text extraction, page/section metadata
│   │   ├── chunk.py               # overlapping chunker
│   │   ├── tag.py                  # metadata tagging (equipment_id, doc_type, date, dept_scope)
│   │   ├── embed.py                 # embedding generation via Ollama
│   │   └── tabular.py              # CSV/XLSX → structured store (FR-ING-7)
│   ├── agents/
│   │   ├── base.py                # common Agent interface / contract types
│   │   ├── planner.py             # FR-PLN-1..3
│   │   ├── document_agent.py      # FR-DOC-1..3
│   │   ├── data_agent.py          # FR-DAT-1..3 (pandas only, no LLM)
│   │   ├── vision_agent.py        # FR-VIS-1..3 (P1)
│   │   ├── rag_agent.py           # FR-RAG-1..2
│   │   ├── synthesis.py           # FR-SYN-1..3 (LLM call)
│   │   └── verification.py        # FR-VER-1..4
│   ├── orchestrator/
│   │   ├── investigation.py       # runs Workflow B end-to-end, emits SSE events
│   │   └── model_router.py        # API_Reference.md §9 — sole point of model dispatch
│   ├── routers/
│   │   ├── session.py             # POST /session
│   │   ├── knowledge_base.py      # /knowledge-base/*
│   │   ├── investigations.py      # /investigations/* incl. SSE stream, plan, report
│   │   ├── evidence.py            # /evidence/{source_id}
│   │   ├── export.py              # /investigations/{id}/export
│   │   └── audit.py               # /audit-log
│   └── services/
│       ├── audit_service.py       # Workflow D: two-write audit pattern
│       └── report_service.py      # assembles report from EvidenceBundle + verification result
├── corpus/                        # the demo documents (per Q1) — not committed if confidential
├── tests/
│   ├── unit/                      # one test module per agent, using the §8 contracts directly
│   ├── integration/                # full Workflow B run against the demo corpus
│   └── fixtures/                   # cached SSE transcripts for the 3 demo scenarios (NFR-REL-1)
└── scripts/
    ├── ingest_corpus.py            # one-off offline ingestion run (workflow.md §1 demo note)
    └── run_demo_scenarios.py       # pre-runs & caches the 3 demo scripts (PRD §9 risk mitigation)
```

---

## 4. Data model summary (build these before any agent code)

Build in this order — later layers depend on earlier ones.

1. **SQL schema** (`db/sql_models.py`): `sessions`, `documents` (metadata mirroring `GET /knowledge-base/documents/{id}`), `datasets`, `investigations` (status, query, session_id), `audit_log` (append-only — no update/delete methods exposed at all, not just at the API layer).
2. **Vector store schema**: chunk record = `{chunk_text, source_id, page, equipment_ids[], document_type, department_scope, embedding}`. Confirm collection dimension matches the embedding model from Q4.
3. **Object store**: files saved at a path keyed by `source_id`; `object_store.get_raw_file` must support returning a specific page render for PDFs (needed by `GET /evidence/{source_id}` and Source Viewer).
4. **Structured/tabular store**: one table per dataset ingestion, columns exactly `timestamp, equipment_id, metric, value, unit` (FR-ING-7).
5. **Graph store**: nodes = equipment IDs, edges = connections, at minimum covering the P-102 cluster (`T-101 → P-102 → V-204 → R-101`) per Q11.

**Definition of done for this section:** you can round-trip a fake document through ingestion → chunk → embed → store → retrieve, and a fake CSV through parse → store → query, with unit tests, before any agent touches them.

---

## 5. Phased build plan

### Phase 0 — Environment & Scaffolding
- Set up repo layout (§3), `.env.example`, `config.py`.
- Confirm Ollama is installed and the chosen models (Q2, Q4) are pulled and respond to a trivial prompt.
- Stand up empty FastAPI app with health check route.
- **DoD:** `uvicorn app.main:app` runs; `/docs` loads; Ollama round-trip test script passes.

### Phase 1 — Ingestion Pipeline (FR-ING-1..7, `API_Reference.md` §3, `workflow.md` §1)
- Implement `extract.py`, `chunk.py`, `tag.py`, `embed.py`, `tabular.py`.
- Implement `POST /knowledge-base/documents`, `GET /knowledge-base/documents/{id}`, `POST /knowledge-base/datasets`, `GET /knowledge-base/summary`.
- Run `scripts/ingest_corpus.py` against the approved demo corpus (Q1) once it exists.
- **DoD:** all documents in the demo corpus show `status: ready`; `GET /knowledge-base/summary` returns correct counts; every chunk has correct page + equipment_id tags (spot-check the P-102 vibration/temperature values are retrievable).

### Phase 2 — Session (FR-ACC-1..2, `API_Reference.md` §2)
- Implement `POST /session` and the storage mechanism decided in Q10.
- **DoD:** session_id issued and accepted as bearer/cookie on a protected route.

### Phase 3 — Planner Agent (FR-PLN-1..3)
- Implement `plan(query, corpus_summary) -> InvestigationPlan` exactly per `API_Reference.md` §8.1.
- Implement out-of-scope classification (`is_in_scope: bool`) — test explicitly against "What is the current price of crude oil?" (Workflow E).
- **DoD:** unit tests cover (a) P-102 query → 4 sub-tasks matching the example plan in `API_Reference.md` §4, (b) fire-emergency query → document/RAG-only sub-tasks, (c) out-of-scope query → `is_in_scope: false`.

### Phase 4 — Document Agent (FR-DOC-1..3)
- Implement `retrieve(sub_task_goal, filters) -> [{chunk_text, source_id, page, score}]` per §8.2.
- Implement named-value extraction (FR-DOC-2) — decide explicitly whether this is regex/rule-based or a small LLM call; if LLM, route it through the Model Router (Phase 13), never ad hoc.
- **DoD:** retrieving against the P-102 corpus returns the correct inspection report chunks with correct page numbers.

### Phase 5 — Data/Analytics Agent (FR-DAT-1..3)
- Implement `analyze(metric, equipment_id, dataset_id) -> {trend, pct_change, data_points, threshold_breach}` per §8.3, using pandas only.
- **DoD:** given the demo CSV, reproduces the exact trend the example report shows (2.1 → 2.8 → 3.7 mm/s, +76%, threshold_breach: true against 3.0 mm/s spec). No LLM call anywhere in this module — enforce with a lint rule or code review checklist, not just intention.

### Phase 6 — Vision/P&ID Agent (FR-VIS-1..3, P1)
- Branch on Q5: either integrate a local VLM via the Model Router, or build the pre-computed graph fallback reading from `graph_store.py`.
- Implement `analyze_pid(pid_source_id, equipment_id) -> {found, connections, confidence}` per §8.4.
- Implement graceful degradation (FR-VIS-3, `workflow.md` §7 row 1): low confidence or timeout → pipeline continues, report omits P&ID section.
- **DoD:** correctly returns `["T-101","V-204"]`-style connections for P-102; a deliberately-broken/unrecognized image returns `found: false` without crashing the pipeline.

### Phase 7 — RAG/Spec Agent (FR-RAG-1..2)
- Implement `retrieve_spec(query, equipment_id, filters) -> [{chunk_text, source_id, page, section}]` per §8.5.
- Implement the `department_scope` filter parameter end-to-end even though enforcement is simplified for the demo (FR-RAG-2) — the interface must exist, not just be a no-op comment.
- **DoD:** retrieves the correct threshold value/section (e.g. "§4.2, 3.0 mm/s") from the pump operating manual.

### Phase 8 — Synthesis (FR-SYN-1..3)
- Assemble the `EvidenceBundle` strictly from Phases 4–7 outputs — never pass raw documents.
- Implement `synthesize(evidence_bundle) -> DraftFindings`, each finding tagged with which evidence item(s) support it, via the Model Router.
- **DoD:** unit test asserts the function signature only accepts a structured `EvidenceBundle` object (not a raw string/document), enforcing FR-SYN-1 at the type level, not just by convention.

### Phase 9 — Verification Agent (FR-VER-1..4)
- Implement `verify(draft_findings, evidence_bundle) -> {findings, overall_confidence, overall_status}` per §8.7.
- Classify each finding Supported/Partially Supported/Unsupported; drop or flag unsupported ones (FR-VER-2).
- Implement the zero-supported-findings → `insufficient_evidence` branch (FR-VER-4, Workflow E's second entry point).
- **DoD:** feeding a deliberately weak/irrelevant evidence bundle produces `unverified`/low confidence or a full insufficient-evidence result, never a confident-sounding hallucination.

### Phase 10 — Orchestrator & SSE Streaming (`workflow.md` §2, `API_Reference.md` §4)
- Implement `POST /investigations` → kicks off Planner, returns `202` + `stream_url`.
- Implement `GET /investigations/{id}/stream` emitting `agent_update` events per the exact schema in `API_Reference.md` §4, then a terminal `investigation_complete` or `insufficient_evidence` event.
- Dispatch Document/Data/Vision/RAG sub-tasks in parallel where the plan allows (per the ASCII diagram in `workflow.md` §2).
- Implement `GET /investigations/{id}/plan`.
- Ensure the investigation continues server-side independent of the SSE connection (NFR-REL-2 / `workflow.md` §7 last row) — a dropped client connection must not kill the job.
- **DoD:** streaming a P-102 query produces events in the same order as the sequence diagram in `workflow.md` §2.1, and `GET /report` works even if you disconnect mid-stream and reconnect later.

### Phase 11 — Report & Evidence Retrieval (FR-RPT-1..4, `API_Reference.md` §5–6)
- Implement `GET /investigations/{id}/report` exactly matching the response shape in `API_Reference.md` §4 (including `pid_relationship`, `confidence`, `verification_status`).
- Implement `GET /evidence/{source_id}` for all three evidence types (document/dataset/pid_drawing).
- Implement `POST /investigations/{id}/export` (PDF) per Workflow C — reuse the report data, respect the no-blue-hyperlink note from `Design.md` if you own PDF styling, otherwise confirm with whoever owns the PDF template.
- **DoD:** every finding in a generated P-102 report has at least one evidence entry that resolves via `GET /evidence/{source_id}` to real, correct content (NFR-USE-2, SRS §9 item 3).

### Phase 12 — Audit Log (FR-AUD-1..2, `workflow.md` §4)
- Implement the two-write pattern: write on investigation creation (`status: started`), update on resolution — never a single write.
- Implement `GET /audit-log` with pagination; confirm no `DELETE`/`PATCH` route exists anywhere for this resource.
- **DoD:** a failed/timed-out investigation still produces a complete, correct audit entry.

### Phase 13 — Model Router (`API_Reference.md` §9, NFR-MNT-2)
- Implement `route(task_type) -> ModelEndpoint`, the single chokepoint all agents call through — no agent may import an Ollama client directly.
- **DoD:** grep the codebase — the only file that references the Ollama endpoint/host directly is the router. Swapping the configured model name requires touching only `config.py`/the router, never agent code.

### Phase 14 — Failure/Degradation Behavior (`workflow.md` §7, NFR-REL-2)
- Explicitly implement each row of the `workflow.md` §7 table as a tested code path, not an afterthought: Vision Agent timeout, Data Agent no-rows, all-findings-unsupported, SSE disconnect.
- **DoD:** each of the four failure rows has a corresponding integration test that asserts the specified graceful behavior.

### Phase 15 — Testing & Acceptance Criteria (`SRS.md` §9)
Map tests directly to the five acceptance bullets:
1. All P0 features functional end-to-end for the P-102 scenario.
2. Out-of-scope query → insufficient evidence, verified by test.
3. Every finding has ≥1 correct, resolvable citation.
4. Investigation timeline test asserts multiple distinct agents contributed (not one LLM call doing everything).
5. A network-monitoring test/assertion (e.g. mock/blackhole all non-local hosts during a test run) proves zero external calls occur.

### Phase 16 — Demo Rehearsal Artifacts (`PRD.md` §9 Risks, `workflow.md` §6)
- Build `scripts/run_demo_scenarios.py` to pre-run and cache the exact 3 demo scenarios from `workflow.md` §6 as fixtures, so a live failure can fall back to cached/replayed responses.
- **DoD:** all 3 scenarios reproduce consistent output across repeated runs (NFR-REL-1), timed to confirm NFR-PERF-1 (<45s) and NFR-PERF-2 (<10s for the RAG-only case).

---

## 6. Appendix A — Full endpoint checklist (tick off against `API_Reference.md`)

- [ ] `POST /session`
- [ ] `POST /knowledge-base/documents`
- [ ] `GET /knowledge-base/documents/{document_id}`
- [ ] `POST /knowledge-base/datasets`
- [ ] `GET /knowledge-base/summary`
- [ ] `POST /investigations`
- [ ] `GET /investigations/{id}/stream` (SSE)
- [ ] `GET /investigations/{id}/report`
- [ ] `GET /investigations/{id}/plan`
- [ ] `GET /evidence/{source_id}`
- [ ] `POST /investigations/{id}/export`
- [ ] `GET /audit-log?limit&offset`

## 7. Appendix B — Explicit non-goals (do NOT build these; flag if asked)
Per `PRD.md` §3.2: production SSO/RBAC/LDAP, full plant-wide ingestion, real-time IoT/SCADA, mobile/WhatsApp/voice interfaces, multi-tenant/cloud/horizontal scaling, a general plant-wide knowledge graph, and any model fine-tuning/training.

## 8. Appendix C — When to stop and ask the user
Stop and ask, rather than proceeding on a best guess, whenever you hit:
- A concrete value not present in any doc (a filename, a numeric threshold, a model name/size, a port).
- A conflict between two docs (e.g. Design.md implying a feature API_Reference.md doesn't expose).
- A choice explicitly marked open in `PRD.md` §11 or listed in Section 1 of this plan.
- Any point where satisfying a requirement would require touching something listed in Appendix B.
