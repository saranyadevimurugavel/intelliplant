"""
Lightweight in-memory vector store using numpy.
No ChromaDB dependency — works on Render free tier instantly.
Persists to a JSON file for durability across restarts.
"""
import json
import os
import logging
import numpy as np
from typing import List, Optional
from core.config import settings

logger = logging.getLogger(__name__)

STORE_PATH = None  # set on first use
_store: dict = {"chunks": [], "embeddings": [], "metadatas": []}
COLLECTION_NAME = "intelliplant_docs"


def _get_store_path() -> str:
    global STORE_PATH
    if STORE_PATH is None:
        STORE_PATH = os.path.join(settings.chroma_dir, "vector_store.json")
    return STORE_PATH


def _load_store():
    global _store
    path = _get_store_path()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                _store = json.load(f)
            logger.info(f"Vector store loaded: {len(_store['chunks'])} chunks")
        except Exception as e:
            logger.warning(f"Could not load vector store: {e}")
            _store = {"chunks": [], "embeddings": [], "metadatas": []}
    else:
        _store = {"chunks": [], "embeddings": [], "metadatas": []}


def _save_store():
    os.makedirs(settings.chroma_dir, exist_ok=True)
    path = _get_store_path()
    with open(path, "w") as f:
        json.dump(_store, f)


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    dot = np.dot(va, vb)
    norm = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(dot / norm) if norm > 0 else 0.0


def add_chunks(
    chunks: List[str],
    metadatas: List[dict],
    ids: List[str],
    embeddings: List[List[float]],
):
    """Add text chunks to the in-memory store."""
    if not _store["chunks"]:
        _load_store()
    for chunk, meta, emb in zip(chunks, metadatas, embeddings):
        _store["chunks"].append(chunk)
        _store["metadatas"].append(meta)
        _store["embeddings"].append(emb)
    _save_store()
    logger.info(f"Added {len(chunks)} chunks. Total: {len(_store['chunks'])}")


def query_similar(
    query_embedding: List[float],
    n_results: int = 5,
    where: Optional[dict] = None,
) -> dict:
    """Find most similar chunks using cosine similarity."""
    if not _store["chunks"]:
        _load_store()

    if not _store["chunks"]:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    # Filter by metadata if where clause provided
    indices = []
    for i, meta in enumerate(_store["metadatas"]):
        if where:
            match = all(meta.get(k) == v for k, v in where.items())
            if not match:
                continue
        indices.append(i)

    if not indices:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    # Compute similarities
    scored = []
    for i in indices:
        sim = _cosine_similarity(query_embedding, _store["embeddings"][i])
        scored.append((sim, i))

    # Sort by similarity descending
    scored.sort(key=lambda x: -x[0])
    top = scored[:n_results]

    docs, metas, dists = [], [], []
    for sim, i in top:
        docs.append(_store["chunks"][i])
        metas.append(_store["metadatas"][i])
        dists.append(1.0 - sim)  # convert similarity to distance

    return {
        "documents": [docs],
        "metadatas": [metas],
        "distances": [dists],
    }


def delete_document_chunks(document_id: str):
    """Remove all chunks for a document."""
    if not _store["chunks"]:
        _load_store()
    keep = [i for i, m in enumerate(_store["metadatas"]) if m.get("document_id") != document_id]
    _store["chunks"] = [_store["chunks"][i] for i in keep]
    _store["metadatas"] = [_store["metadatas"][i] for i in keep]
    _store["embeddings"] = [_store["embeddings"][i] for i in keep]
    _save_store()


def get_collection_stats() -> dict:
    if not _store["chunks"]:
        _load_store()
    return {"total_chunks": len(_store["chunks"]), "collection_name": COLLECTION_NAME}
