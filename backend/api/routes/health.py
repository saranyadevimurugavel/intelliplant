from fastapi import APIRouter
from core.knowledge_graph import get_graph_stats
from core.vector_store import get_collection_stats

router = APIRouter()


@router.get("/health")
async def health_check():
    kg_stats = get_graph_stats()
    vs_stats = get_collection_stats()
    return {
        "status": "healthy",
        "knowledge_graph": kg_stats,
        "vector_store": vs_stats,
    }
