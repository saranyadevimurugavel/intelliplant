"""
Document Processing Pipeline
Handles: PDF, DOCX, Excel/CSV, images (OCR), email archives
Extracts text, entities, and chunks for vector store ingestion.
"""
import os
import re
import uuid
import logging
from typing import List, Tuple
from datetime import datetime, timezone

import fitz  # PyMuPDF
from PIL import Image
import pytesseract

from core.config import settings
from core.embeddings import embed_texts
from core.vector_store import add_chunks, delete_document_chunks
from core.knowledge_graph import add_entity, add_relationship

logger = logging.getLogger(__name__)

# Industrial entity patterns
EQUIPMENT_TAG_PATTERN = re.compile(
    r'\b([A-Z]{1,4}-[A-Z0-9]{2,6}(?:-[A-Z0-9]+)?)\b'
)
PARAMETER_PATTERN = re.compile(
    r'\b(\d+(?:\.\d+)?)\s*(°C|bar|kPa|MPa|kg/hr|m3/hr|rpm|kW|MW|%|ppm|pH)\b'
)
WORK_ORDER_PATTERN = re.compile(r'\b(WO[-\s]?\d{4,8})\b', re.IGNORECASE)
DATE_PATTERN = re.compile(
    r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b'
)
REGULATION_PATTERN = re.compile(
    r'\b(OISD[-\s]?(?:STD[-\s]?)?\d+|PESO\s+\w+|Factories Act|IS\s+\d+|ISO\s+\d+|CPCB|BIS\s+\d+)\b',
    re.IGNORECASE,
)


def extract_text_from_pdf(file_path: str) -> Tuple[str, int]:
    """Extract text from PDF; fallback to OCR for scanned pages."""
    doc = fitz.open(file_path)
    pages_text = []
    for page in doc:
        text = page.get_text()
        if len(text.strip()) < 50:  # likely scanned
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img)
        pages_text.append(text)
    doc.close()
    return "\n\n".join(pages_text), len(pages_text)


def extract_text_from_image(file_path: str) -> Tuple[str, int]:
    """OCR an image file."""
    img = Image.open(file_path)
    text = pytesseract.image_to_string(img)
    return text, 1


def extract_text_from_docx(file_path: str) -> Tuple[str, int]:
    """Extract text from DOCX."""
    from docx import Document
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs), 1


def extract_text_from_spreadsheet(file_path: str) -> Tuple[str, int]:
    """Convert spreadsheet rows to readable text."""
    import pandas as pd
    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path, dtype=str)
        else:
            df = pd.read_excel(file_path, dtype=str)
        text = df.to_string(index=False)
        return text, 1
    except Exception as e:
        logger.warning(f"Spreadsheet extraction error: {e}")
        return "", 1


def extract_text(file_path: str, doc_type: str) -> Tuple[str, int]:
    """Route to correct extractor based on doc_type."""
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".pdf":
            return extract_text_from_pdf(file_path)
        elif ext in (".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"):
            return extract_text_from_image(file_path)
        elif ext == ".docx":
            return extract_text_from_docx(file_path)
        elif ext in (".xlsx", ".xls", ".csv"):
            return extract_text_from_spreadsheet(file_path)
        else:
            # Plain text fallback
            with open(file_path, "r", errors="ignore") as f:
                return f.read(), 1
    except Exception as e:
        logger.error(f"Text extraction failed for {file_path}: {e}")
        return "", 0


def extract_entities(text: str) -> dict:
    """Extract industrial entities from text using regex patterns."""
    equipment_tags = list(set(EQUIPMENT_TAG_PATTERN.findall(text)))
    parameters = []
    for match in PARAMETER_PATTERN.finditer(text):
        parameters.append(f"{match.group(1)} {match.group(2)}")
    work_orders = list(set(WORK_ORDER_PATTERN.findall(text)))
    dates = list(set(DATE_PATTERN.findall(text)))
    regulations = list(set(REGULATION_PATTERN.findall(text)))

    return {
        "equipment_tags": equipment_tags[:20],
        "process_parameters": list(set(parameters))[:20],
        "work_orders": work_orders[:10],
        "dates": dates[:10],
        "regulations": regulations[:10],
    }


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    """Split text into overlapping chunks for embedding."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


async def process_document(
    document_id: str,
    file_path: str,
    original_name: str,
    doc_type: str,
    category: str,
) -> dict:
    """
    Full processing pipeline for a single document.
    Returns extracted metadata dict.
    """
    logger.info(f"Processing document {document_id}: {original_name}")

    # 1. Extract text
    text, page_count = extract_text(file_path, doc_type)
    if not text:
        return {"status": "failed", "error": "No text extracted"}

    # 2. Extract entities
    entities = extract_entities(text)

    # 3. Generate a simple summary (first 500 chars of text)
    summary = text[:500].strip().replace("\n", " ")

    # 4. Chunk text for vector store
    chunks = chunk_text(text)
    if not chunks:
        return {"status": "failed", "error": "No chunks generated"}

    # 5. Remove old chunks (safe re-ingestion)
    delete_document_chunks(document_id)

    # 6. Generate embeddings
    embeddings = embed_texts(chunks)

    # 7. Store in vector store
    chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "document_id": document_id,
            "filename": original_name,
            "doc_type": doc_type,
            "category": category,
            "chunk_index": i,
        }
        for i in range(len(chunks))
    ]
    add_chunks(chunks, metadatas, chunk_ids, embeddings)

    # 8. Update knowledge graph
    add_entity(
        f"DOC-{document_id[:8].upper()}",
        "document",
        name=original_name,
        document_id=document_id,
        doc_type=doc_type,
        category=category,
        summary=summary[:200],
        processed_at=datetime.now(timezone.utc).isoformat(),
    )
    # Link document to extracted equipment tags
    for tag in entities.get("equipment_tags", []):
        node_id = tag.upper()
        if node_id not in ["", "N/A"]:
            add_entity(node_id, "asset", name=tag, source="auto_extracted")
            add_relationship(f"DOC-{document_id[:8].upper()}", node_id, "references_asset")

    return {
        "status": "ready",
        "page_count": page_count,
        "chunk_count": len(chunks),
        "entities": entities,
        "summary": summary,
    }
