"""
Configuration centrale — Variables d'environnement.

Chargées depuis le fichier .env via pydantic-settings.
Importées partout via : from app.core.config import settings
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── API ────────────────────────────────────────────────────────
    app_name: str = "Recruitment AI Backend"
    app_version: str = "0.1.0"
    debug: bool = False
    api_prefix: str = "/v1"

    # ── Google Gemini ──────────────────────────────────────────────
    google_api_key: str = ""

    # ── Chemins ────────────────────────────────────────────────────
    upload_dir: Path = Path("data/uploads")
    chroma_dir: Path = Path("data/chroma_db")

    # ── Upload ─────────────────────────────────────────────────────
    max_upload_size_mb: int = 20
    allowed_extensions: list[str] = [".pdf", ".txt"]

    # ── LangGraph ──────────────────────────────────────────────────
    langgraph_recursion_limit: int = 50

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()