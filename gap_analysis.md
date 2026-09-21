# KavachAI — Gap Analysis vs. Expected Solution

Systematic comparison of what the problem statement **demands** in the expected solution vs. what KavachAI **currently implements**.

---

## Scorecard Summary

| # | Expected Solution Requirement | Status | Severity |
|---|-------------------------------|--------|----------|
| 1 | Working local deployment on single workstation/server | ✅ Present | — |
| 2 | Model auto-selection across ≥2 different task types | ⚠️ Partial | **High** |
| 3 | End-to-end agentic task (e.g. read scanned report → draft approval note as Word) | ⚠️ Partial | **Critical** |
| 4 | Coding task run and verified in a sandbox | ❌ Missing | **Critical** |
| 5 | Multimodal task (image/scanned document understanding) | ⚠️ Partial | **High** |
| 6 | Zero-egress proof via logs or visible network monitor | ❌ Missing | **Critical** |
| 7 | Output as real deliverables (Word/PPT/Excel files) | ❌ Missing | **Critical** |
| 8 | OCR for handwritten notes / scanned PDFs | ❌ Missing | **High** |
| 9 | Multi-step agentic iteration (plan → tool-call → iterate) | ⚠️ Partial | **High** |
| 10 | Sandboxed code execution tool | ❌ Missing | **Critical** |
| 11 | Spreadsheet work tool | ❌ Missing | **High** |
| 12 | Hot-swappable model backend (not locked to one model) | ✅ Present | — |
| 13 | Local knowledge base connector (SOPs, manuals, past correspondence) | ✅ Present | — |

---

## Detailed Gap Breakdown

---

### 1. ✅ Working Local Deployment
**Status: PRESENT**

