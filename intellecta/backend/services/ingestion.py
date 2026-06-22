"""
Document ingestion pipeline:
1. Extract text from PDF/DOCX/TXT/MD
2. Split into chunks via RecursiveCharacterTextSplitter
3. Embed with BGE
4. Upsert to ChromaDB
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple

from core.config import settings
from services.embeddings import embed_texts
from services.vector_store import upsert_chunks

logger = logging.getLogger(__name__)


def _extract_text_pdf(path: str) -> Tuple[str, int]:
    """Extract full text from a PDF."""
    from pypdf import PdfReader

    reader = PdfReader(path)

    pages_text = []

    for page in reader.pages:
        text = page.extract_text() or ""
        pages_text.append(text)

    return "\n\n".join(pages_text), len(reader.pages)


def _extract_text_docx(path: str) -> Tuple[str, int]:
    """Extract text from a DOCX file."""
    from docx import Document

    doc = Document(path)

    paragraphs = [
        paragraph.text.strip()
        for paragraph in doc.paragraphs
        if paragraph.text.strip()
    ]

    text = "\n".join(paragraphs)

    return text, 1


def _extract_text_plain(path: str) -> Tuple[str, int]:
    """Extract text from TXT/MD files."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    return text, 1


def extract_text(file_path: str, filename: str) -> Tuple[str, int]:
    """Route file to appropriate extractor."""
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return _extract_text_pdf(file_path)

    elif ext == ".docx":
        return _extract_text_docx(file_path)

    elif ext in [".txt", ".md"]:
        return _extract_text_plain(file_path)

    raise ValueError(f"Unsupported file type: {ext}")


def chunk_text(text: str) -> List[str]:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    return splitter.split_text(text)


def ingest_document(
    file_path: str,
    filename: str,
    document_id: str,
    user_id: str,
) -> int:
    """Full ingestion pipeline. Returns number of chunks stored."""

    logger.info("Ingesting '%s' for user %s ...", filename, user_id)

    text, num_pages = extract_text(file_path, filename)

    if not text.strip():
        logger.warning("No text extracted from '%s'.", filename)
        return 0

    chunks = chunk_text(text)

    logger.info("Split into %d chunks.", len(chunks))

    if not chunks:
        return 0

    batch_size = 64

    all_embeddings = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        all_embeddings.extend(embed_texts(batch))

    metadatas = [
        {
            "user_id": user_id,
            "document_id": document_id,
            "filename": filename,
            "chunk_index": idx,
            "num_pages": num_pages,
        }
        for idx in range(len(chunks))
    ]

    upsert_chunks(chunks, all_embeddings, metadatas)

    logger.info(
        "Ingestion complete: %d chunks for '%s'.",
        len(chunks),
        filename,
    )

    return len(chunks)