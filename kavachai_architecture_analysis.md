# KavachAI — Architecture & Data-Flow Analysis

> **Scope**: This document is derived exclusively from the implemented source code in the repository. Every diagram cites the specific files, classes, and line ranges that support it. Items marked **[INFERRED]** are reasonable deductions not directly visible in code.

---

## 1. System Overview Diagram

Shows all major modules, their relationships, external services, and data stores as implemented.

```mermaid
graph TB
    subgraph "Browser Client"
        FE["Next.js 16 Frontend<br/>(React 19 + Tailwind 4)"]
    end

    subgraph "FastAPI Backend (Python)"
        MAIN["FastAPI App<br/>app/main.py"]
        
        subgraph "API Routers"
            R_SESSION["Session Router<br/>/api/v1/session"]
            R_KB["Knowledge Base Router<br/>/api/v1/knowledge-base/*"]
            R_INV["Investigations Router<br/>/api/v1/investigations/*"]
            R_EV["Evidence Router<br/>/api/v1/evidence/*"]
            R_EXP["Export Router<br/>/api/v1/exports/*"]
            R_AUD["Audit Router<br/>/api/v1/audit-log"]
        end

        subgraph "Orchestrator"
            ORCH["InvestigationRunner<br/>orchestrator/investigation.py"]
            MR["ModelRouter<br/>orchestrator/model_router.py"]
        end

        subgraph "AI Agents"
            PLAN["Planner Agent"]
            DOC["Document Agent"]
            DATA["Data Agent"]
            VIS["Vision Agent"]
            RAG["RAG Agent"]
            SYN["Synthesis Agent"]
            VER["Verification Agent"]
        end

        subgraph "Ingestion Pipeline"
            EXT["extract.py"]
            CHK["chunk.py"]
            TAG["tag.py"]
            EMB["embed.py"]
            TAB["tabular.py"]
        end

        subgraph "Services"
            AUD_SVC["Audit Service"]
            RPT_SVC["Report Service"]
        end
    end

    subgraph "Data Stores"
        SQLITE[("SQLite<br/>kavachai.db")]
        CHROMA[("ChromaDB<br/>Vector Store")]
        OBJ[("Object Store<br/>Filesystem")]
        GRAPH["NetworkX<br/>Graph Store<br/>(In-Memory)"]
    end

    OLLAMA["Ollama Server<br/>(localhost:11434)<br/>Qwen 2.5 3B + nomic-embed-text"]

    FE -->|"HTTP/SSE"| MAIN
    MAIN --> R_SESSION & R_KB & R_INV & R_EV & R_EXP & R_AUD
    R_INV --> ORCH
    ORCH --> PLAN & DOC & DATA & VIS & RAG & SYN & VER
    PLAN & SYN & VER -->|"generate/chat"| MR
    DOC & RAG -->|"embed"| MR
    EMB -->|"embed"| MR
    MR -->|"HTTP POST"| OLLAMA
    R_KB --> EXT --> CHK --> TAG --> EMB
    EMB --> CHROMA
    R_KB --> TAB --> SQLITE
    R_SESSION & R_INV & R_AUD --> SQLITE
    DOC & RAG --> CHROMA
    DATA --> SQLITE
    VIS --> GRAPH
    R_KB & R_EV --> OBJ
    AUD_SVC --> SQLITE
    RPT_SVC --> R_INV
```

