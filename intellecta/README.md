# Intellecta

Intellecta is an AI-powered document intelligence platform that enables users to interact with uploaded documents through natural language conversations. Built using a Retrieval-Augmented Generation (RAG) architecture, it combines semantic search, vector databases, and local large language models to provide accurate, context-aware, and citation-backed responses.

---

## Features

- Secure user authentication using JWT
- Upload and manage documents
- Support for PDF, DOCX, TXT, and Markdown files
- Retrieval-Augmented Generation (RAG) pipeline
- Semantic document search using vector embeddings
- Conversational AI powered by Ollama (Llama 3.2)
- Multi-turn conversation support
- Context-aware query rewriting
- Intent-based query routing
- Hybrid retrieval re-ranking
- Similarity-based result filtering
- Dynamic citation generation
- User-specific document isolation
- Fully local AI inference for enhanced privacy

---

## Tech Stack

### Frontend

- Next.js
- TypeScript
- Tailwind CSS

### Backend

- FastAPI
- SQLAlchemy
- SQLite
- JWT Authentication

### AI & Retrieval

- Ollama
- Llama 3.2
- ChromaDB
- BAAI/bge-small-en-v1.5
- Recursive Character Text Splitting

### Document Processing

- PyPDF
- Python-Docx

---

## Architecture

```text
User Query
    ↓
Intent Router
    ↓
Query Rewriter
    ↓
Embedding Generation
    ↓
ChromaDB Vector Search
    ↓
Hybrid Re-ranking
    ↓
Similarity Filtering
    ↓
Context Selection
    ↓
Ollama (Llama 3.2)
    ↓
Response Generation
    ↓
Dynamic Citations
```

![Architecture Diagram](./intellecta/assets/arch-diagram.png)

---

## Core Functionalities

### 1. User Authentication
Secure onboarding interface allowing users to register and access their private document environments.

![User Registration Interface](./intellecta/assets/register.png)

### 2. Document Intelligence & Chat
Main workspace workspace where users manage uploaded files and initiate conversational sessions.

![Main Chat Interface](./intellecta/assets/chat.png)

### 3. Retrieval Optimization & Responses
Context-aware generated outputs completed with dynamic source citations based on semantic matching thresholds.

![Chatbot Response Demo](./intellecta/assets/chatbot-response.png)

---

## RAG Pipeline

### 1. Document Upload

Supported formats:

- PDF
- DOCX
- TXT
- Markdown

### 2. Text Processing

- Content extraction
- Recursive text chunking
- Metadata generation

### 3. Embedding Generation

- BAAI/bge-small-en-v1.5 embeddings
- Semantic vector representation

### 4. Vector Storage

- ChromaDB indexing
- User-aware document segregation

### 5. Retrieval

- Semantic similarity search
- Hybrid re-ranking
- Similarity filtering

### 6. Response Generation

- Context injection
- Ollama-powered answer generation
- Dynamic source citations

---

## Key Enhancements Implemented

- Intent-based routing system
- Conversational query rewriting
- Hybrid retrieval re-ranking
- Similarity threshold filtering
- Dynamic citation generation
- Multi-format document support
- Improved retrieval relevance
- Enhanced response grounding

---

## Future Enhancements

- Page-level citations
- BM25 + Vector Fusion retrieval
- OCR support for scanned PDFs
- Voice-based interaction
- Role-based access control
- Analytics dashboard
- Multi-user collaborative workspaces
- Advanced retrieval strategies

---

## Outcome

Intellecta demonstrates the practical application of Retrieval-Augmented Generation for document intelligence. By combining semantic search, vector databases, conversational AI, and local LLM deployment, it provides accurate, explainable, and context-aware interactions with user-uploaded knowledge sources.