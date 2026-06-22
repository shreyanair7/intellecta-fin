# Intellecta — Backend Setup Guide

## Architecture Overview

```
frontend (Vite + React)          backend (FastAPI)
http://localhost:5173   ←──────► http://localhost:8000
                                        │
                              ┌─────────┼─────────┐
                           SQLite    ChromaDB    Ollama
                          (users,   (vectors,  (llama3.2)
                          chats,    per user)
                          docs)
```

### Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| Database | SQLite via SQLAlchemy ORM |
| Auth | JWT (`python-jose`) + bcrypt (`passlib`) |
| Embeddings | `BAAI/bge-small-en-v1.5` (sentence-transformers) |
| Vector Store | ChromaDB (local persistent) |
| LLM | Ollama running `llama3.2` |
| Text Splitting | LangChain `RecursiveCharacterTextSplitter` |
| PDF Parsing | pypdf |

---

## Prerequisites

- **Python 3.10+**
- **Ollama** installed and running

---

## Step 1 — Install Ollama & pull the model

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model (one-time, ~2 GB)
ollama pull llama3.2

# Start Ollama server (runs on http://localhost:11434)
ollama serve
```

---

## Step 2 — Start the Backend

```bash
cd backend
chmod +x start_backend.sh
./start_backend.sh
```

This will:
1. Create a Python virtual environment in `backend/.venv`
2. Install all dependencies from `requirements.txt`
3. Auto-download the BGE embedding model on first run (~130 MB)
4. Start the API at `http://localhost:8000`

### Manual start (if you prefer)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

---

## Step 3 — Start the Frontend

```bash
# In the project root (separate terminal)
bun install
bun run dev
```

Frontend will be at `http://localhost:5173`.

---

## API Endpoints

### Auth
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register new user, returns JWT |
| `POST` | `/api/v1/auth/login` | Login, returns JWT |

### Documents
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/documents` | List user's documents |
| `POST` | `/api/v1/documents` | Upload & ingest document (multipart) |
| `DELETE` | `/api/v1/documents/{id}` | Delete document + vector chunks |

### Chat
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/chat/conversations` | List conversations |
| `POST` | `/api/v1/chat/conversations` | Create conversation |
| `GET` | `/api/v1/chat/conversations/{id}` | Get single conversation |
| `PATCH` | `/api/v1/chat/conversations/{id}` | Rename conversation |
| `DELETE` | `/api/v1/chat/conversations/{id}` | Delete conversation |
| `POST` | `/api/v1/chat/query` | RAG query → answer + citations |
| `GET` | `/api/v1/chat/report/{id}` | Download conversation as Markdown |

### Health
| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |

Interactive docs: `http://localhost:8000/docs`

---

## RAG Pipeline

```
User uploads PDF
      │
      ▼
pypdf extracts text
      │
      ▼
RecursiveCharacterTextSplitter
(chunk_size=1000, overlap=200)
      │
      ▼
BAAI/bge-small-en-v1.5 encodes chunks
      │
      ▼
ChromaDB upserts vectors
(metadata: user_id, document_id, filename)

─────────────────────────────────────────

User sends message
      │
      ▼
BGE encodes query
      │
      ▼
ChromaDB cosine similarity search
(filtered by user_id, top k=4)
      │
      ▼
Build prompt: system + context + question
      │
      ▼
Ollama llama3.2 generates answer
      │
      ▼
Return: { answer, citations, messages }
```

---

## File Structure

```
backend/
├── main.py                  # FastAPI app, CORS, router registration
├── requirements.txt
├── start_backend.sh
├── core/
│   ├── config.py            # Settings (env vars, paths, model names)
│   ├── database.py          # SQLAlchemy engine + session
│   ├── deps.py              # JWT auth dependency
│   └── security.py          # bcrypt + JWT utilities
├── models/
│   └── models.py            # User, Conversation, Message, Document ORM
├── schemas/
│   └── schemas.py           # Pydantic request/response schemas
├── routers/
│   ├── auth.py              # /auth/register, /auth/login
│   ├── documents.py         # /documents CRUD + ingestion
│   └── chat.py              # /chat conversations + RAG query + report
└── services/
    ├── embeddings.py        # BGE model (lazy-loaded singleton)
    ├── vector_store.py      # ChromaDB CRUD
    ├── llm.py               # Ollama HTTP client
    └── ingestion.py         # PDF→chunks→embed→upsert pipeline
```

---

## Environment Variables (optional `.env` in `backend/`)

```env
SECRET_KEY=your-secret-key-here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
EMBED_MODEL=BAAI/bge-small-en-v1.5
```

---

## Troubleshooting

**"Ollama is not running" in answers**
→ Run `ollama serve` in a terminal. The backend still works and returns an informative fallback message.

**ChromaDB / embedding errors on first run**
→ The BGE model downloads automatically. Allow ~1-2 minutes on first startup for the model cache to populate.

**CORS errors in the browser**
→ Make sure the backend is running on port 8000. The frontend calls `http://localhost:8000/api/v1`.

**`ModuleNotFoundError`**
→ Activate the virtualenv: `source backend/.venv/bin/activate` then re-run `uvicorn`.
