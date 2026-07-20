"""
IntelliPlant — AI for Industrial Knowledge Intelligence
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
import os

from core.config import settings
from core.database import init_db
from core.knowledge_graph import init_knowledge_graph
from api.routes import documents, copilot, maintenance, compliance, lessons, health, auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting IntelliPlant backend...")
    await init_db()
    init_knowledge_graph()
    logger.info("IntelliPlant backend ready.")
    yield
    logger.info("Shutting down IntelliPlant backend.")


app = FastAPI(
    title="IntelliPlant — Industrial Knowledge Intelligence",
    description="AI-powered platform for industrial document intelligence",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + [
        "https://intelliplant.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(copilot.router, prefix="/api/copilot", tags=["Copilot"])
app.include_router(maintenance.router, prefix="/api/maintenance", tags=["Maintenance"])
app.include_router(compliance.router, prefix="/api/compliance", tags=["Compliance"])
app.include_router(lessons.router, prefix="/api/lessons", tags=["Lessons Learned"])

# Serve built React frontend — single URL for everything
# Checks: local dev, GitHub Actions build path, Render build path
FRONTEND_DIST = None
for candidate in [
    os.path.join(os.path.dirname(__file__), "frontend_dist"),       # Render/GitHub Actions
    os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"),  # Local dev
]:
    if os.path.exists(candidate) and os.path.exists(os.path.join(candidate, "index.html")):
        FRONTEND_DIST = os.path.abspath(candidate)
        logger.info(f"Serving frontend from: {FRONTEND_DIST}")
        break

if FRONTEND_DIST:
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))


@app.get("/")
async def root():
    return {
        "name": "IntelliPlant API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }
