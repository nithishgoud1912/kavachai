# Technical Architecture Specification: Multi-Agent RAG & Industrial Analytics System

## Document Metadata
| Attribute | Value |
| :--- | :--- |
| **Document Title** | Technical Architecture & System Implementation Specification |
| **System Category** | Multi-Agent RAG & Industrial Knowledge Platform |
| **Environment Lifecycle** | Prototype (Phase 1–4) → Production Scale Target |
| **Document Version** | 1.0.0 |
| **Status** | Approved Specification |

---

## Executive Summary
This document provides the standard technical architecture specification for an enterprise-grade, multi-agent Retrieval-Augmented Generation (RAG) and industrial data analytics system. The architecture integrates vector storage, relational session and metadata tracking, structured time-series metric analysis, graph-based topological relationship tracking, and an immutable raw object store.

---

## Phase 1: Architecture & Technology Selection

### 1.1 Technology Selection Matrix

| Subsystem | Prototype Environment | Production Roadmap Target | Core Function & Technical Rationale |
| :--- | :--- | :--- | :--- |
| **Vector Database** | ChromaDB / FAISS | ChromaDB / Milvus / Qdrant | Dense vector storage and similarity search over overlapping text chunks and document embeddings. |
| **Relational Database** | SQLite | PostgreSQL | User account management, active session state, document metadata, and append-only audit logging. |
| **Structured Time-Series Store** | SQLite / Parquet | TimescaleDB / PostgreSQL | Robust schema for parsed tabular data tracking plant metrics and telemetry trends. |
| **Graph Store** | NetworkX | Neo4j | Equipment relationships and topological network mapping populated by the Vision Agent. |
| **Object Store** | Local File System (`/storage/raw/`) | AWS S3 / MinIO Object Store | Retains original raw files (PDF, DOCX, TXT, CSV, PNG, JPG) addressable directly by `source_id` for UI rendering. |

### 1.2 Subsystem Topology

```
                                  +---------------------------------------+
                                  |       Ingestion & API Gateway         |
                                  +-------------------+-------------------+
                                                      |
         +-------------------+------------------------+-----------------------+-------------------+
         |                   |                        |                       |                   |
         v                   v                        v                       v                   v
  +--------------+    +--------------+         +--------------+        +--------------+    +--------------+
  | Object Store |    |  Vector DB   |         | Relational DB|        | Time-Series  |    |  Graph Store |
  | (Local / S3) |    |(Chroma/FAISS)|         |(SQLite/Postgres)      |(SQLite/Timescale) |(NetworkX/Neo4j)
  +--------------+    +--------------+         +--------------+        +--------------+    +--------------+
  | Raw PDFs,    |    | Overlapping  |         | Users,       |        | Plant        |    | Equipment    |
  | Images,      |    | Chunks &     |         | Sessions,    |        | Metrics,     |    | Topology &   |
  | Spec Files   |    | Embeddings   |         | Metadata     |        | Telemetry    |    | Graph Nodes  |
  +--------------+    +--------------+         +--------------+        +--------------+    +--------------+
```

---

## Phase 2: Schema Design & Indexing Optimization

### 2.1 Structured Time-Series Schema

The time-series store uses a standardized schema engineered for deterministic metric extraction and high-speed trend analysis.

#### DDL Definition (SQL)
```sql
CREATE TABLE plant_metrics (
    metric_id BIGINT PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    equipment_id VARCHAR(64) NOT NULL,
    metric VARCHAR(64) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(16) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexing for optimized multi-column time-series range queries
CREATE INDEX idx_plant_metrics_lookup 
ON plant_metrics (equipment_id, metric, timestamp DESC);
```

### 2.2 Static Hashing Implementation

To satisfy high-velocity retrieval demands from the Data and Knowledge Agents:
- **Primary Lookup Keys**: Static hashing structures are implemented on high-frequency primary keys, specifically `equipment_id` and `investigation_id`.
- **Access Complexity**: Guarantees $O(1)$ bucketed access for the most frequent relational and structured queries.
- **Operational Advantage**: Eliminates dynamic re-indexing overhead during live, high-throughput investigation sessions.

### 2.3 Metadata Tagging & Coupling

Relational metadata tables are tightly bound to vector database chunks to facilitate granular, multi-tenant context retrieval.

#### Metadata Structure Example (JSON)
```json
{
  "chunk_id": "chk_98f12a4c",
  "source_id": "doc_2026_sop_089",
  "source_document_name": "Turbine_Maintenance_Standard_Operating_Procedure.pdf",
  "page_number": 14,
  "document_type": "SOP",
  "date": "2026-03-15",
  "department_scope": "Operations_Turbine_Hall",
  "equipment_ids": ["TURB-001", "VALVE-104", "PUMP-012"]
}
```

---

## Phase 3: Ingestion Pipeline Integration

### 3.1 Pipeline Processing Flow

