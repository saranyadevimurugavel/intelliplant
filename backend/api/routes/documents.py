"""Document ingestion and management API routes."""
import os
import uuid
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from core.database import get_db, Document
from core.config import settings
from core.auth import get_current_user, require_role, has_permission
from services.document_processor import process_document
from core.knowledge_graph import get_graph_stats

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".xls", ".csv", ".jpg", ".jpeg",
                      ".png", ".tiff", ".tif", ".bmp", ".txt", ".msg", ".eml"}


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = Form(default="general"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Upload and queue a document for processing."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not supported.")

    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}{ext}"
    file_path = os.path.join(settings.upload_dir, safe_filename)

    # Save file
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # Determine doc_type
    doc_type_map = {
        ".pdf": "pdf", ".docx": "docx", ".xlsx": "spreadsheet",
        ".xls": "spreadsheet", ".csv": "spreadsheet",
        ".jpg": "image", ".jpeg": "image", ".png": "image",
        ".tiff": "image", ".tif": "image", ".bmp": "image",
        ".msg": "email", ".eml": "email", ".txt": "text",
    }
    doc_type = doc_type_map.get(ext, "other")

    # Save to DB
    doc = Document(
        id=doc_id,
        filename=safe_filename,
        original_name=file.filename,
        doc_type=doc_type,
        category=category,
        file_path=file_path,
        file_size=len(content),
        status="pending",
    )
    db.add(doc)
    await db.commit()

    # Process in background
    background_tasks.add_task(
        _process_and_update, doc_id, file_path, file.filename, doc_type, category
    )

    return {
        "document_id": doc_id,
        "filename": file.filename,
        "status": "processing",
        "message": "Document uploaded and queued for processing.",
    }


async def _process_and_update(doc_id, file_path, original_name, doc_type, category):
    """Background task: process document and update DB."""
    from core.database import AsyncSessionLocal
    result = await process_document(doc_id, file_path, original_name, doc_type, category)
    async with AsyncSessionLocal() as db:
        doc = await db.get(Document, doc_id)
        if doc:
            doc.status = result.get("status", "failed")
            doc.page_count = result.get("page_count")
            doc.entities = result.get("entities")
            doc.summary = result.get("summary")
            doc.extracted_text = None  # Don't store full text in DB
            doc.processed_at = datetime.now(timezone.utc)
            await db.commit()


@router.get("/")
async def list_documents(
    category: str = None,
    status: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List all documents with optional filters."""
    query = select(Document).order_by(Document.created_at.desc())
    result = await db.execute(query)
    docs = result.scalars().all()

    if category:
        docs = [d for d in docs if d.category == category]
    if status:
        docs = [d for d in docs if d.status == status]

    return [
        {
            "id": d.id,
            "filename": d.original_name,
            "doc_type": d.doc_type,
            "category": d.category,
            "status": d.status,
            "page_count": d.page_count,
            "summary": d.summary,
            "entities": d.entities,
            "file_size": d.file_size,
            "created_at": d.created_at,
            "processed_at": d.processed_at,
        }
        for d in docs
    ]


@router.get("/{document_id}")
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single document's details."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {
        "id": doc.id,
        "filename": doc.original_name,
        "doc_type": doc.doc_type,
        "category": doc.category,
        "status": doc.status,
        "page_count": doc.page_count,
        "summary": doc.summary,
        "entities": doc.entities,
        "file_size": doc.file_size,
        "created_at": doc.created_at,
        "processed_at": doc.processed_at,
    }


@router.get("/stats/knowledge-graph")
async def knowledge_graph_stats():
    """Get knowledge graph statistics."""
    return get_graph_stats()


@router.get("/graph/entity/{entity_id}")
async def get_entity(entity_id: str):
    """Get a knowledge graph entity and its neighbors."""
    from core.knowledge_graph import get_entity, get_neighbors
    entity = get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found in knowledge graph.")
    neighbors = get_neighbors(entity_id)
    return {"entity_id": entity_id, "attributes": entity, "neighbors": neighbors}


@router.get("/graph/search")
async def search_knowledge_graph(q: str, node_type: str = None):
    """Search the knowledge graph for entities."""
    from core.knowledge_graph import search_entities
    results = search_entities(q, node_type)
    return {"query": q, "results": results}
