# KavachAI — Application Verification & Evaluation Report

**System:** KavachAI — Sovereign Industrial Agentic AI Workbench  
**Problem Statement Reference:** SIH26117 · Mangalore Refinery and Petrochemicals Limited (MRPL)  
**Report Version:** 1.0  
**Generated At:** September 8, 2026  
**Status:** All Systems Operational & Verified Live  

---

## 1. Executive Summary

**KavachAI** is an on-premise, agentic AI investigation workbench engineered for critical industrial facilities (refineries, petrochemical plants, power generation). It provides plant engineers with evidence-backed, deterministic answers to complex operational inquiries while guaranteeing that **all inference remains strictly local — zero confidential data leaves the network**.

This report outlines the verified operational status of the application stack, provides a comprehensive testing guide for evaluators and judges, details the multi-agent architecture, and includes step-by-step instructions for running the 3 core industrial demonstration scenarios.

```
+----------------------------------------------------------------------------------------------------+
|                                    KavachAI System Architecture                                    |
|                                                                                                    |
|    +------------------------------------------------------------------------------------------+    |
|    |                      Next.js 16 Frontend UI (Port 3000)                                   |    |
|    |   Warm Minimal Theme · Playfair Display Logo · SSE Agent Stream · Interactive Evidence   |    |
|    +--------------------------------------------+---------------------------------------------+    |
|                                                 | REST / SSE                                       |
|    +--------------------------------------------v---------------------------------------------+    |
|    |                      FastAPI Backend Orchestrator (Port 8000)                            |    |
|    |          Planner Agent -> Multi-Agent Execution -> Synthesis & Verification Agent        |    |
|    +-----+-----------------------+-----------------------+--------------------+---------------+    |
|          |                       |                       |                    |                    |
|    +-----v------+         +------v-----+          +------v-----+       +------v-----+              |
|    | Document   |         | Data       |          | Vision     |       | Audit Log  |              |
|    | Agent      |         | Agent      |          | Agent      |       | Service    |              |
|    | (PyMuPDF)  |         | (Pandas)   |          | (Topology) |       | (SQLite)   |              |
|    +-----+------+         +------+-----+          +------+-----+       +------+-----+              |
|          |                       |                       |                    |                    |
|    +-----v-----------------------v-----------------------v--------------------v---------------+    |
|    |                  Local Sovereign Storage & Local LLM Inference (Port 11434)              |    |
|    |      ChromaDB (Vectors) · SQLite (Telemetry/Audit) · Local Raw Files · Ollama Qwen 2.5   |    |
|    +------------------------------------------------------------------------------------------+    |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Live Services Health Matrix

Every component of the KavachAI platform is configured and running live:

| Layer | Component | Service URL / Port | Technology Stack | Verified Status |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend** | Interactive Workbench | `http://localhost:3000` | Next.js 16.3.4 (Turbopack), React 19, Tailwind CSS v4 | **ONLINE** |
| **Backend** | API & Orchestrator | `http://localhost:8000` | FastAPI, Uvicorn, Python 3.12, AsyncIO | **ONLINE** |
| **Local LLM** | Local Inference Engine | `http://localhost:11434` | Ollama Daemon, `qwen2.5:3b` (1.9 GB), Local VRAM | **ONLINE** |
| **Vector DB** | Vector & Chunk Store | `backend/data/chroma` | ChromaDB 1.5.9, Persistent SQLite Store | **INGESTED (7 docs)** |
| **Telemetry DB** | Structured Metrics | `backend/data/kavachai.db` | SQLite / SQLAlchemy 2.0 (214 rows time-series) | **POPULATED** |
| **Raw Store** | Document Object Store | `backend/data/objects/` | Local Filesystem Object Store (PDFs, PNG drawings) | **READY** |

---

## 3. Verified Corpus Ingestion Status

The application has been seeded with a realistic, confidential refinery dataset:

```
============================================================
Knowledge Base Ingestion Summary:
  Documents:    7 (Inspection reports Jan/Apr/Jul, Manual, History, SOP, PFD)
  Datasets:     1 (214-row vibration & temperature sensor log)
  PID Drawings: 1 (Unit 101 interconnect: T-101 -> P-102 -> V-204 -> R-101)
============================================================
Phase 1 Ingestion DoD: ALL PASSED
```