```
   Incoming File (PDF / DOCX / CSV / Image)
                     |
                     v
   +------------------------------------+
   |     Raw Object Store Persistence   |   <--- Guaranteed Immutability
   |     (Retains original source_id)   |        (Direct Source Viewer Link)
   +-----------------+------------------+
                     |
         +-----------+-----------+
         |                       |
         v                       v
[Unstructured Pathway]  [Structured Pathway]
         |                       |
         v                       v
  PyMuPDF Extraction      Tabular Parsing (Pandas)
  Chunking & Local        Column Semantics Mapping
  Inference Embeddings          |
         |                       v
         v               Time-Series Schema Insert
  Vector DB Storage
  with Metadata Tags
```

### 3.2 Ingestion Phase Rules
1. **Unstructured Data Pipeline**:
   - Incoming text and PDF files are routed through a `PyMuPDF` extraction engine.
   - Text is split into overlapping semantic chunks.
   - Vector embeddings are calculated via the local inference model.
   - Embeddings and metadata tags are stored in the Vector DB (ChromaDB/FAISS).
2. **Structured Data Pipeline**:
   - Tabular files (CSV, XLSX) are parsed directly into the structured time-series schema.
   - Exact column semantics (`timestamp`, `equipment_id`, `metric`, `value`, `unit`) are rigorously validated and preserved.
3. **Immutability Guarantee**:
   - Raw files are immediately written to local file-system object storage **prior** to any chunking or parsing operations.
   - This ensures the UI Source Viewer can always display the original, unaltered evidence referencing any specific `source_id`.

---

## Phase 4: Agent Query Execution Setup

### 4.1 Vector Search & Filtering (Document Agent)
- Exposes API endpoints allowing the **Document Agent** to run k-Nearest Neighbor (k-NN) similarity searches against vector embeddings.
- Applies strict hard metadata filters at query time to constrain search spaces by `department_scope` and target `equipment_id` lists.

### 4.2 Deterministic Analytics (Data Agent)
- Provides the **Data Agent** direct query access to the structured time-series database via Python `pandas` integrations.
- **LLM Isolation**: All arithmetic, statistical calculations, and trend estimations are strictly executed programmatically in Python/SQL, isolating computational work entirely from LLM generation.

### 4.3 Append-Only Audit Trail

To preserve regulatory integrity and investigation transparency, the audit table operates on an append-only enforcement protocol.

#### Enforcement & Lifecycle
- **API Prohibition**: All `DELETE` and `PATCH` requests are rejected at the API gateway layer.
- **Two-Step Write Process**:
  1. **Step 1 (Investigation Creation)**: Captures `user_id`, `timestamp`, `investigation_id`, and initial `query_text`.
  2. **Step 2 (Investigation Resolution)**: Appends a resolution log entry capturing `agents_invoked`, `verification_status`, and `confidence_score`.

#### Audit Trail Schema DDL
```sql
CREATE TABLE audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investigation_id VARCHAR(64) NOT NULL,
    lifecycle_phase VARCHAR(16) NOT NULL CHECK (lifecycle_phase IN ('CREATION', 'RESOLUTION')),
    user_id VARCHAR(64) NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    query_text TEXT,
    agents_invoked TEXT, -- JSON formatted array of agent identifiers
    verification_status VARCHAR(32),
    confidence_score DOUBLE PRECISION,
    checksum_hash VARCHAR(64)
);

CREATE INDEX idx_audit_investigation ON audit_log (investigation_id);
```

---

## System Architecture Summary Matrix

```
+-----------------------------------------------------------------------------------+
|                            Multi-Agent Execution Layer                            |
|    +-------------------+   +-----------------+   +----------------------------+   |
|    |  Document Agent   |   |   Data Agent    |   |  Vision / Knowledge Agent  |   |
|    +---------+---------+   +--------+--------+   +-------------+--------------+   |
+--------------|----------------------|--------------------------|------------------+
               | Vector               | Structured Pandas        | Graph Queries
               v                      v                          v
+------------------------+  +--------------------+  +-------------------------------+
|  ChromaDB / FAISS      |  | Time-Series Store  |  | NetworkX / Neo4j              |
|  (Filtered Vector Search) |  | (Deterministic)   |  | (Equipment Relationships)     |
+------------------------+  +--------------------+  +-------------------------------+
               ^                      ^                          ^
               |                      |                          |
+--------------+----------------------v--------------------------+------------------+
|                            Ingestion & Object Storage                             |
|  +-----------------------------------------------------------------------------+  |
|  | Immutable Local Raw File Storage (PDF, CSV, PNG, DOCX)                      |  |
|  | Traceable via source_id                                                     |  |
|  +-----------------------------------------------------------------------------+  |
|                            Relational Database & Audit                            |
|  +-----------------------------------------------------------------------------+  |
|  | SQLite / PostgreSQL (Users, Sessions, Metadata, Append-Only Audit Trail)     |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