The project has a complete [docker-compose.yml](file:///c:/Users/HP/Desktop/SIH/KavachAI/docker-compose.yml) with three services (backend, frontend, ollama), all containerized and deployable on a single machine. Ollama runs locally. This satisfies the requirement.

---

### 2. ⚠️ Model Auto-Selection Across ≥2 Task Types
**Status: PARTIAL — needs visible demonstration**

The [model_router.py](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/orchestrator/model_router.py) does map task types to different models:
- `text_reasoning` / `classification` → `qwen2.5:3b`
- `embedding` → `nomic-embed-text`  
- `vision` → `qwen2.5vl:3b`

> [!WARNING]
> **Gap**: The `text_reasoning` and `classification` task types currently map to the **same model** (`qwen2.5:3b`). The expected solution explicitly asks for auto-selection demonstrated **across at least two different task types** with *visible model switching*. The current routing is a static config lookup — there is no intelligent routing logic that picks a model based on task analysis (e.g. "this is a coding request, route to DeepSeek-Coder; this is a summary request, route to Qwen").
> 
> **What's needed**: At least one additional distinct model (e.g., a code-specialized model like `deepseek-coder` or `codellama`) mapped to a `coding` task type, and **visible UI/logs showing the routing decision**.

---

### 3. ⚠️ End-to-End Agentic Task (Scanned Report → Approval Note as Word File)
**Status: PARTIAL — critical gap on output format**

The investigation pipeline in [investigation.py](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/orchestrator/investigation.py) does run an end-to-end agentic workflow:
- Planner decomposes query → specialist agents run in parallel → Synthesis → Verification → Report

> [!CAUTION]
> **Gap 1: No Word (.docx) output**. The export router ([export.py](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/routers/export.py)) only generates **PDF**. The problem statement specifically asks for _"approval notes, PPT/Word/Excel files"_ as deliverables. There is no `.docx` generation anywhere.
> 
> **Gap 2: No approval note template**. The problem statement's example demo is _"reading a scanned inspection report, pulling out key findings and drafting an approval note as a Word file."_ There is no approval note document template or generation logic.

---

### 4. ❌ Coding Task Run & Verified in a Sandbox
**Status: COMPLETELY MISSING**

> [!CAUTION]
> There is **zero** code execution infrastructure in the project. No sandbox, no Docker-based code runner, no subprocess execution, no Jupyter kernel. The grep for `sandbox` and `code_execution` returned no results.
> 
> The problem statement explicitly requires: _"A coding task run and verified in a sandbox."_ This must be demonstrable at the venue.
> 
> **What's needed**: A sandboxed code execution environment (e.g., subprocess with resource limits, Docker container sandbox, or Pyodide-based WASM execution) with:
> - Code generation from the LLM
> - Execution in an isolated environment
> - Stdout/stderr capture and result verification
> - UI to show the generated code, execution output, and pass/fail status

---

### 5. ⚠️ Multimodal Task (Image/Scanned Document Understanding)
**Status: PARTIAL**

The [vision_agent.py](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/agents/vision_agent.py) does use `qwen2.5vl:3b` for P&ID analysis, and [model_router.py](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/orchestrator/model_router.py#L176-L230) has a `generate_vision()` method. However:

> [!WARNING]
> **Gap 1**: Vision is narrowly scoped to **P&ID drawings** only (equipment location + connectivity). The problem statement requires understanding of _"scanned PDFs, handwritten notes, engineering drawings, photographs."_ There's no general-purpose image understanding, photograph analysis, or handwritten note recognition.
> 
> **Gap 2**: The vision agent has extensive **hardcoded offline fallbacks** in model_router that return canned JSON for "P-102", "T-101" etc. This means during a demo without GPU, the multimodal task is essentially faked with deterministic responses.

---

### 6. ❌ Zero-Egress Proof (Logs or Visible Network Monitor)
**Status: COMPLETELY MISSING**

> [!CAUTION]
> The problem statement explicitly requires: _"The system should also show, through logs or a visible network monitor, that no external calls are made at any point. That's the actual proof of the sovereign claim, not just a statement of it."_
> 
> Currently, the project only has:
> - Text labels in PDF exports saying "Air-Gapped" / "Zero External Egress"
> - No actual network monitoring, no packet capture, no egress log dashboard
> 
> **What's needed**: A real-time network activity monitor panel in the UI (or accessible via a dedicated page) that captures all outbound connections and proves visually that only `localhost:11434` (Ollama) is contacted. This could be:
> - A backend middleware logging all `httpx` calls with timestamps and destinations
> - A `tcpdump`/`ss` based live monitor shown in the UI
> - A Docker network policy that blocks all external traffic + a visible log of blocked attempts

---

### 7. ❌ Output as Real Deliverables (Word/PPT/Excel)
**Status: MISSING**

| Format | Status |
|--------|--------|
| PDF | ✅ Implemented via ReportLab |
| Word (.docx) | ❌ Not implemented |
| PowerPoint (.pptx) | ❌ Not implemented |
| Excel (.xlsx) | ❌ Not implemented (only `openpyxl` in requirements for reading) |
| Working Code | ❌ No code generation + sandbox |

The problem statement demands: _"Output should be real deliverables, approval notes, PPT/Word/Excel files, working code, calculations with steps shown."_

> [!IMPORTANT]
> **What's needed**: At minimum, add `.docx` export (using `python-docx`, already in requirements) and ideally `.pptx` (using `python-pptx`). An "Export as Word" and "Export as PPTX" button alongside the existing PDF export.

---

### 8. ❌ OCR for Handwritten Notes / Scanned PDFs
**Status: MISSING**

The [SRS.md](file:///c:/Users/HP/Desktop/SIH/KavachAI/SRS.md) explicitly states OCR is _"Roadmap only"_ and _"The demo document corpus is prepared in advance and is clean enough not to require a production-grade OCR pipeline."_

> [!WARNING]
> The problem statement requires: _"scanned PDFs, handwritten notes, engineering drawings, photographs, read through on-device OCR and vision models."_
>
> Current text extraction ([extract.py](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/ingestion/extract.py)) uses PyMuPDF's `get_text()` which only extracts **embedded text layers** from PDFs. Scanned PDFs (image-only pages) will return empty text.
>
> **What's needed**: Integration of a local OCR engine such as:
> - **Tesseract** (via `pytesseract`) — most common
> - **EasyOCR** — better for handwritten text
> - **Surya** — modern OCR that runs locally
> - Or using the vision model (Qwen-VL) itself for OCR-free text extraction from images

---

### 9. ⚠️ Multi-Step Agentic Iteration (Plan → Tool-Call → Iterate)
**Status: PARTIAL**

The investigation pipeline does implement a multi-step flow: Planner → Document/Data/Vision/RAG agents → Synthesis → Verification. This is genuinely agentic.

> [!WARNING]
> **Gap**: The agent workflow is **one-shot, non-iterative**. The problem statement says: _"iterate on a task instead of answering once and stopping."_ Currently:
> - If the planner generates a bad plan, it's never corrected
> - If synthesis produces low-confidence findings, there's no re-query loop
> - Agents don't call back to other agents if they need more information
> - There's no tool-calling loop where the LLM decides what tool to invoke next
>
> This is more of a **pipeline** than a true **agent with tool-calling and iteration**. A true agentic system would have a ReAct-style loop where the LLM decides when to stop.

---

### 10. ❌ Sandboxed Code Execution Tool
**Status: COMPLETELY MISSING**

See Gap #4. The problem statement lists _"code execution in a sandbox"_ as one of the **local tools** the agent needs. This is distinct from the "coding task" demo requirement — it's about the agent being able to write and execute code as part of its reasoning.

---

### 11. ❌ Spreadsheet Work Tool
**Status: MISSING**

The problem statement lists _"spreadsheet work"_ as a local tool the agent should call. Currently:
- The data agent ([data_agent.py](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/agents/data_agent.py)) reads CSV/XLSX for trend analysis
- But there's no tool that lets the agent **create, modify, or compute over spreadsheets** as a task output

**What's needed**: An agent tool that can generate `.xlsx` files with computed results, formulas, and formatting.

---

### 12. ✅ Hot-Swappable Model Backend
**Status: PRESENT**

The [model_router.py](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/orchestrator/model_router.py) centralizes all model dispatch. Models are configurable via [.env](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/.env) and [config.py](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/config.py). New models can be added by changing config without touching agent code. This satisfies NFR-MNT-2.

---

### 13. ✅ Local Knowledge Base Connector
**Status: PRESENT**

The [knowledge_base.py](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/routers/knowledge_base.py) router provides document upload, dataset ingestion, and vector search via ChromaDB. The ingestion pipeline (extract → chunk → tag → embed → store) is complete. This satisfies the requirement for grounding in organizational SOPs and manuals.

---

## Priority Matrix for Demo Readiness

### 🔴 Critical (Demo will fail without these)

| Gap | Effort | Recommendation |
|-----|--------|----------------|
| **Coding sandbox** | 2-3 days | Build a Docker-based Python sandbox with subprocess execution, stdout capture, and UI panel |
| **Word (.docx) export** | 1 day | Use `python-docx` to generate approval notes; add export button |
| **Network egress proof** | 1-2 days | Add middleware logging all outbound calls; build a "Sovereign Monitor" UI panel showing real-time connection log |
| **Visible model auto-selection** | 1 day | Add a `coding` task type mapped to a code model; show model selection in agent timeline UI |

### 🟡 High Priority (Judges will likely probe these)

| Gap | Effort | Recommendation |
|-----|--------|----------------|
| **OCR for scanned docs** | 1-2 days | Integrate Tesseract or EasyOCR in `extract.py` as fallback when PyMuPDF returns empty text |
| **Agentic iteration loop** | 2-3 days | Add a ReAct-style loop in the chat or investigation flow where the LLM can decide to re-query |
| **Excel output** | 1 day | Use `openpyxl` (already installed) to generate `.xlsx` from data analysis |
| **General image understanding** | 1 day | Extend vision agent beyond P&ID to handle photographs and general documents |

### 🟢 Nice-to-Have (Strengthens but not blocking)

| Gap | Effort | Recommendation |
|-----|--------|----------------|
| PPT (.pptx) export | 1 day | Use `python-pptx` to auto-generate board presentations |
| Handwritten note recognition | 1-2 days | Use EasyOCR or Qwen-VL for handwriting |
| File read/write tool for agent | 0.5 day | Let the agent save/read files on the server during a task |

---

## Summary

The project has a **strong architectural foundation** — the model router, investigation pipeline, knowledge base, and multi-agent orchestration are well-built. However, **5 of the expected solution's explicit demo requirements are either completely missing or critically incomplete**:

1. **No coding sandbox** — the problem statement specifically asks for this as a demo item
2. **No Word/PPT/Excel output** — only PDF export exists
3. **No network egress proof** — the "sovereign" claim has no verifiable evidence in the UI
4. **No OCR** — scanned documents cannot be processed
5. **Model auto-selection is superficial** — same model handles reasoning and classification; no code-specific model

These 5 gaps represent the difference between a project that _describes_ sovereignty and one that _proves_ it at a demo.
