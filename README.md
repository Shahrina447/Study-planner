# MindBridge-RAG Study Planner

An asynchronous safety-aware RAG assistant for student wellbeing and academic
support, with S0, S1, and S2 comparison.

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
│   │   ├── embedder.py           # Async SentenceTransformer wrapper
│   │   ├── retriever.py          # pgvector cosine similarity search
│   │   └── db.py                 # asyncpg PostgreSQL/pgvector pool
│   ├── services/
│   │   ├── orchestrator.py       # AI / corpus / compare pipelines
│   │   └── pdf_extractor.py      # PyMuPDF text extraction
│   ├── scripts/
│   │   └── ingest.py             # Bulk PDF ingestion script
│   ├── study_materials/          # Pre-loaded reference PDFs
│   ├── .env.example
│   └── pyproject.toml
│
├── backend/data/                 # Integrated MindBridge CSV files
├── mindbridge_rag_templates/     # Required group submission templates
├── requirements/                 # Official project manual
├── REQUIREMENTS_COMPLIANCE.md
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
- PostgreSQL with pgvector *(required)*

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
| `DATABASE_URL` | Yes | PostgreSQL connection string with pgvector available |
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
| Vector store | PostgreSQL + pgvector |
| Database access | asyncpg |
| Python package manager | uv |

---

## Dataset Validation

```bash
cd backend
uv run python scripts/build_mindbridge_dataset.py
uv run python scripts/validate_mindbridge_dataset.py
uv run python scripts/embed_corpus.py
```

See `REQUIREMENTS_COMPLIANCE.md` for completed and human-owned deliverables.

> MindBridge-RAG is an educational support tool, not a medical, therapy, or
> emergency service.
