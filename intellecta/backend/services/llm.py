"""
Ollama integration for local LLM inference.
Calls the local Ollama HTTP API with llama3.2.
"""
from __future__ import annotations

import json
import logging
from typing import List, Dict

import httpx

from core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Intellecta, a precise research assistant. You ONLY answer questions based on the provided context chunks retrieved from the user's documents. 

Rules:
- Base your answer strictly on the context provided.
- If the context does not contain enough information, say so honestly.
- Be concise, accurate, and cite which document(s) support each claim.
- Do not hallucinate or add information not present in the context."""


def build_rag_prompt(query: str, context_chunks: List[str], sources: List[Dict]) -> str:
    context_text = "\n\n---\n\n".join(
        f"[Source {i+1}: {s['filename']}, page ~{s.get('page', '?')}]\n{chunk}"
        for i, (chunk, s) in enumerate(zip(context_chunks, sources))
    )
    return f"""Context from retrieved documents:

{context_text}

---

User question: {query}

Answer based solely on the context above:"""


SMALLTALK_SYSTEM_PROMPT = """You are Intellecta, a friendly local document-intelligence assistant. \
The user is making small talk (a greeting, thanks, or casual remark) rather than asking about \
their documents. Reply warmly and briefly in 1-2 sentences. You may mention that you can help \
with their uploaded documents, but keep it light and conversational — do not produce citations \
or reference specific document content."""


async def generate_smalltalk_reply(query: str) -> str:
    """Generate a short, direct conversational reply with no retrieval involved."""
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SMALLTALK_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        "stream": False,
        "options": {
            "temperature": 0.4,
            "top_p": 0.9,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]
    except httpx.ConnectError:
        logger.warning("Ollama not reachable — returning fallback smalltalk reply.")
        return "Hello! How can I help you with your uploaded documents today?"
    except Exception as exc:
        logger.error("Ollama error during smalltalk generation: %s", exc)
        return "Hello! How can I help you with your uploaded documents today?"


REWRITE_PROMPT_TEMPLATE = """You are a query rewriting assistant.

Your task is to rewrite follow-up questions into complete standalone questions.

Rules:

- Preserve the original meaning.
- Use conversation history only when necessary.
- If the question is already complete, return it unchanged.
- Do not answer the question.
- Do not explain your reasoning.
- Return ONLY the rewritten question.

Conversation History:
{history}

Current Question:
{query}"""


def _format_history(history: list[dict]) -> str:
    if not history:
        return "(none)"
    lines = []
    for msg in history:
        role = "User" if msg.get("role") == "user" else "Assistant"
        lines.append(f"{role}: {msg.get('content', '')}")
    return "\n".join(lines)


async def contextualize_query(current_query: str, history: list[dict]) -> str:
    """
    Rewrite a follow-up question into a standalone question using recent
    conversation history. Returns the original query unchanged on any
    failure (Ollama unreachable, empty/unparseable output, etc.) so the
    retrieval pipeline degrades gracefully.
    """
    current_query = (current_query or "").strip()
    if not current_query:
        return current_query

    prompt = REWRITE_PROMPT_TEMPLATE.format(
        history=_format_history(history),
        query=current_query,
    )

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
            rewritten = data["message"]["content"].strip().strip('"').strip()
    except httpx.ConnectError:
        logger.warning("Ollama not reachable during query rewriting — using original query.")
        return current_query
    except Exception as exc:
        logger.error("Query rewriting error: %s", exc)
        return current_query

    return rewritten if rewritten else current_query


async def generate_answer(query: str, context_chunks: List[str], sources: List[Dict]) -> str:
    prompt = build_rag_prompt(query, context_chunks, sources)

    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]
    except httpx.ConnectError:
        logger.warning("Ollama not reachable — returning fallback answer.")
        return (
            f"⚠️ **Ollama is not running.** To enable local LLM answers, start Ollama with:\n\n"
            f"```\nollama serve\nollama pull {settings.OLLAMA_MODEL}\n```\n\n"
            f"Based on the retrieved context, here is a summary of relevant passages for your query: *\"{query}\"*\n\n"
            + "\n\n".join(f"- {chunk[:300]}…" for chunk in context_chunks[:2])
        )
    except Exception as exc:
        logger.error("Ollama error: %s", exc)
        raise