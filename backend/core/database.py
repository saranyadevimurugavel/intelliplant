"""SQLite database setup with SQLAlchemy async."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Text, DateTime, Float, JSON, Integer, Boolean
from datetime import datetime, timezone
import uuid

from core.config import settings

DATABASE_URL = f"sqlite+aiosqlite:///{settings.sqlite_db}"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def utcnow():
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    doc_type = Column(String, nullable=False)  # pdf, pid, spreadsheet, email, scan
    category = Column(String)  # maintenance, safety, engineering, compliance, etc.
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)
    status = Column(String, default="pending")  # pending, processing, ready, failed
    page_count = Column(Integer)
    extracted_text = Column(Text)
    entities = Column(JSON)   # extracted entities
    summary = Column(Text)
    created_at = Column(DateTime, default=utcnow)
    processed_at = Column(DateTime)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False)
    role = Column(String, nullable=False)   # user | assistant
    content = Column(Text, nullable=False)
    sources = Column(JSON)   # list of source citations
    confidence = Column(Float)
    created_at = Column(DateTime, default=utcnow)


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    work_order_id = Column(String)
    asset_tag = Column(String)
    asset_name = Column(String)
    work_type = Column(String)   # corrective, preventive, inspection
    description = Column(Text)
    findings = Column(Text)
    status = Column(String)
    priority = Column(String)
    scheduled_date = Column(DateTime)
    completed_date = Column(DateTime)
    technician = Column(String)
    document_id = Column(String)
    created_at = Column(DateTime, default=utcnow)


class ComplianceGap(Base):
    __tablename__ = "compliance_gaps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    regulation = Column(String)   # Factory Act, OISD, PESO, etc.
    clause = Column(String)
    requirement = Column(Text)
    current_state = Column(Text)
    gap_description = Column(Text)
    severity = Column(String)   # critical, major, minor
    status = Column(String, default="open")  # open, in_progress, closed
    corrective_action = Column(Text)
    due_date = Column(DateTime)
    created_at = Column(DateTime, default=utcnow)


class LessonLearned(Base):
    __tablename__ = "lessons_learned"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_type = Column(String)
    asset_tag = Column(String)
    description = Column(Text)
    root_cause = Column(Text)
    corrective_actions = Column(Text)
    preventive_actions = Column(Text)
    severity = Column(String)
    recurrence_count = Column(Integer, default=1)
    pattern_tags = Column(JSON)
    document_id = Column(String)
    created_at = Column(DateTime, default=utcnow)


async def init_db():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency for FastAPI routes."""
    async with AsyncSessionLocal() as session:
        yield session
