# SRS.md — Software Requirements Specification
## VIGIL — Sovereign Industrial Agentic AI Workbench
Conforms loosely to IEEE 830 structure. **Version:** 1.0 · **Reference:** SIH26117 (MRPL)

---

## 1. Introduction

### 1.1 Purpose
This document specifies the functional and non-functional requirements for VIGIL, an on-premise multi-agent AI system that answers complex industrial questions using an organization's private documents, drawings, and operational data, producing evidence-backed and verified answers.

### 1.2 Scope
VIGIL ingests heterogeneous industrial knowledge (PDFs, scanned documents, P&ID drawings/images, tabular time-series data), orchestrates specialized AI agents to investigate a natural-language query, and returns a structured, cited, confidence-scored report. All inference runs on locally hosted open-weight models; no confidential data is transmitted to third-party APIs. This SRS covers the internal-round prototype scope defined in `PRD.md` §3 and §6.

### 1.3 Definitions, Acronyms, Abbreviations
| Term | Meaning |
|---|---|
| Agent | An LLM-driven or deterministic software component with a narrow responsibility (e.g., Document Agent) |
| Planner | The agent that decomposes a user query into an investigation plan |
| RAG | Retrieval-Augmented Generation |
| P&ID | Piping and Instrumentation Diagram |
| VLM | Vision-Language Model |
| Verification Agent | Agent that checks a draft conclusion against gathered evidence before it is shown to the user |
| Sovereign / on-premise | Runs entirely within the organization's network; no external inference API calls |
| Confidence score | A 0–100 score attached to a finding, reflecting evidential support |

### 1.4 References
- `PRD.md` — Product Requirements Document
- `Design.md` — UI/UX Design Specification
- `API_Reference.md` — API contract
- `workflow.md` — End-to-end process flows
- SIH26117 problem statement (MRPL)

### 1.5 Overview
Section 2 describes the system in context. Section 3 lists functional requirements by module. Section 4 covers external interfaces. Section 5 covers non-functional requirements. Section 6 covers data requirements. Section 7 covers system models. Section 8 covers constraints and technology choices.

---

## 2. Overall Description

### 2.1 Product Perspective
VIGIL is a new, standalone, on-premise web application. It is composed of:
- A **web frontend** (investigation UI).
- A **backend API** (FastAPI) exposing REST endpoints and a streaming channel for agent progress.
- An **Agent Orchestration layer** (Planner + specialist agents + Verification Agent).
- A **Local AI layer** (LLM, VLM, embedding model, all served via Ollama or an equivalent local runtime).
- A **Data layer**: vector database (document chunks), relational store (metadata, users, audit log), object store (raw documents/images), lightweight graph store (equipment relationships, scoped to demo corpus).

```
Browser (UI)
     │  HTTPS / SSE
     ▼
Backend API (FastAPI)
     │
     ▼
Agent Orchestrator (Planner → specialist agents → Verifier)
     │
     ├── Local AI Layer (Ollama: LLM, VLM, embeddings)
     └── Data Layer (Vector DB, SQL DB, Object Store, Graph Store)
```

### 2.2 Product Functions (Summary)
1. Ingest a curated document/drawing/data corpus into searchable, metadata-tagged form.
2. Accept a natural-language investigation query from a user.
3. Plan and execute a multi-agent investigation over the corpus.
4. Produce a structured, evidence-cited, confidence-scored, verified answer.
5. Log every step of the investigation for audit purposes.
6. Allow export of the final answer as a report.

### 2.3 User Classes and Characteristics
| Class | Description | Technical skill |
|---|---|---|
| Engineer/Operator (standard user) | Asks investigation questions, reads reports | Low–medium |
| Demo Admin (internal round) | Uploads/manages the corpus for the demo | Medium |

(Full RBAC with department-level knowledge isolation is a documented **future** user class — see `PRD.md` §3.2.)

### 2.4 Operating Environment
- Runs on a single on-premise server or high-spec laptop/workstation with a GPU (demo hardware).
- Backend: Python 3.11+, FastAPI.
- Frontend: modern evergreen browser (Chrome/Edge/Firefox), desktop-first, responsive down to tablet width.
- Local model runtime: Ollama (or compatible local inference server).
- No internet dependency required at runtime for the core investigation flow.

