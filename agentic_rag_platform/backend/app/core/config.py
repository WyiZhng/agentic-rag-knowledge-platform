"""Application configuration using Pydantic BaseSettings."""
# ruff: noqa: I001 - Imports structured for Jinja2 template conditionals

from pathlib import Path
from typing import Literal

from pydantic import computed_field, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


def find_env_file() -> Path | None:
    """Find .env file in current or parent directories."""
    current = Path.cwd()
    for path in [current, current.parent]:
        env_file = path / ".env"
        if env_file.exists():
            return env_file
    return None


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_ignore_empty=True,
        extra="ignore",
    )

    # === Project ===
    PROJECT_NAME: str = "agentic_rag_platform"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "local", "staging", "production"] = "local"
    TIMEZONE: str = "UTC"  # IANA timezone (e.g. "UTC", "Europe/Warsaw", "America/New_York")
    MODELS_CACHE_DIR: Path = Path("./models_cache")
    MEDIA_DIR: Path = Path("./media")
    MAX_UPLOAD_SIZE_MB: int = 50  # Max file upload size in MB
    # Soft per-org storage cap surfaced on /billing — not enforced yet (5 GB).
    STORAGE_SOFT_LIMIT_BYTES: int = 5 * 1024 * 1024 * 1024

    # === Logfire ===
    LOGFIRE_TOKEN: str | None = None
    LOGFIRE_SERVICE_NAME: str = "agentic_rag_platform"
    LOGFIRE_ENVIRONMENT: str = "development"

    # === Database (PostgreSQL async) ===
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "agentic_rag_platform"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:
        """Build async PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Build sync PostgreSQL connection URL (for Alembic)."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Pool configuration
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # === Auth (SECRET_KEY for JWT/Session/Admin) ===
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info: ValidationInfo) -> str:
        """Validate SECRET_KEY is secure in production."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        # Get environment from values if available
        env = info.data.get("ENVIRONMENT", "local") if info.data else "local"
        if v == "change-me-in-production-use-openssl-rand-hex-32" and env == "production":
            raise ValueError(
                "SECRET_KEY must be changed in production! "
                "Generate a secure key with: openssl rand -hex 32"
            )
        return v

    # === JWT Settings ===
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"

    # Public URL of the frontend; used to build OAuth redirect targets and
    # Stripe checkout/portal return URLs. Always declared (not gated) because
    # the billing model_validator references it unconditionally.
    FRONTEND_URL: str = "http://localhost:3000"

    # === Auth (API Key) ===
    API_KEY: str = "change-me-in-production"
    API_KEY_HEADER: str = "X-API-Key"

    @field_validator("API_KEY")
    @classmethod
    def validate_api_key(cls, v: str, info: ValidationInfo) -> str:
        """Validate API_KEY is set in production."""
        env = info.data.get("ENVIRONMENT", "local") if info.data else "local"
        if v == "change-me-in-production" and env == "production":
            raise ValueError(
                "API_KEY must be changed in production! "
                "Generate a secure key with: openssl rand -hex 32"
            )
        return v

    # === Redis ===
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_DB: int = 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_URL(self) -> str:
        """Build Redis connection URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # === Rate Limiting ===
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds

    # === Celery ===
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # === AI Agent (langgraph, openai) ===
    OPENAI_API_KEY: str = ""
    AI_MODEL: str = "gpt-5.5"
    AI_TEMPERATURE: float = 0.7
    AI_THINKING_ENABLED: bool = False
    AI_THINKING_EFFORT: str = "medium"  # "low", "medium", "high"
    AI_AVAILABLE_MODELS: list[str] = [
        "gpt-5.5",
        "gpt-5.5-pro",
        "gpt-5.4",
        "gpt-5.4-pro",
        "gpt-5.4-mini",
        "gpt-5.4-nano",
        "gpt-5-mini",
        "gpt-5-nano",
        "gpt-5",
        "gpt-4.1",
    ]
    AI_FRAMEWORK: str = "langgraph"
    LLM_PROVIDER: str = "openai"

    # === RAG (Retrieval Augmented Generation) ===
    # Vector Database (pgvector) — uses existing PostgreSQL

    # Embeddings
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Chunking
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 50

    # Retrieval
    RAG_DEFAULT_COLLECTION: str = "documents"
    RAG_TOP_K: int = 10
    RAG_CHUNKING_STRATEGY: str = "recursive"  # recursive, markdown, or fixed
    RAG_HYBRID_SEARCH: bool = False  # Enable BM25 + vector hybrid search
    RAG_ENABLE_OCR: bool = False  # OCR fallback for scanned PDFs (requires tesseract)

    # Reranker
    HF_TOKEN: str = ""
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L6-v2"

    # Document Parser

    # Google Drive (optional, for document ingestion via service account)

    # S3 (optional, for document ingestion from S3/MinIO)

    # === CORS ===
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: list[str], info: ValidationInfo) -> list[str]:
        """Warn if CORS_ORIGINS is too permissive in production."""
        env = info.data.get("ENVIRONMENT", "local") if info.data else "local"
        if "*" in v and env == "production":
            raise ValueError(
                "CORS_ORIGINS cannot contain '*' in production! Specify explicit allowed origins."
            )
        return v

    @computed_field  # type: ignore[prop-decorator]
    @property
    def rag(self) -> "RAGSettings":
        """Build RAG-specific settings."""
        from app.services.rag.config import RAGSettings, DocumentParser, PdfParser, EmbeddingsConfig

        pdf_parser = PdfParser()

        return RAGSettings(
            collection_name=self.RAG_DEFAULT_COLLECTION,
            chunk_size=self.RAG_CHUNK_SIZE,
            chunk_overlap=self.RAG_CHUNK_OVERLAP,
            chunking_strategy=self.RAG_CHUNKING_STRATEGY,
            enable_hybrid_search=self.RAG_HYBRID_SEARCH,
            enable_ocr=self.RAG_ENABLE_OCR,
            embeddings_config=EmbeddingsConfig(model=self.EMBEDDING_MODEL),
            document_parser=DocumentParser(),
            pdf_parser=pdf_parser,
        )


# Rebuild Settings to resolve RAGSettings forward reference
from app.services.rag.config import RAGSettings

Settings.model_rebuild()


settings = Settings()
