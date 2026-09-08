# workflow.md — End-to-End Workflows
## KavachAI — Sovereign Industrial Agentic AI Workbench

This document describes the runtime workflows that implement the requirements in `SRS.md` and are exposed via `API_Reference.md`, rendered per `Design.md`.

---

## 1. Workflow A — Document/Corpus Ingestion

```
 Admin uploads file
        │
        ▼
 File type detection ──► PDF/DOCX/TXT ──► Text extraction (PyMuPDF)
        │                                        │
        │                                        ▼
        │                              Preserve page/section metadata
        │                                        │
        │                                        ▼
        │                                 Chunk text (overlapping)
        │                                        │
        │                                        ▼
        │                          Tag chunk: doc name, page, equipment_id,
        │                          doc type, date, dept scope
        │                                        │
        │                                        ▼
        │                             Generate embeddings (local model)
        │                                        │
        │                                        ▼
        │                              Store in Vector DB (Chroma/FAISS)
        │
        ├──► CSV/XLSX ──► Parse to structured schema (timestamp, equipment_id,
        │                  metric, value, unit) ──► Store in structured store
        │
        └──► PNG/JPG/PID ──► Store raw in object store ──► (optional) pre-process
                              for Vision Agent (crop/label demo equipment region)

 Raw file always retained in object store, addressable by source_id,
 so the Source Viewer (Design.md §5.6) can render the original.
```

**Maps to:** FR-ING-1..7, `API_Reference.md` §3.
**Demo note:** for the internal round, this pipeline is run once, offline, against the prepared corpus — it does not need to be demonstrated live unless time permits.

---

## 2. Workflow B — Investigation Query (Primary Flow)

This is the core product workflow and the one that must be demo-perfect.

```
 User enters query in Investigation Workspace
        │
        ▼
 POST /investigations  ──►  Planner Agent
        │                        │
        │                        ▼
        │             Is the query in scope of the corpus?
        │                        │
        │              ┌─────────┴─────────┐
        │              │                   │
        │             NO                  YES
        │              │                   │
        │              ▼                   ▼
        │   emit "insufficient_evidence"   Decompose into sub-tasks:
        │   (skip remaining pipeline)        - document sub-task(s)
        │              │                     - data sub-task(s)
        │              │                     - vision sub-task(s) (if drawing relevant)
        │              │                     - rag/spec sub-task(s)
        │              ▼                   │
        │         END (UI shows            ▼
        │         Screen 4b)      Dispatch sub-tasks in parallel where possible
        │                                    │
        │              ┌─────────────────────┼─────────────────────┐
        │              ▼                     ▼                     ▼
        │      Document Agent           Data Agent            Vision Agent
        │      vector search over       load dataset,         locate equipment
        │      relevant chunk           pandas trend calc     + connections in
        │      metadata filter          (deterministic,       P&ID (if available)
        │      (dept scope, equip_id)   NOT LLM arithmetic)         │
        │              │                     │                     │
        │              └──────────┬──────────┴──────────┬──────────┘
        │                         ▼                      ▼
        │                   RAG/Spec Agent      each agent streams an
        │                   retrieve threshold/  `agent_update` SSE event
        │                   spec passages         to the client as it
        │                         │                completes (Design.md §5.3)
        │                         ▼
        │              Assemble EvidenceBundle
        │              { document_findings, data_findings,
        │                vision_findings, spec_findings }
        │                         │
        │                         ▼
        │              LLM Synthesis (local model via Model Router)
        │              input: EvidenceBundle only (never raw docs)
        │              output: DraftFindings, each finding tagged
        │                       with which evidence item(s) support it
        │                         │
        │                         ▼
        │              Verification Agent
        │              for each draft finding:
        │                check finding claim against cited evidence
        │                classify: supported | partially_supported | unsupported
        │              compute overall_confidence, overall_status
        │                         │
        │              ┌──────────┴──────────┐
        │              │                     │
        │      at least one finding    zero findings
        │      is "supported"          are "supported"
        │              │                     │
        │              ▼                     ▼
        │      Build final Report     emit "insufficient_evidence"
        │      (unsupported findings  (do not show a normal report
        │       dropped or flagged)    with unverified claims)
        │              │                     │
        └──────────────┴─────────┬───────────┘
                                  ▼
                    emit "investigation_complete"
                                  │
                                  ▼
                    GET /investigations/{id}/report
                                  │
                                  ▼
                    Render Investigation Report (Design.md §5.4)
                    User may click any citation → Source Viewer (§5.6)
                    User may click Export → Workflow C
```

**Maps to:** FR-PLN-1..3, FR-DOC-1..3, FR-DAT-1..3, FR-VIS-1..3, FR-RAG-1..2, FR-SYN-1..3, FR-VER-1..4, FR-RPT-1..3.

