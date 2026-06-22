"""
ChromaDB service - persistent local vector store.
Each user's chunks are namespaced with a user_id metadata filter.
"""
from __future__ import annotations

import logging
import uuid
from typing import List, Dict, Any

import chromadb

from core.config import settings

logger = logging.getLogger(__name__)

_client: chromadb.PersistentClient | None = None
_collection = None

COLLECTION_NAME = "intellecta_docs"


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB collection '%s' ready.", COLLECTION_NAME)
    return _collection


def upsert_chunks(
    chunks: List[str],
    embeddings: List[List[float]],
    metadatas: List[Dict[str, Any]],
) -> None:
    col = _get_collection()
    ids = [str(uuid.uuid4()) for _ in chunks]
    col.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    logger.info("Upserted %d chunks into ChromaDB.", len(chunks))


def query_chunks(
    query_embedding: List[float],
    query_text: str,
    user_id: str,
    top_k: int = 10,
) -> Dict[str, Any]:
    col = _get_collection()
    
    # Retrieve more candidates than needed
    results = col.query(
        query_embeddings=[query_embedding],
        n_results=max(top_k * 3, 20),
        where={"user_id": user_id},
        include=["documents", "metadatas", "distances"],
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    # Extract keywords from query
    query_words = {
        word.lower().strip(".,!?()[]{}")
        for word in query_text.split()
        if len(word) > 3
    }

    reranked = []

    for doc, meta, distance in zip(
        documents,
        metadatas,
        distances,
    ):
        chunk_words = set(
            word.lower().strip(".,!?()[]{}")
            for word in doc.split()
        )

        matches = len(query_words & chunk_words)

        # Lower score = better
        hybrid_score = distance - (matches * 0.03)
        print(
            f"distance={distance:.4f} | "
            f"matches={matches} | "
            f"hybrid={hybrid_score:.4f}"
        )
        
        reranked.append(
            (
                hybrid_score,
                doc,
                meta,
                distance,
                matches,
            )
        )

    reranked.sort(key=lambda x: x[0])

    reranked = reranked[:top_k]

    return {
        "documents": [[r[1] for r in reranked]],
        "metadatas": [[r[2] for r in reranked]],
        "distances": [[r[3] for r in reranked]],
    }

def delete_document_chunks(document_id: str, user_id: str) -> None:
    col = _get_collection()
    col.delete(where={"$and": [{"document_id": document_id}, {"user_id": user_id}]})
    logger.info("Deleted chunks for document %s.", document_id)
