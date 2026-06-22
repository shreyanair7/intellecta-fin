import json
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from models.models import Conversation, Message, User
from schemas.schemas import (
    ConversationOut,
    MessageOut,
    QueryRequest,
    QueryResponse,
    Source,
)
from services.embeddings import embed_query
from services.intent_handlers import (
    handle_app_info,
    handle_document_management,
    handle_out_of_scope,
    handle_system_info,
)
from services.llm import contextualize_query, generate_answer, generate_smalltalk_reply
from services.router import classify_intent
from services.vector_store import query_chunks

router = APIRouter(prefix="/chat", tags=["chat"])

def _msg_to_out(msg: Message) -> MessageOut:
    sources = None
    if msg.sources_json:
        try:
            raw = json.loads(msg.sources_json)
            sources = [Source(**s) for s in raw]
        except Exception:
            sources = None
    return MessageOut(
        id=msg.id,
        role=msg.role,
        content=msg.content,
        createdAt=msg.created_at,
        sources=sources,
    )


def _convo_to_out(convo: Conversation) -> ConversationOut:
    return ConversationOut(
        id=convo.id,
        title=convo.title,
        updatedAt=convo.updated_at,
        messages=[_msg_to_out(m) for m in convo.messages],
    )


# ─── List conversations ───────────────────────────────────────────────────────

@router.get("/conversations", response_model=List[ConversationOut])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    convos = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [_convo_to_out(c) for c in convos]


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return _convo_to_out(convo)


@router.post("/conversations", response_model=ConversationOut, status_code=201)
def create_conversation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    convo = Conversation(user_id=current_user.id, title="New chat")
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return _convo_to_out(convo)