### Ingested Assets & Evidence Contracts
1. **`doc_1120`**: `P-102_Inspection_Jan.pdf` (Baseline vibration: 2.1 mm/s, Bearing Temp: 68°C)
2. **`doc_1121`**: `P-102_Inspection_Apr.pdf` (Vibration rise: 2.8 mm/s, Bearing Temp: 71°C)
3. **`doc_1122`**: `P-102_Inspection_Jul.pdf` (Advisory limit exceeded: 3.7 mm/s > 3.0 mm/s limit, Bearing Temp: 77°C)
4. **`doc_1130`**: `P-102_Pump_Operating_Manual.pdf` (Spec sheet: Max permissible continuous vibration = 3.0 mm/s)
5. **`doc_1140`**: `P-102_Maintenance_History.pdf` (Coupling realignment logged 6 months prior)
6. **`doc_sop01`**: `SOP_Emergency_Fire_Evacuation.pdf` (Emergency siren protocol, Assembly Point C)
7. **`doc_pfd01`**: `Unit_101_Interconnect_Description.pdf` (Subsystem upstream/downstream dependencies)
8. **`pid_101`**: `pid_unit_101.png` (P&ID diagram showing T-101 Feed Tank, P-102 Pump, V-204 Control Valve, R-101 Reactor)
9. **`ds_4471`**: `P-102_telemetry_jan_jul.csv` (Deterministic time-series sensor points)

---

## 4. Step-by-Step Test & Evaluation Scenarios

To thoroughly test the application in your browser (`http://localhost:3000`), execute the following 3 verified test scenarios:

### Scenario 1: Multi-Agent Industrial Equipment Investigation
*Tests: Planner decomposition, Document Agent, Data Agent, Vision Agent, Synthesis & Verification.*

1. Navigate to **`http://localhost:3000`**.
2. Enter your Name (`Vikram Sharma`) and select Department (`Engineering` or `Maintenance`).
3. Click **"Enter Workbench"**.
4. In the query box, enter:
   ```text
   Investigate Pump P-102 and determine whether its condition has deteriorated.
   ```
   *(Or click the suggested question chip)*.
5. Click **"Investigate"**.
6. **Observe the Live Investigation Screen (`/investigation/[id]`)**:
   - Real-time Server-Sent Events (SSE) stream will display the active Planner creating sub-tasks.
   - Watch the specialized agents activate:
     - **Planner Agent**: Classifies query in-scope and generates 4 sub-tasks.
     - **Document Agent**: Discovers 3 quarterly inspection reports and operating manuals.
     - **Data Agent**: Queries time-series store and calculates the deterministic 76.2% vibration increase.
     - **Vision Agent**: Parses Unit 101 P&ID topology for upstream/downstream risks.
     - **Verification Agent**: Validates every claim against source IDs before approving the report.
7. **Inspect the Final Report (`/report/[id]`)**:
   - Status badge displays **"ATTENTION REQUIRED"** in warm terracotta rust.
   - **Key Findings Card**: Shows vibration progression ($2.1 \to 2.8 \to 3.7\text{ mm/s}$).
   - **Click on any citation link** (e.g., `P-102_Inspection_Jul.pdf, p. 2`): The interactive **Source Viewer** modal opens, rendering the raw document with highlighted text.
   - **Interactive Telemetry Trend**: Displays the line chart with the 3.0 mm/s Advisory Limit red threshold line.
   - **P&ID Relationship Section**: Visually shows `T-101 -> P-102 (ALERT) -> V-204 -> R-101`.
   - **Export Report**: Click "Export Report" to generate an official branded PDF download.

---

### Scenario 2: Single-Agent Procedural Inquiry (Fast RAG)
*Tests: High-speed semantic search, SOP extraction, rapid response (<10s).*

1. From the Workspace (`http://localhost:3000/workspace`), enter:
   ```text
   What should an employee do during a fire emergency?
   ```
2. Click **"Investigate"**.
3. **Evaluation Checkpoints**:
   - Planner determines this is a procedural query requiring the **Document Agent only**.
   - Result renders with **"NORMAL"** verification badge.
   - Lists exact steps from `SOP_Emergency_Fire_Evacuation.pdf`: alarm activation, shutdown protocol, and evacuation to **Assembly Point C**.
   - Direct clickable citations to page and section of the SOP.

---

### Scenario 3: Out-of-Scope / Hallucination Refusal Guardrail
*Tests: Refusal policy, zero-hallucination compliance, safety perimeter.*

1. From the Workspace, enter an out-of-scope question:
   ```text
   What is the current price of crude oil?
   ```
2. Click **"Investigate"**.
3. **Evaluation Checkpoints**:
   - The Planner and Model Router immediately identify that this query falls outside plant documentation.
   - **Refusal Behavior**: The system **does not hallucinate** or speculate on external market data.
   - Displays the **"Insufficient Evidence"** screen explaining that internal confidential records do not cover external market prices.
   - Offers suggested valid investigation alternatives.

