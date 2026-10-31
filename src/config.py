"""Configurações centrais da aplicação carregadas de variáveis de ambiente."""

import os
from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Identificação do projeto
    PROJECT_NAME: str = "Empório da Música - AI Agent"
    VERSION: str = "0.1.0"
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"

    # LLM & Provedores
    LLM_PROVIDER: Literal["google", "openai"] = "google"
    GOOGLE_API_KEY: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    OPENAI_API_KEY: str | None = Field(default=None, alias="OPENAI_API_KEY")

    LLM_MODEL: str = "gemini-2.5-flash"
    TEMPERATURE: float = 0.2

    # RAG & Embeddings
    EMBEDDING_PROVIDER: Literal["google", "openai", "local"] = "google"
    EMBEDDING_MODEL: str = "text-embedding-004"

    # Logging
    LOG_LEVEL: str = "INFO"


settings = Settings()
