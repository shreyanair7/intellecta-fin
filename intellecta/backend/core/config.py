from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Intellecta"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "intellecta-super-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/intellecta.db"

    # Paths
    CHROMA_PATH: str = str(BASE_DIR / "chroma_db")
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")

    # Embedding model
    EMBED_MODEL: str = "BAAI/bge-small-en-v1.5"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # RAG
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Retrieval
    TOP_K: int = 10

    # Citation filtering
    MAX_CITATIONS: int = 4
    RELEVANCE_MARGIN: float = 0.15

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()