"""
Handlers for non-document-retrieval intents produced by services/router.py.

Each function here returns a plain string answer and performs NO vector
search — they either query the relational database directly
(DOCUMENT_MANAGEMENT), use local Python utilities (SYSTEM_INFO), or return a
static/templated response (APP_INFO, OUT_OF_SCOPE). None of these touch
ChromaDB, embeddings, or the citation-filtering logic in routers/chat.py.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from models.models import Document


def handle_document_management(query: str, user_id: str, db: Session) -> str:
    """
    Answer questions about the user's uploaded document inventory by
    querying the `documents` table directly. No retrieval involved.
    """
    docs = (
        db.query(Document)
        .filter(Document.user_id == user_id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )

    if not docs:
        return (
            "You haven't uploaded any documents yet. Once you upload a file, "
            "I'll be able to list it here and answer questions about it."
        )

    normalized = query.strip().lower()

    # "How many documents do I have?"
    if "how many" in normalized:
        count = len(docs)
        noun = "document" if count == 1 else "documents"
        return f"You have {count} {noun} uploaded."

    # "What was my latest upload?"
    if "latest" in normalized or "most recent" in normalized or "last upload" in normalized:
        latest = docs[0]
        return (
            f"Your most recently uploaded document is \"{latest.name}\", "
            f"uploaded on {latest.uploaded_at.strftime('%Y-%m-%d %H:%M')}."
        )

    # Default: list all documents
    lines = [f"You have {len(docs)} document(s) uploaded:"]
    for doc in docs:
        size_kb = doc.size / 1024
        lines.append(
            f"- {doc.name} ({size_kb:.1f} KB, uploaded "
            f"{doc.uploaded_at.strftime('%Y-%m-%d %H:%M')})"
        )
    return "\n".join(lines)


def handle_app_info() -> str:
    """
    Return a structured description of Intellecta's capabilities.
    No retrieval involved.
    """
    return (
        "Here's what I can help you with:\n\n"
        "- **Document upload**: Upload PDF, DOCX, TXT, or Markdown files for me to index.\n"
        "- **Question answering**: Ask questions about your uploaded documents and "
        "I'll answer using their content.\n"
        "- **Summarization**: Ask me to summarize a document, a chapter, or a specific topic.\n"
        "- **Citation support**: Answers grounded in your documents include citations "
        "showing the source file and location.\n"
        "- **Document management**: Ask what documents you've uploaded, how many you have, "
        "or what your latest upload was.\n\n"
        "I currently work only with your uploaded documents and local application data — "
        "I don't have access to live internet information."
    )


def handle_system_info(query: str) -> str:
    """
    Answer date/time questions using the local system clock.
    No retrieval involved.
    """
    normalized = query.strip().lower()
    now = datetime.now()

    wants_time = "time" in normalized
    wants_date = "date" in normalized or "day" in normalized or "today" in normalized

    if wants_time and not wants_date:
        return f"The current time is {now.strftime('%H:%M:%S')}."

    if wants_date and not wants_time:
        return f"Today's date is {now.strftime('%A, %B %d, %Y')}."

    # Ambiguous or asks for both — give both.
    return (
        f"Today's date is {now.strftime('%A, %B %d, %Y')} "
        f"and the current time is {now.strftime('%H:%M:%S')}."
    )


def handle_out_of_scope() -> str:
    """
    Politely explain that live/external-data questions aren't supported.
    No retrieval involved.
    """
    return (
        "I currently do not have access to live internet information such as "
        "weather, news, sports scores, or stock prices. I can assist with "
        "uploaded documents and application-related information."
    )