### 2.1 Sequence Diagram (compressed)
```
User        UI          Backend       Planner   DocAgent  DataAgent  VisionAgent  RAGAgent   LLM      Verifier
 │           │              │            │          │          │           │          │        │          │
 │ ask query │              │            │          │          │           │          │        │          │
 │──────────►│  POST /investigations     │          │          │           │          │        │          │
 │           │─────────────►│───────────►│          │          │           │          │        │          │
 │           │              │            │ plan     │          │           │          │        │          │
 │           │◄── SSE stream opens ──────│          │          │           │          │        │          │
 │           │              │            │─────────►│          │           │          │        │          │
 │           │              │            │          │ chunks   │           │          │        │          │
 │           │◄── agent_update: document_agent complete ───────│           │          │        │          │
 │           │              │            │────────────────────►│           │          │        │          │
 │           │              │            │                     │ trend     │          │        │          │
 │           │◄── agent_update: data_agent complete ────────────────────────│          │        │          │
 │           │              │            │────────────────────────────────►│          │        │          │
 │           │              │            │                                 │ P&ID     │        │          │
 │           │◄── agent_update: vision_agent complete ────────────────────────────────│         │          │
 │           │              │            │─────────────────────────────────────────► │         │          │
 │           │              │            │                                            │ spec    │          │
 │           │◄── agent_update: rag_agent complete ───────────────────────────────────────────── │          │
 │           │              │            │───────────────────────────────────────────────────────► synth   │
 │           │              │            │                                                        │        │
 │           │              │            │────────────────────────────────────────────────────────────────► verify
 │           │◄── investigation_complete ────────────────────────────────────────────────────────────────────│
 │           │  GET /report │            │                                                                   │
 │◄──────────│◄─────────────│            │                                                                   │
```

---

## 3. Workflow C — Report Export

```
 User clicks "Export Report"
        │
        ▼
 POST /investigations/{id}/export {format: "pdf"}
        │
        ▼
 Render report data (API §4 GET .../report) into the PDF template
 (Design.md palette — no default blue hyperlink styling)
        │
        ▼
 Store generated PDF, return download_url
        │
        ▼
 UI triggers download
```
**Maps to:** FR-RPT-4.

---

## 4. Workflow D — Audit Logging (cross-cutting)

Every investigation writes an audit entry at two points, not one — so partial/failed investigations are still auditable:

```
 Investigation created ──► write audit entry (status: started, query, user, dept)
        │
        ▼
 [Workflow B executes]
        │
        ▼
 Investigation resolved (complete OR insufficient_evidence OR failed)
        │
        ▼
 update audit entry: agents_invoked, verification_status, confidence, timestamp
        │
        ▼
 Entry becomes immutable (append-only per FR-AUD-2)
```
**Maps to:** FR-AUD-1..2, `API_Reference.md` §7.

---

## 5. Workflow E — Out-of-Scope / Insufficient Evidence Handling

This workflow is deliberately called out on its own because it is a core trust feature for the demo (see `PRD.md` §5, secondary scenario).

```
 Query received: "What is the current price of crude oil?"
        │
        ▼
 Planner classifies against corpus_summary
        │
        ▼
 No document/dataset/drawing in corpus is relevant to this query
        │
        ▼
 is_in_scope = false
        │
        ▼
 Skip Document/Data/Vision/RAG/Synthesis entirely (no wasted LLM calls)
        │
        ▼
 emit "insufficient_evidence" immediately
        │
        ▼
 UI renders Screen 4b (Design.md §5.5) — orange "insufficient evidence"
 card, NOT a red error, NOT a hallucinated guess
```
This same terminal state is also reachable **later** in Workflow B (§2) if the Verification Agent finds zero supported findings even after the full pipeline ran — e.g., the query was plausible-sounding but the retrieved evidence didn't actually support any conclusion.

---

## 6. Demo Script Mapping (for rehearsal)

| Demo question | Workflow exercised | Expected terminal screen |
|---|---|---|
| "What should an employee do during a fire emergency?" | Workflow B, RAG-only path (no data/vision sub-tasks planned) | Investigation Report, single-source citation, high confidence |
| "Investigate Pump P-102 and determine whether its condition has deteriorated." | Workflow B, full multi-agent path | Investigation Report, multi-source citations, P&ID relationship, 91% confidence, Verified |
| "What is the current price of crude oil?" | Workflow E | Insufficient Evidence card |

Rehearse all three back-to-back so judges see: (1) simple grounded answer, (2) full agentic investigation with evidence, (3) correct refusal — in that order, telling the "we don't hallucinate" story last for maximum impact.

---

## 7. Failure/Degradation Behavior (NFR-REL-2)

| Failure | Behavior |
|---|---|
| Vision Agent times out or low confidence (FR-VIS-3) | Pipeline continues without P&ID evidence; report omits the P&ID relationship section rather than showing a wrong one |
| Data Agent finds no dataset rows for the equipment | Data-related sub-finding is dropped; other findings (document/RAG) may still support a (lower-confidence) conclusion |
| Verification Agent marks all findings unsupported | Terminal state = insufficient_evidence (Workflow E), even though agents "ran" |
| SSE connection drops mid-investigation | Client can `GET /investigations/{id}/report` directly once complete — investigation continues server-side independent of the stream connection |
