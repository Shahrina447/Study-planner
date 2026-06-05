# Atlas — Study Planner

**Chat with your own notes.**
A RAG-powered study assistant that grounds every answer in your uploaded course materials.

**Stack:** Next.js 15 · React 19 · Tailwind CSS v4 · FastAPI · Mistral AI · sentence-transformers

---

## Repository Structure

```
atlas/
├── frontend/                     # Next.js 15 application
│   ├── app/                      # App Router pages & layouts
│   │   ├── layout.tsx
│   │   ├── globals.css
│   │   ├── page.tsx              # Chat (home)
│   │   ├── documents/page.tsx    # Document upload & management
│   │   ├── quiz/page.tsx         # Auto-generated quizzes
│   │   ├── stress/page.tsx       # Stress relief & breathing
│   │   └── study-plan/page.tsx   # Daily schedule & deadlines
│   ├── src/
│   │   ├── components/
│   │   │   ├── AppShell.tsx      # Sidebar layout & navigation
│   │   │   ├── ChatView.tsx      # Chat interface with RAG controls
│   │   │   └── ui/               # Radix UI / shadcn primitives
│   │   ├── hooks/
│   │   │   └── use-mobile.tsx
│   │   └── lib/
│   │       └── utils.ts
│   ├── .env.example
│   ├── components.json           # shadcn/ui config
│   ├── next.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── backend/                      # FastAPI application
│   ├── main.py                   # App entry point & route handlers
│   ├── config.py                 # Pydantic settings (reads .env)
│   ├── rag/
│   │   ├── embedder.py           # SentenceTransformer singleton
│   │   ├── retriever.py          # Cosine similarity search
│   │   ├── db.py                 # asyncpg PostgreSQL pool
│   │   └── in_memory_db.py       # In-memory fallback vector store
│   ├── services/
│   │   ├── orchestrator.py       # AI / corpus / compare pipelines
│   │   └── pdf_extractor.py      # PyMuPDF text extraction
│   ├── scripts/
│   │   └── ingest.py             # Bulk PDF ingestion script
│   ├── study_materials/          # Pre-loaded reference PDFs
│   ├── .env.example
│   └── pyproject.toml
│
├── .gitignore
└── README.md
```

---

## How It Works

```
Upload Documents
      ↓
Text Chunking & Embedding
(PDFs split into chunks, embedded with all-MiniLM-L6-v2)
      ↓
RAG Retrieval
(Cosine similarity search against vector store)
      ↓
Context-Aware Generation
(Mistral synthesises answers from retrieved chunks)
      ↓
Adaptive Study Planning + Stress Monitoring
```

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.13+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — Python package manager
- PostgreSQL with pgvector *(optional — falls back to in-memory store)*

---

### Frontend

```bash
cd frontend

npm install
npm run dev
# → http://localhost:3000
```

---

### Backend

```bash
cd backend

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env and add your MISTRAL_API_KEY

# Start the API server
uv run uvicorn main:app --reload
# → http://localhost:8000
```

#### Environment variables (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `MISTRAL_API_KEY` | Yes | Your Mistral AI API key |
| `MISTRAL_MODEL` | No | Model name (default: `mistral-small-latest`) |
| `DATABASE_URL` | No | PostgreSQL connection string (omit for in-memory store) |
| `CORS_ORIGIN` | No | Frontend origin (default: `http://localhost:3000`) |

---

### Ingest pre-loaded study materials *(optional)*

```bash
cd backend
uv run python scripts/ingest.py
```

---

## Key Features

| Feature | Description |
|---|---|
| Grounded answers | Every response is cited from your uploaded documents |
| Three response modes | AI synthesis · Raw corpus · Side-by-side compare |
| Tunable retrieval | Adjustable Top-K and similarity threshold |
| Auto-generated quizzes | Questions ranked by difficulty, from your notes |
| Adaptive scheduling | Study blocks around peak hours |
| Stress detection | Guides 4-7-8 breathing when rapid questioning is detected |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend framework | Next.js 15 (App Router) |
| UI | React 19, Tailwind CSS v4, Radix UI |
| Icons | Lucide React |
| Backend framework | FastAPI |
| LLM | Mistral AI |
| Embeddings | `all-MiniLM-L6-v2` via sentence-transformers |
| Vector store | PostgreSQL + pgvector (in-memory fallback) |
| Python package manager | uv |

---

> Atlas is a study aid. Always verify critical information against your original course materials before exams.