---

### Scenario 4: Immutable Audit Trail Inspection
*Tests: Regulatory compliance, append-only logs, forensic traceability.*

1. In the navigation bar, click **"Audit Log"** (or open `http://localhost:3000/audit`).
2. **Evaluation Checkpoints**:
   - Verify every query you ran is captured chronologically.
   - Inspect columns: **Timestamp**, **User Name**, **Department**, **Query Text**, **Agents Invoked**, **Verification Status**, and **Confidence Score**.
   - Confirms zero data tampering: API gateway rejects all `DELETE` or `PATCH` requests on audit tables.

---

## 5. UI Polish & Design Review Checklist

The frontend has been upgraded with the **Warm Minimal** aesthetic and luxury polish:

- [x] **Logo Typography**: Set in **Playfair Display** serif font with tight letter-spacing in both Header and Login view.
- [x] **Color Palette Consistency**:
  - `#faf8f5` Warm Linen Canvas Background
  - `#eee8df` Warm Neutral Surface-2 (inputs, tags, nested cards)
  - `#2d2a26` Deep Charcoal Text Ink
  - `#c45d3e` Warm Terracotta Rust Accent
- [x] **SVG Grain Overlay**: Fixed 4% opacity organic grain texture overlay across the viewport with `mix-blend-mode: multiply`.
- [x] **Layered Surfaces**: Clear visual depth hierarchy (`bg-bg` $\to$ `bg-surface` $\to$ `bg-surface-2`).
- [x] **Heading Letter-Spacing**: Set to `-0.025em` across all headings for editorial crispness.
- [x] **Hero Page-Load Animations**: Staggered fade-in + `translateY(20px)` with `0.8s` duration and `cubic-bezier(0.16, 1, 0.3, 1)` easing.
- [x] **Scroll-Triggered Reveals**: Below-the-fold sections reveal smoothly via `ScrollObserver` IntersectionObserver.
- [x] **Composite Multi-Layer Shadows**: Contact (`0 1px 2px`), Mid (`0 4px 12px`), and Ambient (`0 16px 32px -4px`) shadow layers.
- [x] **Card Inset Highlight**: `inset 0 1px 0 rgba(255, 255, 255, 0.06)` applied to all card containers.
- [x] **Card Hover Micro-interactions**: Smooth `translateY(-2px)` with lightened borders on hover.
- [x] **Section Padding**: Standardized to `100px` on desktop and `60px` on mobile.
- [x] **Scroll-Reactive Navbar**: Navbar begins transparent and dynamically applies `backdrop-filter: blur(16px)` on scroll.

---

## 6. Verification Commands & Diagnostics

Evaluators can run the following automated commands from the terminal to verify backend code health:

### 1. Ingest Synthetic Corpus
```powershell
cd c:\Users\abhin\Desktop\coding\sih\kavachai-main\kavachai-main\backend
python scripts/ingest_corpus.py
```
*Expected Output: `Phase 1 Ingestion DoD: ALL PASSED`*

### 2. Pre-Run & Cache Demo Scenarios
```powershell
python scripts/run_demo_scenarios.py
```
*Expected Output: Generates 3 JSON scenario fixtures in `tests/fixtures/`.*

### 3. Run Unit & Integration Tests
```powershell
python -m pytest tests/unit/ -v
```
*Expected Output: All unit tests for Planner, Document Agent, Data Agent, Vision Agent, and Synthesis pass.*

### 4. Direct API Health Check
```powershell
# Knowledge base summary
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/knowledge-base/summary"

# Audit log entries
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/audit-log?limit=5"
```

---

## 7. Operational Summary & Conclusion

| Requirement | Implementation | Evidence / Metric |
| :--- | :--- | :--- |
| **Sovereignty & Security** | 100% On-Premise Inference | Ollama `qwen2.5:3b` on `127.0.0.1:11434`; 0 external HTTP calls. |
| **Multimodal Synthesis** | 3 specialized agent types | Text (PyMuPDF) + Numeric (Pandas) + P&ID (Topology Graph). |
| **Evidence Traceability** | Strict Verification Agent | Every claim cites `source_id`, `page_number`, and `section`. |
| **Auditability** | Append-only SQLite log | Tracks user, query, agents invoked, and confidence score. |
| **Design Standard** | Warm Minimal Theme | Playfair Display serif, 4% grain, multi-layer shadows, blur nav. |

**Conclusion:** The KavachAI application is **fully verified, operational, and demo-ready**. All services are active and communicating synchronously across local ports `3000`, `8000`, and `11434`.
