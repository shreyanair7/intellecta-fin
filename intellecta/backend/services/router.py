"""
Intent Routing Layer for Intellecta.

Classifies an incoming user query into one of six intents using a local
Ollama model, BEFORE any embedding generation or ChromaDB retrieval takes
place. This lets non-document queries (greetings, app-info questions,
date/time questions, document-inventory questions, and clearly out-of-scope
questions) be answered directly — without running them through the RAG
pipeline and without attaching irrelevant citations.

This module is intentionally self-contained: it does not import or modify
anything from embeddings.py, vector_store.py, or ingestion.py.
"""
from __future__ import annotations

import logging
from typing import Final

import httpx

from core.config import settings

logger = logging.getLogger(__name__)

VALID_INTENTS: Final[set[str]] = {
    "SMALLTALK",
    "DOCUMENT_QUERY",
    "DOCUMENT_MANAGEMENT",
    "APP_INFO",
    "SYSTEM_INFO",
    "OUT_OF_SCOPE",
}

# Default intent used whenever classification is ambiguous, fails, or the
# model returns something unexpected. DOCUMENT_QUERY is the safest fallback
# because it preserves the existing (pre-router) behavior of always
# attempting retrieval.
DEFAULT_INTENT: Final[str] = "DOCUMENT_QUERY"

CLASSIFIER_PROMPT_TEMPLATE: Final[str] = """You are an intent classifier for a document intelligence assistant.

Return ONLY ONE label from:

SMALLTALK
DOCUMENT_QUERY
DOCUMENT_MANAGEMENT
APP_INFO
SYSTEM_INFO
OUT_OF_SCOPE

Intent Definitions

SMALLTALK:
Greetings, thanks, acknowledgements, casual conversation.
Examples:
- Hi
- Hello
- Thanks
- Good morning
- How are you?
- Okay

DOCUMENT_QUERY:
Questions about concepts, topics, explanations, summaries, comparisons, definitions, analysis, or information that may exist inside uploaded documents.

This is the DEFAULT choice whenever the user is asking about knowledge, content, concepts, technical topics, academic subjects, reports, manuals, notes, guides, or document information.

Examples:
- Compare saga pattern and circuit breaker
- Explain linked lists
- Summarize the foam formation document
- What causes foam formation?
- Explain microservices architecture
- What are the disadvantages?
- Explain it simply
- Compare the uploaded reports
- What does the document say about API Gateway?
- Give me a summary of Unit 1

DOCUMENT_MANAGEMENT:
Questions about uploaded files themselves, document inventory, file counts, filenames, uploads, or document metadata.

Examples:
- What documents are uploaded?
- List my files
- Show uploaded documents
- How many documents do I have?
- What was my latest upload?
- Which files have I uploaded?

APP_INFO:
Questions about Intellecta's capabilities, features, usage, limitations, or how the application works.

Examples:
- What can you do?
- How do I use this?
- What are your features?
- How does Intellecta work?

SYSTEM_INFO:
Questions about current date or time.

Examples:
- What date is today?
- What time is it?
- Today's date?
- Current time?

OUT_OF_SCOPE:
Questions requiring live external information that cannot come from uploaded documents.

Examples:
- Weather in Bangalore
- Latest IPL score
- Today's stock market
- Current news
- Bitcoin price

Classification Rules

1. If the user is asking about a concept, topic, explanation, comparison, summary, definition, or subject matter, choose DOCUMENT_QUERY.
2. If unsure between DOCUMENT_QUERY and DOCUMENT_MANAGEMENT, choose DOCUMENT_QUERY.
3. Follow-up questions such as:
   - Explain it simply
   - What are the disadvantages?
   - Compare them
   should be DOCUMENT_QUERY.
4. Return ONLY the label.
5. Do not explain your choice.

User Message:
{query}
"""


def _extract_label(raw: str) -> str | None:
    """
    Pull a valid intent label out of the raw model output.

    Ollama models occasionally wrap the label in punctuation, extra
    whitespace, or a trailing period even when explicitly told to return
    only the label, so this does a tolerant best-effort match rather than
    a strict equality check.
    """
    if not raw:
        return None

    cleaned = raw.strip().strip(".").strip().upper()

    # Exact match first (the common case).
    if cleaned in VALID_INTENTS:
        return cleaned

    # Fall back to scanning tokens in case of stray text around the label,
    # e.g. "Label: SMALLTALK" or "SMALLTALK." or a short sentence.
    tokens = cleaned.replace("\n", " ").split()
    for token in tokens:
        token = token.strip(".,:;\"'")
        if token in VALID_INTENTS:
            return token

    return None


async def classify_intent(query: str) -> str:
    """
    Classify a user query into one of the six supported intents using
    Ollama.

    Always returns one of VALID_INTENTS. On any failure (Ollama unreachable,
    unparseable response, etc.) this falls back to DEFAULT_INTENT so the
    chat flow degrades gracefully into the existing RAG behavior rather
    than breaking.
    """
    query = (query or "").strip()
    if not query:
        return DEFAULT_INTENT

    prompt = CLASSIFIER_PROMPT_TEMPLATE.format(query=query)

    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0.0,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            raw_label = data["message"]["content"]
    except httpx.ConnectError:
        logger.warning(
            "Ollama not reachable during intent classification — "
            "defaulting to %s.",
            DEFAULT_INTENT,
        )
        return DEFAULT_INTENT
    except Exception as exc:
        logger.error("Intent classification error: %s", exc)
        return DEFAULT_INTENT

    label = _extract_label(raw_label)

    if label is None:
        logger.warning(
            "Intent classifier returned unrecognized output (%r) — "
            "defaulting to %s.",
            raw_label,
            DEFAULT_INTENT,
        )
        return DEFAULT_INTENT

    return label