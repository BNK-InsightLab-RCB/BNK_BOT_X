"""Runtime settings. `.env`가 코드 기본값을 오버라이드한다."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Qdrant — 전용 컨테이너(6335). BNK_Bot(6333)과 분리.
    qdrant_url: str = "http://localhost:6335"
    qdrant_api_key: str | None = None
    qdrant_collection_name: str = "bnk_ops_knowledge"
    embedding_dim: int = 1024  # KURE-v1

    # LLM — Qwen via Ollama(OpenAI 호환). 엔드포인트 공유, 코드는 새로.
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "qwen3.5-bnk"
    llm_timeout_s: float = 120.0

    # Embedding — KURE-v1
    embedding_model: str = "nlpai-lab/KURE-v1"

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    source_dir: Path = base_dir / "examples" / "bank_sample"
    data_dir: Path = base_dir / "data"
    manuals_dir: Path = data_dir / "manuals"
    graph_db_path: Path = data_dir / "lineage.sqlite3"
    handoff_db_path: Path = data_dir / "handoffs.sqlite3"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