### 2.5 Design and Implementation Constraints
- All inference on confidential content must occur via the local model runtime — enforced at the architecture level (Model Router only ever targets local endpoints).
- Demo must run on modest hardware: model sizes are chosen for latency, not maximum accuracy (see §8).
- Time-boxed development (≈2 days for internal round) constrains scope to the P0/P1 features in `PRD.md` §6.

### 2.6 Assumptions and Dependencies
- The demo document corpus is prepared in advance and is clean enough not to require a production-grade OCR pipeline.
- Ollama (or equivalent) and the chosen models are pre-downloaded and available offline on demo hardware.
- Users trust the system enough to act on "insufficient evidence" responses rather than expecting an answer regardless.

---

## 3. Functional Requirements

Each requirement has an ID of the form `FR-<Module>-<n>` for traceability into `API_Reference.md` and `workflow.md`.

### 3.1 Document Ingestion Module
- **FR-ING-1**: The system shall accept PDF, DOCX, TXT, CSV/XLSX, and common image formats (PNG/JPG) as source documents.
- **FR-ING-2**: The system shall extract text content from PDFs/DOCX, preserving page number and section metadata.
- **FR-ING-3**: The system shall chunk extracted text into overlapping passages sized for the embedding model's context window.
- **FR-ING-4**: The system shall tag each chunk with metadata: source document name, page number, equipment ID(s) mentioned (if detectable), document date, and document type (SOP, inspection report, manual, etc.).
- **FR-ING-5**: The system shall generate vector embeddings for each chunk and store them in the vector database.
- **FR-ING-6**: The system shall store raw source files in an object store, addressable by ID, so the UI can display/open the original page.
- **FR-ING-7**: The system shall parse tabular time-series files (CSV/XLSX) into a queryable structured store, preserving column semantics (e.g., timestamp, equipment ID, measurement type, value, unit).

### 3.2 Planner Agent
- **FR-PLN-1**: On receiving a user query, the Planner shall produce a structured investigation plan identifying which specialist agents are required (Document, Vision, Data) and what each must retrieve.
- **FR-PLN-2**: The Planner shall be able to classify a query as out-of-scope (unanswerable from the corpus) and short-circuit to an "insufficient evidence" response without invoking unnecessary agents.
- **FR-PLN-3**: The Planner's plan shall be visible to the user as an "investigation timeline" (see `Design.md`).

### 3.3 Document Intelligence Agent
- **FR-DOC-1**: Given a sub-task from the Planner, the Document Agent shall query the vector database and return the top-k most relevant chunks with metadata.
- **FR-DOC-2**: The Document Agent shall extract specific named values (e.g., "vibration: 3.7 mm/s") from retrieved chunks when the sub-task requests a specific field.
- **FR-DOC-3**: Every value or statement the Document Agent returns shall carry a traceable source reference (document, page).

### 3.4 Data/Analytics Agent
- **FR-DAT-1**: Given a metric and equipment ID, the Data Agent shall retrieve the relevant time-series records from the structured store.
- **FR-DAT-2**: The Data Agent shall compute deterministic statistics (trend direction, percentage change, min/max, threshold comparison) using code, not LLM-generated arithmetic.
- **FR-DAT-3**: The Data Agent shall return both the computed result and the underlying data points used, for citation.

### 3.5 Vision/P&ID Agent (P1)
- **FR-VIS-1**: Given a P&ID image and an equipment ID, the Vision Agent shall attempt to locate the equipment and its directly connected components.
- **FR-VIS-2**: The Vision Agent shall return a simple connectivity list (e.g., "feeds into," "connects to") for the identified equipment, suitable for rendering as a small relationship diagram.
- **FR-VIS-3**: If the Vision Agent cannot confidently identify the equipment, it shall report this rather than guessing, and the pipeline shall continue without P&ID evidence.

