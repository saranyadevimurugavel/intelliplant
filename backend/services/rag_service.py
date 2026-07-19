"""
RAG Service — using Groq (LLaMA 3.3 70B) for generation + Gemini for embeddings.
"""
import logging
from typing import List, Optional
from groq import Groq

from core.config import settings
from core.embeddings import embed_query
from core.vector_store import query_similar
from core.knowledge_graph import get_asset_full_context

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are IntelliPlant Copilot, an expert AI assistant for industrial operations, maintenance, and engineering at a petroleum refinery / heavy industry plant.

You have access to the plant's full document corpus including engineering drawings, P&IDs, maintenance work orders, operating procedures, inspection reports, safety procedures, OEM equipment manuals, regulatory compliance documents (OISD, PESO, Factory Act), and incident reports.

INSTRUCTIONS:
1. Answer based ONLY on the provided context. Do not fabricate facts.
2. Always cite sources using [Source: <filename>] format.
3. End every answer with: **Confidence: High/Medium/Low**
4. If the answer is not in the context, say clearly: "I could not find reliable information about this in the available documents."
5. For safety-critical queries, always add: "⚠️ Verify with the relevant procedure and your supervisor before acting."
6. Keep answers concise but complete. Use bullet points for steps or lists."""


def build_context_from_chunks(retrieved_chunks: dict) -> tuple:
    context_parts = []
    sources = []
    seen_docs = set()

    documents = retrieved_chunks.get("documents", [[]])[0]
    metadatas = retrieved_chunks.get("metadatas", [[]])[0]
    distances = retrieved_chunks.get("distances", [[]])[0]

    for doc_text, meta, dist in zip(documents, metadatas, distances):
        filename = meta.get("filename", "Unknown")
        category = meta.get("category", "")
        chunk_idx = meta.get("chunk_index", 0)
        doc_id = meta.get("document_id", "")
        similarity = round(1 - dist, 3)

        context_parts.append(
            f"[Source: {filename} | Category: {category}]\n{doc_text}\n"
        )
        if doc_id not in seen_docs:
            sources.append({
                "document_id": doc_id,
                "filename": filename,
                "category": category,
                "similarity_score": similarity,
                "chunk_index": chunk_idx,
            })
            seen_docs.add(doc_id)

    return "\n---\n".join(context_parts), sources


def determine_confidence(sources: list) -> str:
    if not sources:
        return "low"
    top = sources[0].get("similarity_score", 0)
    if top >= 0.80:
        return "high"
    elif top >= 0.55:
        return "medium"
    return "low"


async def answer_query(
    query: str,
    session_history: Optional[List[dict]] = None,
    doc_category_filter: Optional[str] = None,
) -> dict:
    """Full RAG pipeline: embed → retrieve → Groq LLM."""
    # 1. Embed query
    query_embedding = embed_query(query)

    # 2. Retrieve chunks
    where_filter = {"category": doc_category_filter} if doc_category_filter else None
    retrieved = query_similar(query_embedding, n_results=6, where=where_filter)

    # 3. Build context
    context_text, sources = build_context_from_chunks(retrieved)

    # 4. Knowledge graph augmentation
    kg_context = ""
    for tag in _extract_asset_tags(query)[:2]:
        asset_ctx = get_asset_full_context(tag.upper())
        if asset_ctx:
            kg_context += f"\n[Knowledge Graph — {tag}]: {_fmt_kg(asset_ctx)}\n"

    # 5. Build messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if session_history:
        for msg in session_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

    user_content = f"""DOCUMENT CONTEXT:
{context_text or "No documents indexed yet. Please upload documents first."}
{kg_context}

USER QUESTION: {query}"""

    messages.append({"role": "user", "content": user_content})

    # 6. Call Groq
    try:
        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            temperature=0.2,
            max_tokens=1500,
        )
        answer = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq LLM call failed: {e}")
        answer = _fallback_answer(context_text, sources)

    return {
        "answer": answer,
        "sources": sources,
        "confidence": determine_confidence(sources),
        "query": query,
        "kg_entities_found": _extract_asset_tags(query),
    }


def _extract_asset_tags(query: str) -> List[str]:
    import re
    return list(set(re.compile(r'\b([A-Z]{1,4}-[A-Z0-9]{2,6})\b').findall(query.upper())))


def _fmt_kg(ctx: dict) -> str:
    a = ctx.get("asset", {})
    parts = [f"{a.get('name','')} | Status: {a.get('status','')} | Criticality: {a.get('criticality','')}"]
    if ctx.get("maintenance_records"):
        parts.append(f"{len(ctx['maintenance_records'])} work orders")
    if ctx.get("incidents"):
        parts.append(f"{len(ctx['incidents'])} incidents")
    return " | ".join(parts)


def _fallback_answer(context: str, sources: list) -> str:
    if not sources:
        return "I could not find reliable information in the available documents. Please upload relevant documents first.\n\n**Confidence: Low**"
    source_list = "\n".join(f"- {s['filename']} ({s['similarity_score']:.0%} match)" for s in sources[:3])
    return f"Based on available documents:\n\n{context[:400]}...\n\n**Sources:**\n{source_list}\n\n**Confidence: Low** *(LLM unavailable)*"
