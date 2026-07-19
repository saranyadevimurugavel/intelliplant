"""Expert Knowledge Copilot API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
import uuid

from core.database import get_db, ChatSession, ChatMessage
from services.rag_service import answer_query
from datetime import datetime, timezone

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    category_filter: Optional[str] = None


class SessionCreate(BaseModel):
    title: Optional[str] = "New Conversation"


@router.post("/query")
async def query_copilot(request: QueryRequest, db: AsyncSession = Depends(get_db)):
    """Submit a query to the Expert Knowledge Copilot."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Get or create session
    session_id = request.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        session = ChatSession(id=session_id, title=request.query[:60])
        db.add(session)
        await db.commit()

    # Fetch session history
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(10)
    )
    history = history_result.scalars().all()
    history_dicts = [{"role": m.role, "content": m.content} for m in history]

    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=request.query,
    )
    db.add(user_msg)
    await db.commit()

    # Generate answer via RAG
    try:
        result = await answer_query(
            query=request.query,
            session_history=history_dicts,
            doc_category_filter=request.category_filter,
        )
    except Exception as e:
        import traceback
        import logging
        logging.getLogger(__name__).error(f"Copilot error: {e}\n{traceback.format_exc()}")
        raise

    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=result["answer"],
        sources=result["sources"],
        confidence={"high": 0.9, "medium": 0.6, "low": 0.3}.get(result["confidence"], 0.5),
    )
    db.add(assistant_msg)

    # Update session title if first query
    if len(history) == 0:
        session_obj = await db.get(ChatSession, session_id)
        if session_obj:
            session_obj.title = request.query[:60]
            session_obj.updated_at = datetime.now(timezone.utc)

    await db.commit()

    return {
        "session_id": session_id,
        "answer": result["answer"],
        "sources": result["sources"],
        "confidence": result["confidence"],
        "kg_entities_found": result.get("kg_entities_found", []),
    }


@router.get("/sessions")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """List all chat sessions."""
    result = await db.execute(
        select(ChatSession).order_by(ChatSession.updated_at.desc()).limit(50)
    )
    sessions = result.scalars().all()
    return [
        {"id": s.id, "title": s.title, "created_at": s.created_at, "updated_at": s.updated_at}
        for s in sessions
    ]


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get all messages in a session."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "sources": m.sources,
            "confidence": m.confidence,
            "created_at": m.created_at,
        }
        for m in messages
    ]


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a chat session and its messages."""
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    msgs = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
    )
    for m in msgs.scalars().all():
        await db.delete(m)
    await db.delete(session)
    await db.commit()
    return {"message": "Session deleted."}