### 3.6 Knowledge/RAG Agent
- **FR-RAG-1**: The RAG Agent shall retrieve specification/threshold values relevant to a sub-task (e.g., "normal operating vibration range for this pump model") from the document corpus.
- **FR-RAG-2**: Retrieval shall be restricted to documents the requesting user's role is permitted to access (permission-aware retrieval; demo may implement this as a stubbed/simplified check per `PRD.md` non-goals, but the interface shall be designed for it — see `API_Reference.md`).

### 3.7 Synthesis (LLM Reasoning)
- **FR-SYN-1**: The system shall combine the structured outputs of the Document, Data, Vision, and RAG agents into a single evidence bundle and pass only this bundle (not raw documents) to the LLM for synthesis.
- **FR-SYN-2**: The LLM shall produce a draft finding set: each finding shall reference which evidence item(s) support it.
- **FR-SYN-3**: The LLM shall not be asked to perform numeric calculations that the Data Agent is responsible for (FR-DAT-2 supersedes LLM arithmetic).

### 3.8 Verification Agent
- **FR-VER-1**: The Verification Agent shall check each draft finding against the evidence bundle and classify it as Supported, Partially Supported, or Unsupported.
- **FR-VER-2**: Unsupported findings shall be removed or rewritten as explicitly uncertain before being shown to the user.
- **FR-VER-3**: The Verification Agent shall assign a confidence score (0–100) to the overall answer.
- **FR-VER-4**: If no findings are Supported, the system shall return an "insufficient evidence" response instead of a normal report (see `Design.md` for the required UI treatment).

### 3.9 Investigation Report / UI Delivery
- **FR-RPT-1**: The system shall render the final answer as a structured report: overall assessment, key findings (each with evidence references), P&ID relationship view (if available), conclusion, confidence score, verification status, and a recommended next step.
- **FR-RPT-2**: The system shall render a step-by-step investigation timeline showing what each agent did and when.
- **FR-RPT-3**: The system shall allow the user to click an evidence reference and view the underlying source (document page, data table, or diagram excerpt).
- **FR-RPT-4**: The system shall allow exporting the final report as a PDF.

### 3.10 Audit Log
- **FR-AUD-1**: The system shall log, for every query: requesting user, timestamp, query text, documents/data accessed, agents invoked, and final answer.
- **FR-AUD-2**: Audit log entries shall be immutable from the application UI (append-only).

### 3.11 Access / Session (P2 — minimal for demo)
- **FR-ACC-1**: The system shall capture a user's name and department at session start.
- **FR-ACC-2**: The system's retrieval interfaces shall accept a department/role parameter so permission-aware retrieval (FR-RAG-2) can be demonstrated conceptually, even if enforcement is simplified for the demo.

---

## 4. External Interface Requirements

### 4.1 User Interfaces
See `Design.md` for full specification. Summary: a session-entry screen, an investigation workspace (query input + live agent timeline), and a report view with evidence drill-down.

### 4.2 API Interfaces
See `API_Reference.md` for the full REST/SSE contract (ingestion, query, investigation status streaming, evidence retrieval, report export, audit log).

### 4.3 Hardware Interfaces
None beyond standard compute (CPU/GPU) and storage on the demo/deployment machine.

### 4.4 Software Interfaces
- **Ollama** (or compatible): local model serving for LLM, VLM, embedding model.
- **Vector database**: ChromaDB or FAISS.
- **Relational database**: SQLite (demo) / PostgreSQL (production path) for users, sessions, audit log, document metadata.
- **Graph store**: lightweight in-process graph (e.g., NetworkX) for the demo equipment cluster; Neo4j documented as the production path.
- **PDF/text extraction**: PyMuPDF.
- **Data analytics**: pandas.

---

## 5. Non-Functional Requirements

### 5.1 Performance
- **NFR-PERF-1**: The primary demo investigation scenario shall complete end-to-end in under 45 seconds on demo hardware.
- **NFR-PERF-2**: A simple SOP/RAG-only query shall return in under 10 seconds.
- **NFR-PERF-3**: The UI shall stream intermediate agent progress (not a blank loading screen) for any query taking longer than 3 seconds.

