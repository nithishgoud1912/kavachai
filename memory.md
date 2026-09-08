# KavachAI Backend Build — Decision Log & Memory

## Section 1 Decisions (Pre-Phase 0) — ALL RESOLVED

| # | Question | Decision | Date |
|---|---|---|---|
| 1 | Demo corpus files | **Draft synthetic corpus**, show for approval before wiring in. Must contain: vibration 2.1→2.8→3.7 mm/s, temp 68→71→77°C, threshold 3.0 mm/s in §4.2, equipment T-101→P-102→V-204→R-101, fire emergency SOP, maintenance history. | 2026-09-08 |
| 2 | LLM choice | **Qwen 2.5 3B** via Ollama. Smaller than docs anticipated — prompts must be tight/structured. | 2026-09-08 |
| 3 | Demo hardware | **RTX 3050 6GB VRAM, 16GB DDR5 RAM**. 3B model fits. VLM alongside too tight. | 2026-09-08 |
| 4 | Embedding model | **nomic-embed-text** (768 dimensions, ~270MB via Ollama). | 2026-09-08 |
| 5 | Vision/VLM approach | **Pre-computed graph fallback**. Equipment relationships pre-loaded in NetworkX. Same §8.4 contract — VLM swap-in later is zero-change. | 2026-09-08 |
| 6 | Vector DB | **ChromaDB** (embedded, persistent, native metadata filtering). | 2026-09-08 |
| 7 | Deployment target | **Docker** with NVIDIA runtime for GPU passthrough. | 2026-09-08 |
| 8 | Ports/CORS/HTTPS | Backend **:8000**, frontend **:3000**, **plain HTTP**. CORS allows `http://localhost:3000`. Ollama on default `:11434`. | 2026-09-08 |
| 9 | Frontend ownership | **Teammate builds in parallel** — do not touch `frontend/` directory. Test backend via scripts/curl. | 2026-09-08 |
| 10 | Session persistence | **SQLite** (same DB as docs/audit — zero extra deps). | 2026-09-08 |
| 11 | Graph store scope | **4 nodes only**: T-101 → P-102 → V-204 → R-101. Minimal for P-102 demo scenario. | 2026-09-08 |

## Tech Stack (Locked)

| Layer | Choice |
|---|---|
| Language/Framework | Python 3.11+, FastAPI |
| LLM | Qwen 2.5 3B via Ollama |
| Embeddings | nomic-embed-text (768d) via Ollama |
| Vision Agent | Pre-computed NetworkX graph (no live VLM) |
| Vector DB | ChromaDB |
| Relational DB | SQLite |
| Object store | Local filesystem (by source_id) |
| Graph store | NetworkX (4 nodes) |
| PDF extraction | PyMuPDF (fitz) |
| Tabular analytics | pandas |
| Streaming | SSE via FastAPI StreamingResponse |
| Deployment | Docker + NVIDIA runtime |

## Build Progress

| Phase | Status | Notes |
|---|---|---|
| Section 1 Q&A | ✅ COMPLETE | All 11 decisions resolved |
| Phase 0 — Scaffolding | ✅ COMPLETE | FastAPI app, health check, config, Ollama tester |
| Phase 1 — Ingestion | ✅ COMPLETE | Extract, chunk, tag, embed, tabular; 7 PDFs, 1 CSV (214 rows), 1 P&ID image |
| Phase 2 — Session | ✅ COMPLETE | POST /session with SQLite storage |
| Phase 3 — Planner | ✅ COMPLETE | FR-PLN-1..3 decomposition + Workflow E out-of-scope check |
| Phase 4 — Document Agent | ✅ COMPLETE | FR-DOC-1..3 vector retrieval + post-filtering |
| Phase 5 — Data Agent | ✅ COMPLETE | FR-DAT-1..3 pure pandas trend (+76%) and threshold breach (3.7 > 3.0) |
| Phase 6 — Vision Agent | ✅ COMPLETE | FR-VIS-1..3 NetworkX graph fallback (T-101 -> P-102 -> V-204 -> R-101) |
| Phase 7 — RAG Agent | ✅ COMPLETE | FR-RAG-1..2 spec retrieval for pump operating limit §4.2 |
| Phase 8 — Synthesis | ✅ COMPLETE | FR-SYN-1..3 accepts EvidenceBundle only, synthesizes draft findings |
| Phase 9 — Verification | ✅ COMPLETE | FR-VER-1..4 verifies against evidence, scores confidence, flags unsupported |
| Phase 10 — Orchestrator & SSE | ✅ COMPLETE | Workflow B parallel execution, SSE streaming, disconnected job resilience |
| Phase 11 — Report & Evidence | ✅ COMPLETE | Report assemble, GET /evidence/{source_id}, PDF export with ReportLab |
| Phase 12 — Audit Log | ✅ COMPLETE | FR-AUD-1..2 two-write pattern, append-only, GET-only router |
| Phase 13 — Model Router | ✅ COMPLETE | Single chokepoint, local Ollama + deterministic fallback for resilience |
| Phase 14 — Failure/Degradation | ✅ COMPLETE | All workflow.md §7 degradation pathways implemented and tested |
| Phase 15 — Testing & Acceptance | ✅ COMPLETE | 19 unit & integration tests passing (100% pass rate) |
| Phase 16 — Demo Rehearsal | ✅ COMPLETE | 3 demo scenarios verified, benchmarked, and cached as fixtures |


## Key Architectural Constraints (Non-Negotiable)
1. LLM never does arithmetic — Data Agent uses pandas (FR-DAT-2, FR-SYN-3)
2. LLM never sees raw documents — only structured EvidenceBundle (FR-SYN-1)
3. All model calls through Model Router — no direct Ollama imports in agents (NFR-MNT-2)
4. No external network calls with query/doc content (NFR-SEC-1)
5. Every module comments the FR/NFR IDs it implements
6. Nothing from Appendix B non-goals list
