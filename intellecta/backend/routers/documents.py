import os
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.deps import get_current_user
from models.models import Document, User
from schemas.schemas import DocumentOut
from services.ingestion import ingest_document
from services.vector_store import delete_document_chunks

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.get("", response_model=list[DocumentOut])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    docs = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    return [DocumentOut.from_orm_doc(d) for d in docs]


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read content and check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the 20 MB limit.",
        )

    # Create DB record first to get the ID
    doc = Document(
        user_id=current_user.id,
        name=file.filename,
        size=len(content),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Save to disk
    upload_dir = Path(settings.UPLOAD_DIR) / current_user.id
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{doc.id}{ext}"
    with open(file_path, "wb") as f:
        f.write(content)

    # Ingest into vector store (synchronous — acceptable for local use)
    try:
        ingest_document(
            file_path=str(file_path),
            filename=file.filename,
            document_id=doc.id,
            user_id=current_user.id,
        )
    except Exception as exc:
        # Don't fail the upload if ingestion fails; log it
        import logging
        logging.getLogger(__name__).error("Ingestion error for %s: %s", file.filename, exc)

    return DocumentOut.from_orm_doc(doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # Remove from vector store
    try:
        delete_document_chunks(document_id, current_user.id)
    except Exception:
        pass

    # Remove file from disk
    from pathlib import Path as P
    for ext in [".pdf", ".txt", ".md", ".docx"]:
        p = P(settings.UPLOAD_DIR) / current_user.id / f"{document_id}{ext}"
        if p.exists():
            p.unlink()

    db.delete(doc)
    db.commit()
