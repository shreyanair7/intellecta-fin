"""
Intellecta FastAPI Backend
Run with: uvicorn main:app --reload --port 8000
"""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import Base, engine
from routers import auth, chat, documents

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s — %(message)s")
logger = logging.getLogger(__name__)

# ─── Create tables ────────────────────────────────────────────────────────────
# Import models so SQLAlchemy registers them before create_all
from models import models  # noqa: F401 — registers ORM classes

Base.metadata.create_all(bind=engine)

# Ensure upload dir exists
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.CHROMA_PATH).mkdir(parents=True, exist_ok=True)

# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Intellecta API",
    description="Local RAG backend with FastAPI, ChromaDB, BGE embeddings, and Ollama.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────
PREFIX = settings.API_V1_PREFIX

app.include_router(auth.router, prefix=PREFIX)
app.include_router(documents.router, prefix=PREFIX)
app.include_router(chat.router, prefix=PREFIX)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "Intellecta API"}


@app.on_event("startup")
async def on_startup():
    logger.info("Intellecta API started. Docs at http://localhost:8000/docs")
