"""
KavachAI — Knowledge Base Router
Implements: FR-ING-1..7 (document/dataset ingestion), Equipment Graph Management
Endpoints: API_Reference.md §3
    POST /knowledge-base/documents
    GET  /knowledge-base/documents/{document_id}
    POST /knowledge-base/datasets
    GET  /knowledge-base/summary
    POST /knowledge-base/graph/nodes
    POST /knowledge-base/graph/edges
    GET  /knowledge-base/graph
"""

import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List

from app.db.database import get_db
from app.db.sql_models import Document, Dataset, Session as SessionModel
from app.db.object_store import object_store
from app.db.vector_store import vector_store
from app.db.graph_store import graph_store
from app.ingestion.extract import extract_text, get_page_count
from app.ingestion.chunk import chunk_pages
from app.ingestion.tag import tag_chunks
from app.ingestion.embed import generate_embeddings
from app.ingestion.tabular import parse_tabular_file
from app.models.ingestion import (
    DocumentUploadResponse,
    DocumentDetailResponse,
    DatasetUploadResponse,
    KnowledgeBaseSummary,
    GraphNodeCreate,
    GraphEdgeCreate,
    GraphResponse,
)
from app.deps import get_current_session

router = APIRouter(prefix="/api/v1/knowledge-base", tags=["knowledge-base"])


@router.post("/documents", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    equipment_ids: Optional[str] = Form(None),  # JSON string: '["P-102"]'
    department_scope: Optional[str] = Form(None),
    current_session: SessionModel = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload and ingest a document.
    Implements: FR-ING-1..6
    """
    import json

    # Parse equipment_ids from JSON string
    equip_ids = []
    if equipment_ids:
        try:
            equip_ids = json.loads(equipment_ids)
        except json.JSONDecodeError:
            equip_ids = [equipment_ids]

    safe_filename = Path(file.filename.replace("\\", "/")).name or "file"
    source_id = f"doc_{uuid.uuid4().hex[:8]}"
    file_content = await file.read()

    # Save raw file to object store (FR-ING-6)
    object_store.save_raw_file(source_id, file_content, safe_filename)

    # Create document record
    page_count = get_page_count(file_content, safe_filename)
    doc = Document(
        filename=safe_filename,
        document_type=document_type,
        status="processing",
        pages=page_count,
        equipment_ids=equip_ids,
        department_scope=department_scope,
        source_id=source_id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Run ingestion pipeline (FR-ING-2..5)
    try:
        # Extract text (FR-ING-2)
        pages = extract_text(file_content, safe_filename)

        if pages:
            # Chunk text (FR-ING-3)
            chunks = chunk_pages(pages)

            # Tag chunks with metadata (FR-ING-4)
            tagged_chunks = tag_chunks(
                chunks, source_id, safe_filename,
                document_type, equip_ids, department_scope,
            )

            # Generate embeddings (FR-ING-5)
            texts = [c["text"] for c in tagged_chunks]
            embeddings = await generate_embeddings(texts)

            # Store in vector DB
            chunk_ids = [f"{source_id}_chunk_{i}" for i in range(len(tagged_chunks))]
            metadatas = [c["metadata"] for c in tagged_chunks]
            vector_store.upsert_chunks(chunk_ids, texts, embeddings, metadatas)

            # Update document status
            doc.status = "ready"
            doc.chunks = len(tagged_chunks)
        else:
            # No text extracted (might be an image/PID)
            doc.status = "ready"
            doc.chunks = 0

        await db.commit()

    except Exception as e:
        doc.status = "failed"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    return DocumentUploadResponse(
        document_id=doc.id,
        status=doc.status,
        chunks_expected=True,
    )


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    current_session: SessionModel = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Get document ingestion status and metadata.
    Implements: FR-ING-1 (status tracking)
    """
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentDetailResponse(
        document_id=doc.id,
        filename=doc.filename,
        document_type=doc.document_type,
        status=doc.status,
        pages=doc.pages,
        chunks=doc.chunks,
        equipment_ids=doc.equipment_ids or [],
        ingested_at=doc.ingested_at.isoformat() + "Z",
    )


@router.post("/datasets", response_model=DatasetUploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    current_session: SessionModel = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a structured time-series dataset.
    Implements: FR-ING-7
    """
    safe_filename = Path(file.filename.replace("\\", "/")).name or "file"
    dataset_id = f"ds_{uuid.uuid4().hex[:4]}"
    file_content = await file.read()

    # Save raw file to object store
    source_id = dataset_id
    object_store.save_raw_file(source_id, file_content, safe_filename)

    try:
        result = parse_tabular_file(file_content, safe_filename, dataset_id)

        ds = Dataset(
            id=dataset_id,
            filename=safe_filename,
            columns=result["columns"],
            row_count=result["row_count"],
            status="ready",
            table_name=result["table_name"],
        )
        db.add(ds)
        await db.commit()

        return DatasetUploadResponse(
            dataset_id=dataset_id,
            columns=result["columns"],
            row_count=result["row_count"],
            status="ready",
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dataset ingestion failed: {str(e)}")


@router.get("/summary", response_model=KnowledgeBaseSummary)
async def get_summary(
    current_session: SessionModel = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Get corpus overview for the workspace footer.
    Implements: API_Reference.md §3 GET /knowledge-base/summary
    """
    # Count documents (excluding PID drawings)
    doc_result = await db.execute(
        select(func.count(Document.id)).where(
            Document.status == "ready",
            Document.document_type != "pid_drawing",
        )
    )
    doc_count = doc_result.scalar() or 0

    # Count PID drawings
    pid_result = await db.execute(
        select(func.count(Document.id)).where(
            Document.status == "ready",
            Document.document_type == "pid_drawing",
        )
    )
    pid_count = pid_result.scalar() or 0

    # Count datasets
    ds_result = await db.execute(
        select(func.count(Dataset.id)).where(Dataset.status == "ready")
    )
    ds_count = ds_result.scalar() or 0

    return KnowledgeBaseSummary(
        documents=doc_count,
        datasets=ds_count,
        pid_drawings=pid_count,
    )


# --- Equipment Graph Management Endpoints ---

@router.post("/graph/nodes", status_code=201)
async def add_graph_node(
    body: GraphNodeCreate,
    current_session: SessionModel = Depends(get_current_session),
):
    """Add or update an equipment node in the topological graph."""
    graph_store.add_node(
        equipment_id=body.equipment_id,
        equipment_type=body.equipment_type,
        label=body.label,
    )
    return {"status": "created", "node": graph_store.get_equipment_info(body.equipment_id)}


@router.post("/graph/edges", status_code=201)
async def add_graph_edge(
    body: GraphEdgeCreate,
    current_session: SessionModel = Depends(get_current_session),
):
    """Add or update a directed relationship edge between equipment nodes."""
    graph_store.add_edge(
        from_id=body.from_id,
        to_id=body.to_id,
        relationship=body.relationship,
        label=body.label,
    )
    return {"status": "created", "edge": {"from": body.from_id, "to": body.to_id, "relationship": body.relationship}}


@router.get("/graph", response_model=GraphResponse)
async def get_graph(current_session: SessionModel = Depends(get_current_session)):
    """Retrieve full equipment relationship graph."""
    return GraphResponse(
        nodes=graph_store.get_all_nodes(),
        edges=graph_store.get_all_edges(),
    )
