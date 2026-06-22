from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


# ─── Auth ────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: str
    name: str
    email: str

    class Config:
        from_attributes = True


TokenResponse.model_rebuild()


# ─── Documents ───────────────────────────────────────────────────────────────

class DocumentOut(BaseModel):
    id: str
    name: str
    size: int
    uploadedAt: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

    @classmethod
    def from_orm_doc(cls, doc):
        return cls(id=doc.id, name=doc.name, size=doc.size, uploadedAt=doc.uploaded_at)


# ─── Chat ─────────────────────────────────────────────────────────────────────

class Source(BaseModel):
    id: str
    documentName: str
    page: int
    snippet: str


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    createdAt: datetime
    sources: Optional[List[Source]] = None

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: str
    title: str
    updatedAt: datetime
    messages: List[MessageOut]

    class Config:
        from_attributes = True


class QueryRequest(BaseModel):
    conversationId: Optional[str] = None
    content: str


class QueryResponse(BaseModel):
    answer: str
    citations: List[Source]
    user: MessageOut
    ai: MessageOut
    conversation: ConversationOut