@router.patch("/conversations/{conversation_id}", response_model=ConversationOut)
def rename_conversation(
    conversation_id: str,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    if "title" in body:
        convo.title = body["title"][:255]
        db.commit()
        db.refresh(convo)
    return _convo_to_out(convo)


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    db.delete(convo)
    db.commit()


# ─── Query (RAG) ──────────────────────────────────────────────────────────────
@router.post("/query", response_model=QueryResponse)
async def query(
    payload: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Resolve or create conversation
    if payload.conversationId:
        convo = (
            db.query(Conversation)
            .filter(
                Conversation.id == payload.conversationId,
                Conversation.user_id == current_user.id,
            )
            .first()
        )
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation not found.")
    else:
        convo = Conversation(user_id=current_user.id, title="New chat")
        db.add(convo)
        db.commit()
        db.refresh(convo)

    # Persist user message
    user_msg = Message(
        conversation_id=convo.id,
        role="user",
        content=payload.content,
    )
    db.add(user_msg)

    # Auto-title on first message
    existing_msgs = (
        db.query(Message)
        .filter(Message.conversation_id == convo.id)
        .count()
    )

    if existing_msgs == 0:
        convo.title = payload.content[:48] + (
            "…" if len(payload.content) > 48 else ""
        )

    db.commit()
    db.refresh(user_msg)

    # ─── Intent routing (before any embedding generation) ────────────────────
    intent = await classify_intent(payload.content)
    print(f"\nIntent detected: {intent}\n")
    if intent != "DOCUMENT_QUERY":
        if intent == "SMALLTALK":
            answer = await generate_smalltalk_reply(payload.content)
        elif intent == "DOCUMENT_MANAGEMENT":
            answer = handle_document_management(
                payload.content, current_user.id, db
            )
        elif intent == "APP_INFO":
            answer = handle_app_info()
        elif intent == "SYSTEM_INFO":
            answer = handle_system_info(payload.content)
        else:  # OUT_OF_SCOPE
            answer = handle_out_of_scope()

        ai_msg = Message(
            conversation_id=convo.id,
            role="ai",
            content=answer,
            sources_json=None,
        )

        db.add(ai_msg)
        convo.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(ai_msg)
        db.refresh(convo)

        return QueryResponse(
            answer=answer,
            citations=[],
            user=_msg_to_out(user_msg),
            ai=_msg_to_out(ai_msg),
            conversation=_convo_to_out(convo),
        )

    # ─── DOCUMENT_QUERY → existing RAG pipeline (unchanged) ───────────────────
    from core.config import settings as cfg

    recent_messages = (
        db.query(Message)
        .filter(Message.conversation_id == convo.id)
        .order_by(Message.created_at.desc())
        .limit(6)
        .all()
    )
    recent_messages = list(reversed(recent_messages))

    history = [
        {"role": m.role, "content": m.content}
        for m in recent_messages
        if m.id != user_msg.id
    ]

    standalone_query = await contextualize_query(
        payload.content,
        history,
    )

    print("\n---- Query Rewriting ----")
    print(f"Original: {payload.content}")
    print(f"Standalone: {standalone_query}")
    print("-------------------------\n")

    query_embedding = embed_query(standalone_query)

    results = query_chunks(
        query_embedding,
        standalone_query,
        current_user.id,
        top_k=cfg.TOP_K,
    )

    chunks: list[str] = results.get("documents", [[]])[0]
    metas: list[dict] = results.get("metadatas", [[]])[0]
    distances: list[float] = results.get("distances", [[]])[0]

    # Similarity filtering
    filtered_chunks = []
    filtered_metas = []
    filtered_distances = []

    if distances:
        best_distance = min(distances)

        cutoff = best_distance + cfg.RELEVANCE_MARGIN

        print(
            f"Best distance={best_distance:.4f} | "
            f"Cutoff={cutoff:.4f}"
        )

        for chunk, meta, distance in zip(chunks, metas, distances):
            if distance <= cutoff:
                filtered_chunks.append(chunk)
                filtered_metas.append(meta)
                filtered_distances.append(distance)
    else:
        citation_cutoff = float("inf")
    chunks = filtered_chunks[: cfg.MAX_CITATIONS]
    metas = filtered_metas[: cfg.MAX_CITATIONS]
    distances = filtered_distances[: cfg.MAX_CITATIONS]

    # Debug logging
    print("\n---- Retrieval Results ----")

    for i, (chunk, distance) in enumerate(zip(chunks, distances)):
        print(
            f"Chunk {i+1}: "
            f"distance={distance:.4f} | "
            f"{chunk[:100].replace(chr(10), ' ')}"
        )

    print(f"Kept {len(chunks)} chunks")
    print("---------------------------\n")

    # Citation-specific filtering
    if distances:
        citation_cutoff = best_distance + 0.015
    else:
        citation_cutoff = float("inf")

    # Build citations
    citations: list[Source] = []

    for chunk, meta, distance in zip(chunks, metas, distances):
        if distance <= citation_cutoff:
            citations.append(
                Source(
                    id=str(uuid.uuid4()),
                    documentName=meta.get("filename", "Unknown"),
                    page=meta.get("chunk_index", 0) + 1,
                    snippet=chunk[:400] + ("…" if len(chunk) > 400 else ""),
                )
            )
    citations = citations[:2]
    
    # Generate answer
    if chunks:
        answer = await generate_answer(
            query=payload.content,
            context_chunks=chunks,
            sources=[
                {
                    "filename": m.get("filename", "?"),
                    "page": m.get("chunk_index", 0) + 1,
                }
                for m in metas
            ],
        )
    else:
        answer = (
            "I couldn't find any relevant information in your indexed documents "
            "for this question."
        )

    # Persist AI message
    ai_msg = Message(
        conversation_id=convo.id,
        role="ai",
        content=answer,
        sources_json=json.dumps(
            [c.model_dump() for c in citations]
        ) if citations else None,
    )

    db.add(ai_msg)

    convo.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(ai_msg)
    db.refresh(convo)

    return QueryResponse(
        answer=answer,
        citations=citations,
        user=_msg_to_out(user_msg),
        ai=_msg_to_out(ai_msg),
        conversation=_convo_to_out(convo),
    )

# ─── Report download ──────────────────────────────────────────────────────────

@router.get("/report/{conversation_id}", response_class=PlainTextResponse)
def download_report(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    lines = [
        "# Intellecta Chat Report",
        f"**Conversation:** {convo.title}",
        f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    for msg in convo.messages:
        role_label = "You" if msg.role == "user" else "Intellecta"
        lines.append(f"## {role_label} — {msg.created_at.strftime('%H:%M:%S')}")
        lines.append("")
        lines.append(msg.content)
        if msg.sources_json:
            try:
                sources = json.loads(msg.sources_json)
                lines.append("")
                lines.append("**Sources:**")
                for i, s in enumerate(sources, 1):
                    lines.append(f'{i}. {s["documentName"]} (p. {s["page"]}) — "{s["snippet"][:200]}"')
            except Exception:
                pass
        lines.append("")

    content = "\n".join(lines)
    filename = f"intellecta-{convo.title[:40].replace(' ', '-').lower()}.md"
    return PlainTextResponse(
        content=content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )