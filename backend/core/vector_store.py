"""
ChromaDB vector store wrapper for RAG retrieval.
"""
import logging
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from core.config import settings

logger = logging.getLogger(__name__)

# Singleton chroma client
_client: Optional[chromadb.PersistentClient] = None
_collection = None
COLLECTION_NAME = "intelliplant_docs"


def get_chroma_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_collection():
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_chunks(
    chunks: List[str],
    metadatas: List[dict],
    ids: List[str],
    embeddings: List[List[float]],
):
    """Add text chunks with their embeddings to the vector store."""
    collection = get_collection()
    collection.add(
        documents=chunks,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings,
    )
    logger.info(f"Added {len(chunks)} chunks to vector store.")


def query_similar(
    query_embedding: List[float],
    n_results: int = 5,
    where: Optional[dict] = None,
) -> dict:
    """Retrieve most similar chunks to a query embedding."""
    collection = get_collection()
    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": min(n_results, collection.count() or 1),
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where
    return collection.query(**kwargs)


def delete_document_chunks(document_id: str):
    """Remove all chunks for a document (e.g., on re-ingestion)."""
    collection = get_collection()
    collection.delete(where={"document_id": document_id})


def get_collection_stats() -> dict:
    collection = get_collection()
    return {"total_chunks": collection.count(), "collection_name": COLLECTION_NAME}
