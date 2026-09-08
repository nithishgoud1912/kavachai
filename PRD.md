# PRD.md — Product Requirements Document
## KavachAI — Sovereign Industrial Agentic AI Workbench
**Problem Statement Reference:** SIH26117 · Mangalore Refinery and Petrochemicals Limited (MRPL)
**Document Owner:** Team
**Version:** 1.0
**Status:** Draft for Internal Round

---

## 1. Executive Summary

KavachAI is an on-premise, agentic AI platform that lets refinery engineers ask complex, open-ended questions about plant equipment, safety procedures, and operational history — in natural language — and receive **evidence-backed, verified answers** assembled by a team of specialized AI agents working over the organization's own confidential documents, drawings, and data.

KavachAI is explicitly **not** "a local chatbot over PDFs." The product is the orchestration layer: a Planner that decomposes a question into an investigation, specialist agents that gather evidence from text, images/P&IDs, and structured data, and a Verification Agent that refuses to let a claim stand without evidence. Every model runs inside the corporate network via a local inference layer (Ollama-served open-weight models); nothing confidential leaves the plant.

---

## 2. Problem Statement

Refinery engineers routinely need to answer questions like *"Has Pump P-102's condition deteriorated?"* or *"What is the fire emergency procedure for Zone A?"* The answer is scattered across inspection reports, maintenance logs, P&ID drawings, SOPs, and spreadsheets. Today this means manually opening dozens of documents, cross-referencing drawings, and mentally reconciling numbers — a process that takes hours and is error-prone, and cannot use public cloud AI tools because the data is confidential.

### 2.1 Who feels this pain
- **Process/Reliability Engineers** — investigating equipment health trends.
- **Operations staff** — needing fast, correct answers to safety/procedural questions.
- **HSE (Health, Safety, Environment) officers** — needing traceable, auditable answers, not confident-sounding guesses.
- **Plant management** — needing an audit trail of what was asked, what data was used, and what was concluded.

### 2.2 Why existing tools fail
| Tool | Gap |
|---|---|
| Manual document search | Slow, inconsistent, tribal-knowledge dependent |
| Public LLM chatbots (ChatGPT, Gemini) | Cannot be used — confidential industrial data cannot leave the org |
| Generic local RAG chatbot (Ollama + PDFs) | Answers text questions only; cannot read P&IDs, cannot do numeric trend analysis, cannot verify its own claims, no audit trail, no access control |

---

## 3. Goals and Non-Goals

### 3.1 Goals (this submission)
1. Demonstrate an **agentic investigation workflow** — not a single-shot Q&A — for at least one realistic industrial scenario (equipment health investigation).
2. Demonstrate **multimodal evidence gathering**: text documents, a P&ID/drawing, and tabular/time-series data feeding one answer.
3. Demonstrate **evidence-first, verifiable answers**: every material claim is traceable to a source (document + page, dataset + range, drawing + component).
4. Demonstrate a **Verification Agent** that can downgrade or reject an unsupported conclusion, and that the system can say "insufficient evidence" rather than hallucinate.
5. Demonstrate that the **entire pipeline runs locally** (no external API calls for inference on confidential data).
6. Ship a working, demo-reliable UI covering: ask a question → watch the agents investigate → read an evidence-backed report → export it.

### 3.2 Non-Goals (explicitly out of scope for this round)
- Production-grade authentication/SSO, enterprise RBAC integration (LDAP/AD).
- Full plant-wide document ingestion (thousands of files) — a curated 10–20 document corpus is sufficient.
- Real-time IoT/SCADA integration.
- Mobile app, WhatsApp/email integration, voice interface.
- Multi-tenant deployment, cloud hosting, horizontal scaling.
- A fully general-purpose knowledge graph covering the whole plant — a scoped graph for the demo equipment cluster is sufficient.
- Fine-tuning or training custom models — only prompting/orchestrating existing open-weight models.

These are documented as **Future Scope / Production Roadmap** and presented as such to judges, not built.

---

## 4. Target Users / Personas

| Persona | Role | Primary Need | Success looks like |
|---|---|---|---|
| **Arjun** | Process/Reliability Engineer | Diagnose equipment condition quickly | Gets a trend-backed, cited verdict in under a minute instead of an hour of manual digging |
| **Priya** | HSE Officer | Answer safety/procedural questions correctly | Gets the exact SOP clause, never a guessed answer |
| **Rahul** | Shift Operator | Quick procedural lookups on the floor | Simple chat, no jargon, fast |
| **Deepak** | Plant Manager / Judge persona | Trust and oversight | Can see *why* the AI concluded what it did, and that nothing left the network |

---

## 5. Core Use Case (Primary Demo Scenario)

**"Investigate Pump P-102 and determine whether its condition has deteriorated."**

Inputs available to the system:
- 3 inspection reports (Jan / Apr / Jul) — PDF
- 1 maintenance history document — PDF
- 1 operating/vibration dataset — CSV/XLSX
- 1 P&ID drawing showing P-102 and connected equipment — image/PDF
- 1 pump operating manual with threshold specifications — PDF