### 5.2 Reliability
- **NFR-REL-1**: The 3 prepared demo scenarios shall produce consistent, reproducible results across repeated runs.
- **NFR-REL-2**: If any specialist agent fails or times out, the pipeline shall degrade gracefully (proceed with available evidence and note the gap) rather than crash.

### 5.3 Security & Sovereignty
- **NFR-SEC-1**: No confidential document content or query text shall be transmitted to any external (non-local) API during normal operation.
- **NFR-SEC-2**: All inter-component communication shall occur within the local network/host.
- **NFR-SEC-3**: The system architecture shall support future integration of role-based access control and encryption-at-rest without redesign (interfaces designed accordingly).

### 5.4 Usability
- **NFR-USE-1**: A first-time user shall be able to run a successful investigation within 2 minutes of landing on the app, using a suggested question, without training.
- **NFR-USE-2**: Every generated claim visible to the user shall have a visibly reachable source citation — no unattributed assertions in a final report.

### 5.5 Maintainability
- **NFR-MNT-1**: Each agent shall be an independently testable module with a defined input/output contract (see `API_Reference.md` internal agent contracts).
- **NFR-MNT-2**: The Model Router abstraction shall allow swapping the underlying local model (e.g., Qwen 2.5 → another open-weight model) without changing agent logic.

### 5.6 Portability
- **NFR-PORT-1**: The system shall be deployable via a documented local setup (containerized where practical) without cloud-specific dependencies.

---

## 6. Data Requirements

### 6.1 Demo Corpus (minimum viable)
- 5–10 documents: inspection reports (3+, time-sequenced for one equipment ID), a maintenance history doc, an operating/equipment manual with a threshold spec, 2–3 SOP/safety documents.
- 1 tabular dataset: time-series operational readings (e.g., vibration, temperature) for the demo equipment, with timestamp, equipment ID, metric, value, unit.
- 1–2 P&ID images: showing the demo equipment and its immediate connections.

### 6.2 Data Retention (demo scope)
- All data stored locally for the duration of the demo/deployment; no requirement for retention policy enforcement in this round (documented as future work).

---

## 7. System Models

### 7.1 Use Case Summary
- UC-1: Run an equipment health investigation (primary).
- UC-2: Ask a safety/procedural question (secondary, RAG-only path).
- UC-3: Ask an out-of-scope question and receive an "insufficient evidence" response.
- UC-4: Review the audit log of a past investigation (secondary/demo-only).

### 7.2 High-Level Data Flow
See `workflow.md` for full sequence and state diagrams covering ingestion, investigation, and verification flows.

---

## 8. Technology and Model Constraints

| Layer | Choice for prototype | Rationale |
|---|---|---|
| LLM (reasoning/synthesis) | Qwen 2.5 (7B–14B, quantized as needed for demo hardware) | Strong instruction-following, runs locally via Ollama, sufficient for structured synthesis over pre-retrieved evidence |
| Embeddings | A local embedding model compatible with the chosen runtime | Needed for vector retrieval |
| Vision/VLM (P1) | A local vision-language model, or a scoped/pre-processed fallback if hardware-constrained | P&ID understanding is high-value but hardware-sensitive; degrade gracefully |
| Vector DB | ChromaDB (or FAISS) | Lightweight, embeddable, no external service required |
| Backend | Python 3.11+, FastAPI | Async support for streaming agent progress |
| Frontend | React (or Next.js) | Component-driven UI matching `Design.md` |
| PDF/Text extraction | PyMuPDF | Reliable local extraction with page metadata |
| Tabular analytics | pandas | Deterministic trend computation |

**Explicit constraint (per FR-SYN-3 and the sovereignty requirement):** the LLM is used for language understanding, synthesis, and explanation — never for deterministic calculation, and never given raw, unretrieved documents to search over itself.

---

## 9. Acceptance Criteria (Internal Round)

The prototype is considered acceptance-ready when:
1. All P0 features in `PRD.md` §6 are functional end-to-end for the primary demo scenario.
2. The out-of-scope question correctly returns "insufficient evidence."
3. Every finding in a report has at least one visible, correct citation.
4. The investigation timeline visibly shows multiple agents contributing (not a single LLM call).
5. No network call to an external inference API occurs during a demo run (verifiable via network monitoring).
