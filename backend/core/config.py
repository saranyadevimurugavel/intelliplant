"""Application configuration via environment variables."""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Groq (LLM — free tier)
    groq_api_key: str = "your-groq-key-here"
    groq_model: str = "llama-3.3-70b-versatile"

    # Storage
    upload_dir: str = "./uploads"
    chroma_dir: str = "./chroma_db"
    sqlite_db: str = "./intelliplant.db"
    knowledge_graph_path: str = "./knowledge_graph.json"

    # App
    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "https://intelliplant.vercel.app",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def ensure_dirs(self):
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.chroma_dir, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
