import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "InfraPilot AI"
    APP_TAGLINE: str = "Your Infrastructure. One Command Center."
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    SECRET_KEY: str = "dev-secret-key-infrapilot-ai-change-this-in-production-min32chars"
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:19420",
    ]

    DATABASE_URL: str = "sqlite:///./data/piops.db"

    METRIC_COLLECTION_INTERVAL_SECONDS: int = 5
    HISTORY_RETENTION_HOURS: int = 72

    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen3:4b"
    OLLAMA_TIMEOUT_SECONDS: int = 45

    SOLOHOST_MODE: str = "control-center"
    PI_NETWORK_ENVIRONMENT: str = "sandbox"
    PI_API_KEY: str = ""
    PI_APP_ID: str = "infrapilot-ai"

    AGENT_SHARED_SECRET: str = "dev-agent-secret-key-change-for-production"


settings = Settings()