**Source references:**
- Entry point: [main.py](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/main.py#L21-L61)
- Config & env: [config.py](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/config.py#L12-L48)
- Frontend entry: [page.tsx](file:///c:/Users/HP/Desktop/SIH/KavachAI/frontend/app/page.tsx) (session login), [workspace/page.tsx](file:///c:/Users/HP/Desktop/SIH/KavachAI/frontend/app/workspace/page.tsx) (query input)
- API client: [api.ts](file:///c:/Users/HP/Desktop/SIH/KavachAI/frontend/app/services/api.ts)

---

## 2. Detailed Workflow Diagrams

### 2.1 Workflow A — Session Creation (User Onboarding)

```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant FE as Next.js Frontend
    participant API as POST /api/v1/session
    participant DB as SQLite

    U->>FE: Enter name + department
    FE->>FE: Validate (name non-empty, dept selected)
    FE->>API: POST {name, department}
    API->>DB: INSERT INTO sessions (id, name, department, issued_at)
    DB-->>API: session row
    API-->>FE: {session_id, name, department, issued_at}
    FE->>FE: sessionStorage.setItem("kavachai_session", ...)
    FE->>FE: router.push("/workspace")
    Note over FE: Session stored in sessionStorage only.<br/>No JWT, no cookie auth.
```

**Source references:**
- Frontend form: [page.tsx L33-L51](file:///c:/Users/HP/Desktop/SIH/KavachAI/frontend/app/page.tsx#L33-L51)
- Session hook: [useSession.ts L34-L42](file:///c:/Users/HP/Desktop/SIH/KavachAI/frontend/app/hooks/useSession.ts#L34-L42)
- Backend router: [session.py L17-L33](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/routers/session.py#L17-L33)
- SQL model: [sql_models.py L31-L42](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/db/sql_models.py#L31-L42)

---

### 2.2 Workflow B — Document Ingestion Pipeline

```mermaid
flowchart TD
    START([User uploads file via<br/>POST /knowledge-base/documents]) --> PARSE_EQ[Parse equipment_ids<br/>from JSON string]
    PARSE_EQ --> GEN_SRC[Generate source_id<br/>doc_UUID8]
    GEN_SRC --> SAVE_OBJ[Save raw bytes to<br/>Object Store]
    SAVE_OBJ --> INSERT_DB[INSERT Document record<br/>status = processing]
    INSERT_DB --> EXTRACT{extract_text<br/>.pdf / .docx / .txt}
    
    EXTRACT -->|PDF| PYMUPDF[PyMuPDF: extract per-page text]
    EXTRACT -->|DOCX| DOCX_LIB[python-docx: paragraph concat]
    EXTRACT -->|TXT| TXT_READ[UTF-8 decode]
    EXTRACT -->|Other| EMPTY[Return empty pages]
    
    PYMUPDF & DOCX_LIB & TXT_READ --> HAS_PAGES{pages non-empty?}
    EMPTY --> NO_TEXT[status = ready, chunks = 0]
    
    HAS_PAGES -->|Yes| CHUNK[chunk_pages<br/>512 chars, 64 overlap<br/>sentence-boundary aware]
    HAS_PAGES -->|No| NO_TEXT
    
    CHUNK --> TAG_CHUNKS[tag_chunks<br/>source_id, page, equipment_ids,<br/>document_type, department_scope]
    TAG_CHUNKS --> EMBED[generate_embeddings<br/>via ModelRouter → Ollama<br/>nomic-embed-text 768d]
    EMBED --> VECTOR_STORE[vector_store.upsert_chunks<br/>ChromaDB cosine HNSW]
    VECTOR_STORE --> UPDATE_READY[UPDATE Document<br/>status = ready, chunks = N]
    
    NO_TEXT --> RETURN_RESP
    UPDATE_READY --> RETURN_RESP[Return 202<br/>document_id, status]

    TAG_CHUNKS -.->|On Exception| FAIL[UPDATE status = failed<br/>Raise HTTP 500]

    style FAIL fill:#f87171,color:#1e1e1e
    style UPDATE_READY fill:#4ade80,color:#1e1e1e
```

**Source references:**
- Router: [knowledge_base.py L36-L122](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/routers/knowledge_base.py#L36-L122)
- Extract: [extract.py L14-L99](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/ingestion/extract.py#L14-L99)
- Chunk: [chunk.py L13-L54](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/ingestion/chunk.py#L13-L54)
- Tag: [tag.py L17-L64](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/ingestion/tag.py#L17-L64)
- Embed: [embed.py L14-L35](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/ingestion/embed.py#L14-L35)

---

### 2.3 Workflow C — Dataset Ingestion

```mermaid
flowchart TD
    START([POST /knowledge-base/datasets]) --> GEN_ID[Generate dataset_id<br/>ds_UUID4]
    GEN_ID --> SAVE[Save raw file to Object Store]
    SAVE --> PARSE[parse_tabular_file<br/>pandas read_csv / read_excel]
    PARSE --> NORM[Normalize columns: lowercase, strip]
    NORM --> VALIDATE{Required columns?<br/>timestamp, equipment_id,<br/>metric, value, unit}
    VALIDATE -->|Missing| ERR_422[HTTP 422: Missing columns]
    VALIDATE -->|Present| COERCE[pd.to_numeric value column<br/>dropna on coercion failures]
    COERCE --> STORE_TAB[tabular_store.ingest_dataframe<br/>→ SQLite table: dataset_XXXX]
    STORE_TAB --> INSERT_DS[INSERT Dataset record<br/>status = ready]
    INSERT_DS --> RETURN[Return dataset_id,<br/>columns, row_count, status]

    style ERR_422 fill:#f87171,color:#1e1e1e
    style RETURN fill:#4ade80,color:#1e1e1e
```

**Source references:**
- Router: [knowledge_base.py L148-L188](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/routers/knowledge_base.py#L148-L188)
- Tabular parse: [tabular.py L18-L78](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/ingestion/tabular.py#L18-L78)
- Tabular store: [tabular_store.py L34-L66](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/db/tabular_store.py#L34-L66)

---

### 2.4 Workflow D — Investigation Pipeline (Core Business Flow)

This is the most complex flow in the system. Split into 3 sub-diagrams.

#### 2.4.1 Investigation Creation & Background Dispatch

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as POST /investigations
    participant DB as SQLite
    participant AUD as Audit Service
    participant BG as BackgroundTask

    FE->>API: {query, session_id}
    API->>DB: SELECT session WHERE id = session_id
    alt Session not found
        API-->>FE: 401 Invalid session_id
    end
    API->>DB: INSERT investigation (query, session_id, status=planning)
    API->>AUD: create_audit_entry (first write)
    AUD->>DB: INSERT audit_log (status=started)
    API->>BG: add_task(_run_investigation_background)
    API-->>FE: 202 {investigation_id, status, stream_url}
    FE->>FE: router.push(/investigation/{id})
    FE->>API: GET /investigations/{id}/stream (SSE)
    Note over BG: Pipeline runs server-side<br/>independent of SSE connection
```

**Source references:**
- Create endpoint: [investigations.py L78-L122](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/routers/investigations.py#L78-L122)
- Background runner: [investigations.py L34-L75](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/routers/investigations.py#L34-L75)
- Audit first write: [audit_service.py L18-L39](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/services/audit_service.py#L18-L39)

#### 2.4.2 Agent Pipeline Execution (InvestigationRunner.run)

```mermaid
flowchart TD
    START([InvestigationRunner.run]) --> PLAN_EMIT[Emit: planner → working]
    PLAN_EMIT --> CORPUS[Build CorpusSummary<br/>doc/dataset/PID counts]
    CORPUS --> PLAN_CALL[Planner Agent<br/>LLM: classify + decompose]
    PLAN_CALL --> STORE_PLAN[Store plan JSON in DB<br/>status = investigating]
    
    STORE_PLAN --> SCOPE{is_in_scope?}
    SCOPE -->|No| INSUF_E[Insufficient evidence<br/>status = insufficient_evidence]
    
    SCOPE -->|Yes| GROUP[Group sub-tasks by agent type:<br/>doc_tasks, data_tasks,<br/>vision_tasks, rag_tasks]
    
    GROUP --> PARALLEL["asyncio.gather (parallel):<br/>Document Agent<br/>Data Agent<br/>Vision Agent"]
    PARALLEL --> RAG_SEQ[RAG Agent<br/>runs after parallel block]
    RAG_SEQ --> ASSEMBLE[Assemble EvidenceBundle]
    
    ASSEMBLE --> SYNTH_EMIT[Emit: synthesis → working]
    SYNTH_EMIT --> SYNTH[Synthesis Agent<br/>LLM: produce DraftFindings]
    SYNTH --> VER_EMIT[Emit: verification → working]
    VER_EMIT --> VERIFY[Verification Agent<br/>LLM: classify each finding]
    
    VERIFY --> CHECK_SUP{supported_count > 0?}
    CHECK_SUP -->|No| INSUF_V[Insufficient evidence<br/>No findings verified]
    CHECK_SUP -->|Yes| BUILD_RPT[build_report<br/>report_service.py]
    
    BUILD_RPT --> STORE_RPT[Store report in DB<br/>status = complete<br/>confidence, verification_status]
    STORE_RPT --> AUDIT_RES[Audit Service: resolve_audit_entry<br/>second write]
    AUDIT_RES --> DONE([Return report dict])
    
    INSUF_E --> AUDIT_RES2[Audit resolve: insufficient_evidence]
    INSUF_V --> AUDIT_RES3[Audit resolve: insufficient_evidence]

    style INSUF_E fill:#fbbf24,color:#1e1e1e
    style INSUF_V fill:#fbbf24,color:#1e1e1e
    style DONE fill:#4ade80,color:#1e1e1e
```

**Source references:**
- Full pipeline: [investigation.py L64-L185](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/orchestrator/investigation.py#L64-L185)
- Planner: [planner.py L46-L108](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/agents/planner.py#L46-L108)
- Synthesis: [synthesis.py L46-L106](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/agents/synthesis.py#L46-L106)
- Verification: [verification.py L53-L127](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/agents/verification.py#L53-L127)
- Report builder: [report_service.py L17-L72](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/services/report_service.py#L17-L72)

#### 2.4.3 Individual Agent Detail

```mermaid
flowchart LR
    subgraph "Document Agent"
        DA_IN[sub_task_goal + filters] --> DA_EMB[Embed goal via ModelRouter]
        DA_EMB --> DA_Q[ChromaDB vector query<br/>n_results * 2]
        DA_Q --> DA_BOOST[Boost score if<br/>equipment_id matches]
        DA_BOOST --> DA_OUT["List[DocumentChunk]<br/>chunk_text, source_id, page, score"]
    end

    subgraph "Data Agent (NO LLM)"
        DTA_IN[metric + equipment_id + dataset_id] --> DTA_Q[TabularStore.query_by_equipment<br/>pandas SQL query]
        DTA_Q --> DTA_TREND[Compute trend via<br/>half-split avg comparison]
        DTA_TREND --> DTA_PCT[Compute pct_change<br/>first→last value]
        DTA_PCT --> DTA_OUT["DataAnalysisResult<br/>trend, pct_change, data_points"]
    end

    subgraph "Vision Agent (Pre-Computed)"
        VA_IN[equipment_id] --> VA_CHECK{equipment_exists<br/>in NetworkX graph?}
        VA_CHECK -->|No| VA_NOTFOUND["VisionAnalysisResult<br/>found=false"]
        VA_CHECK -->|Yes| VA_CONN[get_connections<br/>predecessors + successors]
        VA_CONN --> VA_OUT["VisionAnalysisResult<br/>found=true, connections, conf=0.95"]
    end

    subgraph "RAG Agent"
        RA_IN[query + equipment_id] --> RA_AUGMENT["Prepend 'specification<br/>threshold limit' to query"]
        RA_AUGMENT --> RA_EMB[Embed via ModelRouter]
        RA_EMB --> RA_Q[ChromaDB query<br/>prefer manuals/SOPs]
        RA_Q --> RA_BOOST[Boost: equipment match +0.4<br/>spec doc type +0.3]
        RA_BOOST --> RA_SEC[Extract §section refs<br/>via regex]
        RA_SEC --> RA_OUT["List[SpecChunk]<br/>chunk_text, source_id, page, section"]
    end
```

**Source references:**
- Document Agent: [document_agent.py L21-L78](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/agents/document_agent.py#L21-L78)
- Data Agent: [data_agent.py L21-L87](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/agents/data_agent.py#L21-L87) — **pure pandas, zero LLM calls**
- Vision Agent: [vision_agent.py L19-L55](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/agents/vision_agent.py#L19-L55) — **pre-computed NetworkX, no VLM**
- RAG Agent: [rag_agent.py L21-L83](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/agents/rag_agent.py#L21-L83)

---

### 2.5 Workflow E — SSE Streaming to Frontend

```mermaid
sequenceDiagram
    participant FE as Frontend (EventSource)
    participant SSE as GET /investigations/{id}/stream
    participant RUNNERS as _runners dict (in-memory)
    participant DB as SQLite

    FE->>SSE: Open SSE connection
    loop Poll every 500ms
        SSE->>RUNNERS: Check runner.events[last_index:]
        alt New events available
            SSE-->>FE: event: agent_update<br/>data: {agent, status, message, elapsed_ms}
        end
        SSE->>DB: SELECT investigation.status
        alt status = complete
            SSE-->>FE: event: investigation_complete<br/>data: {investigation_id, report_url}
            Note over SSE: Stream ends
        else status = insufficient_evidence
            SSE-->>FE: event: insufficient_evidence<br/>data: {investigation_id, message}
            Note over SSE: Stream ends
        end
    end

    Note over FE: Frontend reconnects on error<br/>up to 5 attempts with exp backoff
```

**Source references:**
- SSE endpoint: [investigations.py L125-L179](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/routers/investigations.py#L125-L179)
- SSE client: [sse.ts L16-L117](file:///c:/Users/HP/Desktop/SIH/KavachAI/frontend/app/services/sse.ts#L16-L117)
- Dedup: [sse.ts L21](file:///c:/Users/HP/Desktop/SIH/KavachAI/frontend/app/services/sse.ts#L21) — `seenEventIds` Set

---

### 2.6 Workflow F — Report Export (PDF)

```mermaid
flowchart TD
    START([POST /investigations/{id}/export]) --> FETCH[Fetch Investigation from DB]
    FETCH --> HAS_REPORT{report exists?}
    HAS_REPORT -->|No| ERR_404[HTTP 404]
    HAS_REPORT -->|Yes| CHECK_FMT{format == pdf?}
    CHECK_FMT -->|No| ERR_422[HTTP 422: Unsupported format]
    CHECK_FMT -->|Yes| GEN_ID[Generate export_id: exp_UUID4]
    GEN_ID --> BUILD_PDF[_generate_pdf via ReportLab<br/>Custom KavachAI palette<br/>Gold/teal — no blue hyperlinks]
    BUILD_PDF --> SAVE[Save to ./data/exports/]
    SAVE --> RETURN[Return export_id + download_url]
    
    DOWNLOAD([GET /exports/{filename}]) --> SERVE[FileResponse<br/>application/pdf]

    style ERR_404 fill:#f87171,color:#1e1e1e
    style ERR_422 fill:#f87171,color:#1e1e1e
```

**Source references:**
- Export router: [export.py L25-L72](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/routers/export.py#L25-L72)
- PDF generator: [export.py L75-L140](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/routers/export.py#L75-L140)

---

### 2.7 Workflow G — Audit Log (Append-Only)

```mermaid
flowchart TD
    subgraph "Write Path (Two-Write Pattern)"
        W1[Investigation Created] -->|First Write| CREATE[create_audit_entry<br/>status=started]
        W2[Investigation Resolved] -->|Second Write| RESOLVE[resolve_audit_entry<br/>agents_invoked, confidence,<br/>verification_status, status]
    end

    subgraph "Read Path (Only Endpoint)"
        R1[GET /audit-log?limit=50&offset=0] --> QUERY[SELECT audit_log<br/>ORDER BY created_at DESC<br/>LIMIT/OFFSET pagination]
        QUERY --> RETURN["AuditLogResponse<br/>{entries[], total}"]
    end

    subgraph "Enforcement"
        NO_DEL["❌ No DELETE endpoint"]
        NO_PATCH["❌ No PATCH endpoint"]
        NO_ORM["❌ No ORM delete/update helper"]
    end

    style NO_DEL fill:#f87171,color:#1e1e1e
    style NO_PATCH fill:#f87171,color:#1e1e1e
    style NO_ORM fill:#f87171,color:#1e1e1e
```

**Source references:**
- Audit service: [audit_service.py](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/services/audit_service.py)
- Audit router: [audit.py](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/routers/audit.py) — GET only
- SQL model comment: [sql_models.py L107-L114](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/db/sql_models.py#L107-L114)

---

### 2.8 Workflow H — Error/Degradation Handling & Offline Fallback

```mermaid
flowchart TD
    subgraph "Model Router Resilience"
        CHECK[is_ollama_available?<br/>GET /api/tags, 300ms timeout,<br/>5s cache]
        CHECK -->|Online| LIVE[Call Ollama API<br/>/api/generate or /api/chat]
        CHECK -->|Offline| OFFLINE[_offline_generate<br/>Deterministic hardcoded responses<br/>for 3 demo scenarios]
        LIVE -->|HTTP error| OFFLINE
    end

    subgraph "Embedding Fallback"
        EMB_CHECK[Ollama available?]
        EMB_CHECK -->|Yes| EMB_LIVE[/api/embed → 768d vectors]
        EMB_CHECK -->|No| EMB_PSEUDO[_pseudo_embed<br/>MD5 hash-bag → 768d<br/>preserves cosine similarity]
    end

    subgraph "Agent-Level Degradation"
        DOC_FAIL[Document Agent fails] --> DOC_SKIP[Emit: failed<br/>Continue pipeline]
        DATA_NONE[No dataset available] --> DATA_SKIP[Emit: skipped<br/>Drop data sub-finding]
        VIS_TIMEOUT[Vision Agent timeout] --> VIS_SKIP[Emit: failed<br/>Continue without P&ID]
        SYNTH_BAD[Synthesis bad JSON] --> SYNTH_FALL[_fallback_synthesis<br/>Basic finding from data]
        VER_BAD[Verification bad JSON] --> VER_FALL[_fallback_verification<br/>All partially_supported, conf=50]
    end
```

**Source references:**
- Ollama check: [model_router.py L47-L60](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/orchestrator/model_router.py#L47-L60)
- Offline generate: [model_router.py L236-L349](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/orchestrator/model_router.py#L236-L349)
- Pseudo-embed: [model_router.py L212-L234](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/orchestrator/model_router.py#L212-L234)
- Agent error handling: [investigation.py L214-L325](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/orchestrator/investigation.py#L214-L325)

---

## 3. Data-Flow Diagrams

### 3.1 Level 0 — Context Diagram

```mermaid
flowchart LR
    USER(("Plant Engineer /<br/>HSE Operator"))
    KAVACH["KavachAI System"]
    OLLAMA(("Ollama LLM Server<br/>(Local Only)"))

    USER -->|"name, department,<br/>investigation query,<br/>documents, datasets"| KAVACH
    KAVACH -->|"session token,<br/>agent timeline (SSE),<br/>investigation report,<br/>PDF export,<br/>audit log"| USER
    KAVACH <-->|"prompts → completions,<br/>texts → embeddings"| OLLAMA

    style KAVACH fill:#0f766e,color:#fff
```

---

### 3.2 Level 1 — Internal Processes & Data Stores

```mermaid
flowchart TD
    USER(("User"))

    subgraph "P1: Session Management"
        P1_PROC["Create Session"]
    end

    subgraph "P2: Knowledge Ingestion"
        P2_DOC["Ingest Document"]
        P2_DS["Ingest Dataset"]
    end

    subgraph "P3: Investigation Engine"
        P3_PLAN["Plan Investigation"]
        P3_GATHER["Gather Evidence"]
        P3_SYNTH["Synthesize + Verify"]
    end

    subgraph "P4: Report & Export"
        P4_RPT["Build Report"]
        P4_EXP["Export PDF"]
    end

    subgraph "P5: Audit"
        P5_LOG["Log & Query Audit"]
    end

    SQLITE[("SQLite DB<br/>sessions, investigations,<br/>documents, datasets,<br/>audit_log,<br/>dataset_* tables")]
    CHROMA[("ChromaDB<br/>kavachai_chunks collection<br/>embeddings + metadata")]
    OBJ[("Object Store<br/>./data/objects/<br/>raw files per source_id")]
    GRAPH[("Graph Store<br/>NetworkX in-memory<br/>4-node equipment graph")]
    EXPORTS[("Export Store<br/>./data/exports/<br/>PDF files")]
    OLLAMA(("Ollama"))

    USER -->|"name, dept"| P1_PROC
    P1_PROC -->|"session row"| SQLITE
    P1_PROC -->|"session_id"| USER

    USER -->|"file bytes, doc_type,<br/>equipment_ids"| P2_DOC
    P2_DOC -->|"raw file"| OBJ
    P2_DOC -->|"document record"| SQLITE
    P2_DOC -->|"chunk embeddings<br/>+ metadata"| CHROMA
    P2_DOC <-->|"texts → embeddings"| OLLAMA

    USER -->|"CSV/XLSX bytes"| P2_DS
    P2_DS -->|"raw file"| OBJ
    P2_DS -->|"dataset record"| SQLITE
    P2_DS -->|"dataset_* table rows"| SQLITE

    USER -->|"query, session_id"| P3_PLAN
    P3_PLAN <-->|"prompt → sub_tasks"| OLLAMA
    P3_PLAN -->|"plan JSON"| SQLITE
    P3_PLAN --> P3_GATHER

    P3_GATHER -->|"query embedding"| CHROMA
    CHROMA -->|"doc chunks"| P3_GATHER
    P3_GATHER -->|"equipment query"| SQLITE
    SQLITE -->|"time-series rows"| P3_GATHER
    P3_GATHER -->|"equipment_id"| GRAPH
    GRAPH -->|"connections"| P3_GATHER

    P3_GATHER --> P3_SYNTH
    P3_SYNTH <-->|"evidence → findings,<br/>findings → verification"| OLLAMA
    P3_SYNTH -->|"report, confidence,<br/>verification_status"| SQLITE

    P3_SYNTH --> P4_RPT
    P4_RPT -->|"report JSON"| USER

    USER -->|"export request"| P4_EXP
    P4_EXP -->|"PDF file"| EXPORTS
    P4_EXP -->|"download_url"| USER

    P3_PLAN -->|"audit entry (start)"| SQLITE
    P3_SYNTH -->|"audit entry (resolve)"| SQLITE
    USER -->|"GET audit-log"| P5_LOG
    P5_LOG -->|"entries"| SQLITE
    SQLITE -->|"audit entries"| P5_LOG
    P5_LOG -->|"paginated entries"| USER
```

---

### 3.3 Level 2 — Investigation Evidence Gathering (Detail)

```mermaid
flowchart TD
    subgraph "Input"
        QUERY["Investigation query text"]
        PLAN["Planner output: sub_tasks[]"]
    end

    subgraph "Document Agent"
        DA1["Extract equipment_ids<br/>via regex [A-Z]-\\d{2,4}"]
        DA2["Embed sub_task_goal<br/>→ 768-dim vector"]
        DA3["ChromaDB.query<br/>cosine similarity, top 10"]
        DA4["Post-filter: boost<br/>equipment match +0.5"]
        DA5["Return top 5<br/>DocumentChunk[]"]
    end

    subgraph "Data Agent"
        DTA1["Find first ready Dataset<br/>from SQLite"]
        DTA2["Resolve table_name:<br/>dataset_{id}"]
        DTA3["SQL: SELECT * FROM table<br/>WHERE equipment_id = ?<br/>AND metric = 'vibration'"]
        DTA4["pandas: sort by timestamp"]
        DTA5["Compute trend:<br/>first-half avg vs second-half avg"]
        DTA6["Compute pct_change:<br/>(last-first)/first * 100"]
        DTA7["Return DataAnalysisResult"]
    end

    subgraph "Vision Agent"
        VA1["Check graph_store<br/>.equipment_exists(id)"]
        VA2["Get predecessors<br/>+ successors"]
        VA3["Return connections[]<br/>confidence = 0.95"]
    end

    subgraph "RAG Agent"
        RA1["Augment query with<br/>'specification threshold limit'"]
        RA2["Embed → ChromaDB query"]
        RA3["Boost: equipment +0.4,<br/>manual/sop +0.3"]
        RA4["Extract §section via regex"]
        RA5["Return SpecChunk[]"]
    end

    subgraph "Assembly"
        BUNDLE["EvidenceBundle<br/>document_findings: DocumentChunk[]<br/>data_findings: DataAnalysisResult?<br/>vision_findings: VisionAnalysisResult?<br/>spec_findings: SpecChunk[]<br/>evidence_items: EvidenceItem[]"]
    end

    QUERY --> DA1 & DTA1 & VA1 & RA1
    PLAN --> DA1 & DTA1 & VA1 & RA1
    DA1 --> DA2 --> DA3 --> DA4 --> DA5
    DTA1 --> DTA2 --> DTA3 --> DTA4 --> DTA5 --> DTA6 --> DTA7
    VA1 --> VA2 --> VA3
    RA1 --> RA2 --> RA3 --> RA4 --> RA5

    DA5 & DTA7 & VA3 & RA5 --> BUNDLE
```

**Data labels on each edge:**

| Edge | Data Flowing |
|------|-------------|
| Query → Agents | `str` (natural language query) |
| Document Agent → ChromaDB | `List[float]` (768-dim embedding) |
| ChromaDB → Document Agent | `{chunk_id, chunk_text, source_id, page, score, metadata}` |
| Data Agent → SQLite | `SELECT * FROM dataset_XXX WHERE equipment_id=? AND metric=?` |
| SQLite → Data Agent | `pd.DataFrame` (timestamp, equipment_id, metric, value, unit) |
| Vision Agent → GraphStore | `str` (equipment_id) |
| GraphStore → Vision Agent | `List[str]` (connected equipment IDs) |
| All Agents → EvidenceBundle | Typed Pydantic models per agent contract |

---

## 4. Data Lifecycle & Security Notes

### 4.1 Sensitive Data Handled

| Data Type | Where Created | Where Stored | Sensitivity |
|-----------|--------------|-------------|-------------|
| User name + department | Session creation | SQLite `sessions` table, browser `sessionStorage` | Low — demo-grade, no passwords |
| Investigation queries | User input | SQLite `investigations.query`, `audit_log.query` | Medium — reveals plant concerns |
| Raw documents (PDFs, DOCX) | File upload | `./data/objects/{source_id}/` filesystem | High — proprietary plant data |
| Telemetry data | CSV upload | SQLite `dataset_*` tables | High — operational metrics |
| LLM prompts/responses | Investigation pipeline | Transient (in-memory only) | Medium — contain evidence excerpts |
| Audit log | Auto-generated | SQLite `audit_log` table | Medium — who queried what |

### 4.2 Authentication & Authorization Boundaries

```mermaid
flowchart LR
    subgraph "Frontend (Browser)"
        SS["sessionStorage<br/>kavachai_session_id"]
    end
    
    subgraph "API Layer"
        AUTH["getAuthHeaders()<br/>Authorization: Bearer session_id"]
        CORS["CORS: localhost:3000 only"]
    end

    subgraph "Backend"
        VALIDATE["Session validation:<br/>ONLY on POST /investigations<br/>(checks session_id exists in DB)"]
        NO_AUTH["All other endpoints:<br/>NO authentication check"]
    end

    SS --> AUTH --> VALIDATE
    
    style NO_AUTH fill:#fbbf24,color:#1e1e1e
```

> [!WARNING]
> **No real authentication exists.** The `session_id` is stored in `sessionStorage` and sent as a Bearer token, but the backend only validates it on `POST /investigations` (line 88-94 of [investigations.py](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/routers/investigations.py#L88-L94)). All other endpoints (knowledge-base, evidence, export, audit) have **zero auth checks**. The `deps.py` file is a placeholder with no actual dependencies implemented.

### 4.3 Data Persistence Locations

| Store | Technology | Path | Persistence |
|-------|-----------|------|-------------|
| Relational data | SQLite (async via aiosqlite) | `./data/kavachai.db` | Persistent, WAL mode |
| Vector embeddings | ChromaDB (PersistentClient) | `./data/chroma/` | Persistent, HNSW cosine |
| Raw source files | Local filesystem | `./data/objects/{source_id}/` | Persistent |
| Equipment graph | NetworkX (in-memory) | N/A | **Volatile** — rebuilt on each startup with hardcoded 4-node demo graph |
| PDF exports | Local filesystem | `./data/exports/` | Persistent, no cleanup |
| Investigation runners | Python dict (in-memory) | `_runners` in investigations.py | **Volatile** — lost on restart |
| Session data (frontend) | Browser sessionStorage | N/A | Per-tab, cleared on tab close |

### 4.4 External Data Sharing

> [!IMPORTANT]
> **Zero external data transmission by design (NFR-SEC-1).** All LLM inference runs through the local Ollama server at `localhost:11434`. The `ModelRouter` is the single chokepoint — no agent imports `httpx` or calls any external endpoint directly. ChromaDB telemetry is explicitly disabled (`anonymized_telemetry=False`).

### 4.5 Potential Gaps, Ambiguities & Risks

| # | Category | Finding | Severity | Source |
|---|----------|---------|----------|--------|
| 1 | **Auth** | No authentication on knowledge-base, evidence, export, or audit endpoints. `deps.py` is empty placeholder. | 🔴 High | [deps.py](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/deps.py) |
| 2 | **Auth** | Session validation only checks existence, not expiry. Sessions never expire or get revoked. | 🟡 Medium | [investigations.py L88-L94](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/routers/investigations.py#L88-L94) |
| 3 | **State** | `_runners` dict is in-memory — SSE will break if backend restarts mid-investigation. | 🟡 Medium | [investigations.py L31](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/routers/investigations.py#L31) |
| 4 | **Hardcoded** | Evidence router hardcodes `"P-102"` for dataset and P&ID queries (marked with `# TODO: parameterize`). | 🟡 Medium | [evidence.py L74, L87](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/routers/evidence.py#L74) |
| 5 | **Hardcoded** | Data Agent defaults to `metric="vibration"` — not derived from the planner's sub-task goal. | 🟡 Medium | [investigation.py L238](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/orchestrator/investigation.py#L238) |
| 6 | **Audit** | `resolve_audit_entry` performs an UPDATE on `audit_log`, contradicting the "append-only" claim (FR-AUD-2). The table technically allows updates via the ORM even though no PATCH API exists. | 🟡 Medium | [audit_service.py L42-L71](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/services/audit_service.py#L42-L71) |
| 7 | **Offline** | Offline fallback in `model_router._offline_generate` returns hardcoded JSON for exactly 3 demo scenarios. Any other query gets generic stub responses. | 🟡 Medium | [model_router.py L236-L349](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/orchestrator/model_router.py#L236-L349) |
| 8 | **Concurrency** | `TabularStore` uses synchronous `sqlite3` directly (not the async engine), potentially blocking the event loop on large datasets. | 🟡 Medium | [tabular_store.py L28-L31](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/db/tabular_store.py#L28-L31) |
| 9 | **Cleanup** | No cleanup mechanism for exported PDFs in `./data/exports/`. Files accumulate indefinitely. | 🟢 Low | [export.py L21-L22](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/routers/export.py#L21-L22) |
| 10 | **Graph** | Equipment graph is hardcoded to 4 demo nodes. No API or ingestion path to add new equipment relationships. | 🟢 Low | [graph_store.py L20-L37](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/db/graph_store.py#L20-L37) |
| 11 | **SQL Injection** | `tabular_store.query_by_equipment` uses f-string for table name in SQL. Table names come from controlled `dataset_id`, but the pattern is fragile. | 🟢 Low | [tabular_store.py L83](file:///c:/Users/HP/Desktop/SIH/KavachAI/backend/app/db/tabular_store.py#L83) |

---

## 5. Architecture Findings Summary

### Main Flows

| Flow | Trigger | Key Components | Terminal States |
|------|---------|----------------|-----------------|
| **Session** | User login | Frontend → Session Router → SQLite | Session created |
| **Doc Ingestion** | File upload | Router → Extract → Chunk → Tag → Embed → ChromaDB | ready / failed |
| **Dataset Ingestion** | CSV upload | Router → pandas → TabularStore → SQLite table | ready / failed |
| **Investigation** | Query submit | Router → Background → Planner → [Doc∥Data∥Vision] → RAG → Synthesis → Verification → Report | complete / insufficient_evidence / failed |
| **SSE Stream** | Frontend EventSource | Polling `_runners.events[]` + DB status check | investigation_complete / insufficient_evidence |
| **Export** | Export button | Router → ReportLab PDF → FileResponse | PDF download |
| **Audit** | Auto (investigation lifecycle) | Two-write: create on start, resolve on end | Append-only read via GET |

### Key Dependencies

| Dependency | Role | Required? |
|-----------|------|-----------|
| **Ollama (Qwen 2.5 3B)** | Text reasoning, planning, synthesis, verification | No — offline fallback exists |
| **Ollama (nomic-embed-text)** | 768-dim embeddings for vector search | No — pseudo-embed fallback exists |
| **SQLite + aiosqlite** | Primary relational store | Yes |
| **ChromaDB** | Vector similarity search | Yes |
| **PyMuPDF (fitz)** | PDF text extraction & page rendering | Yes (for PDF files) |
| **NetworkX** | Equipment relationship graph | Yes (hardcoded data) |
| **ReportLab** | PDF export generation | Yes (for export feature) |

### Key Design Decisions Visible in Code

1. **Single Model Router chokepoint** — All LLM/embedding calls route through `model_router.py`. No agent directly calls Ollama. Enables model-swap-by-config.
2. **Data Agent uses pure pandas** — Zero LLM calls for numeric analysis. The LLM "never does arithmetic."
3. **Vision Agent is pre-computed** — Uses a hardcoded NetworkX graph instead of a live VLM. Contract is identical so VLM can be swapped in later.
4. **Audit is append-only at API layer** — No DELETE/PATCH endpoints exist, though the ORM technically allows updates (used for the two-write resolve pattern).
5. **Investigation survives SSE disconnect** — BackgroundTasks runs server-side; report is persisted to DB and fetchable via `GET /report` even if SSE was never connected.

### Areas Needing Clarification

1. **Department-scope filtering** — `FR-RAG-2` interface exists but enforcement is simplified. The `department_scope` filter is passed to ChromaDB but there's no middleware preventing cross-department access.
2. **Multi-user concurrency** — No locking on investigations. Multiple users could theoretically trigger investigations that share the same `_runners` dict.
3. **Corpus ingestion path** — The `ingest_corpus.py` script is the only way to seed the demo corpus. The API upload endpoints work but are not connected to the suggested questions UI.
4. **Frontend routing for `/investigation/[id]` and `/report/[id]`** — Directory structure exists but page content was not fully inspected in this analysis.
