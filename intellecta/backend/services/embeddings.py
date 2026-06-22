"""
Singleton embedding service using BAAI/bge-small-en-v1.5 via sentence-transformers.
Loaded lazily on first use to avoid slowing down startup.
"""
from __future__ import annotations

import logging
from typing import List

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        from core.config import settings
        logger.info("Loading embedding model %s …", settings.EMBED_MODEL)
        _model = SentenceTransformer(settings.EMBED_MODEL)
        logger.info("Embedding model loaded.")
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Return a list of embedding vectors for the given texts."""
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def embed_query(text: str) -> List[float]:
    """Return a single embedding vector for a query string."""
    return embed_texts([text])[0]