Expected system behavior (see `workflow.md` for the full sequence):
1. Planner Agent decomposes the question into sub-tasks.
2. Document Agent retrieves and extracts relevant passages/values.
3. Data Agent computes the vibration/temperature trend deterministically (not via LLM arithmetic).
4. Vision Agent identifies P-102 and its connections on the P&ID.
5. Knowledge/RAG Agent retrieves the relevant specification/threshold.
6. LLM synthesizes a draft conclusion from the structured evidence.
7. Verification Agent checks the draft against the evidence and either confirms, downgrades, or rejects it.
8. UI renders a structured, cited investigation report; exportable as PDF.

**Secondary demo scenarios** (for breadth, using the same architecture):
- A pure safety/SOP question ("What should an employee do during a fire emergency?") — exercises the Document + RAG path only, with a source citation.
- An out-of-scope question ("What is the current price of crude oil?") — must trigger "insufficient evidence," proving the system does not hallucinate.

---

## 6. Feature List and Priority

| Priority | Feature | Description |
|---|---|---|
| P0 | Chat/Investigation interface | Natural-language question input, streamed agent progress, final report |
| P0 | Document Intelligence Agent | PDF/text ingestion, chunking, metadata-preserving extraction |
| P0 | Knowledge/RAG retrieval | Vector search over the document corpus, source-cited retrieval |
| P0 | Data/Analytics Agent | Deterministic trend calculation from CSV/XLSX time-series |
| P0 | Verification Agent | Evidence-conclusion consistency check, confidence scoring, "insufficient evidence" fallback |
| P0 | Evidence-cited report UI | Findings, evidence list, confidence, verification status |
| P1 | Vision/P&ID Agent | Identify equipment and connections in a P&ID image |
| P1 | Investigation timeline / audit log | Step-by-step trace of what the agents did |
| P1 | Report export (PDF) | Downloadable investigation report |
| P2 | Basic login (name + department, no real auth) | Demonstrates access-scoping concept |
| P2 | Suggested/example questions | Guided demo entry points |
| Future | Full RBAC, knowledge graph, model router, plant-wide ingestion, OCR pipeline, analytics dashboards | Roadmap only |

---

## 7. Success Metrics

### 7.1 For the internal round demo
- The 3 prepared demo questions succeed **consistently and reproducibly** on stage.
- Every material claim in a report is linked to a visible, correct source.
- The out-of-scope question is correctly refused ("insufficient evidence"), not hallucinated.
- End-to-end response time for the primary scenario stays under ~30–45 seconds so the demo doesn't stall.

### 7.2 For the broader product story (told to judges, not necessarily built)
- % of investigation answers with full evidence traceability.
- Reduction in engineer time-to-answer vs. manual document search.
- Verification Agent catch rate (fraction of unsupported draft claims it downgrades).

---

## 8. Constraints and Assumptions

- **Sovereignty constraint:** all inference (LLM + vision + embeddings) must run via a local model runtime (Ollama) inside the demo environment; no calls to OpenAI/Gemini/Claude APIs for confidential content processing.
- **Time constraint:** internal round deliverable is a working prototype, not production software — see Non-Goals.
- **Data constraint:** demo corpus is synthetic/representative MRPL-style documents (5–10 PDFs, 1 CSV, 1–2 drawings), not real confidential MRPL data.
- **Compute constraint:** must run demo-reliably on the hardware available to the team (single GPU/consumer laptop) — model choices in `SRS.md` reflect this.

---

## 9. Risks

| Risk | Mitigation |
|---|---|
| Local LLM (e.g., Qwen 2.5) too slow / weak for multi-agent reasoning on demo hardware | Use a small model for classification/routing, a mid-size model for synthesis; pre-cache/pre-warm the demo scenario; strict prompt scoping so each agent call is small |
| Vision/P&ID understanding is unreliable | Scope the P&ID demo to a single, clean, pre-processed diagram; keep it a P1 feature with a graceful fallback to "P&ID data unavailable" |
| Live demo failure | Pre-run and cache the 3 demo scenarios; have a recorded fallback video |
| Over-scoping in the time available | Strict adherence to the priority table in §6; one polished vertical slice beats many partial features |

---

## 10. Timeline (Internal Round)

| Day | Milestone |
|---|---|
| Day 1 (AM) | Corpus prepared (documents, CSV, P&ID); ingestion + chunking + vector store working |
| Day 1 (PM) | Planner + Document Agent + RAG returning cited answers for the SOP scenario |
| Day 2 (AM) | Data Agent (trend calc) + Verification Agent wired into the pipeline; primary P-102 scenario working end-to-end |
| Day 2 (PM) | UI polish (investigation timeline, evidence panel, report export); Vision/P&ID Agent if time permits; rehearse 3 demo scripts |
| Day 3 | Presentation |

---

## 11. Open Questions
- Final choice of local LLM (Qwen 2.5 7B/14B vs. alternative) pending hardware benchmarking — tracked in `SRS.md` §8.
- Whether Vision/P&ID Agent ships as a live feature or a "pre-computed knowledge graph" fallback for the demo.
