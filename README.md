<div align="center">

# MindBridge-RAG

### A Safety-Aware Retrieval-Augmented Generation Assistant for Student Wellbeing

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791?style=flat&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Mistral AI](https://img.shields.io/badge/Mistral-AI-FF7000?style=flat)](https://mistral.ai)

*Upload your study materials · Ask questions · Get grounded, cited answers · Stay safe*

</div>

---

## Overview

MindBridge-RAG is an academic support assistant that combines **Retrieval-Augmented Generation (RAG)** with a multi-tier safety classification system. Students upload their own documents and receive answers grounded exclusively in that material — not from a generic, unchecked internet corpus.

The project includes a comparative evaluation of three chatbot architectures (S0, S1, S2) to measure how retrieval and safety guardrails affect response quality, groundedness, and student wellbeing.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js 15)                   │
│   Chat · Document Upload · Quiz Generator · Study Planner       │
└───────────────────────────┬─────────────────────────────────────┘
                            │ REST API
┌───────────────────────────▼─────────────────────────────────────┐
│                        Backend (FastAPI)                         │
│                                                                  │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────────┐  │
│  │   Retriever  │   │ Orchestrator │   │  Safety Classifier   │  │
│  │  (pgvector)  │◄──│  S0 · S1 · S2│──►│  L0 → L5 Risk Labels│  │
│  └──────┬───────┘   └──────┬───────┘   └──────────────────────┘  │
│         │                  │                                      │
│  ┌──────▼───────┐   ┌──────▼───────┐                             │
│  │   Embedder   │   │  Mistral AI  │                             │
│  │ MiniLM-L6-v2 │   │     LLM      │                             │
│  └──────────────┘   └──────────────┘                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│              PostgreSQL + pgvector (Vector Store)                │
│         corpus_chunks · conversations · messages                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## How RAG Works in This Project

```
1. Upload PDF / DOCX
        │
        ▼
2. Extract text  →  Split into 300-word chunks
        │
        ▼
3. Embed each chunk  →  384-dimensional vector (all-MiniLM-L6-v2)
        │
        ▼
4. Store vectors in PostgreSQL (pgvector, HNSW index)
        │
   ─────────────────────────────────────────
        │  At query time:
        ▼
5. Embed user question  →  384-dim vector
        │
        ▼
6. Cosine similarity search  →  Top-K most relevant chunks
        │
        ▼
7. Inject chunks into Mistral prompt  →  Grounded answer
        │
        ▼
8. Return answer + source citations + chunk metadata
```

---

## Chatbot Systems Compared

| System | Description | Uses RAG | Safety Guardrails |
|--------|-------------|----------|-------------------|
| **S0** — Basic Chatbot | Mistral with a safety-aware prompt only | ✗ | Prompt-level rules |
| **S1** — Basic RAG | Mistral grounded in retrieved chunks; may supplement with general knowledge | ✓ | Pre-flight risk block |
| **S2** — Safety-Aware RAG | Mistral strictly limited to retrieved corpus; full risk classification applied | ✓ | Full L0–L5 pipeline |
| **Corpus** | Raw retrieval snapshot — no LLM synthesis | ✓ | Risk block |

Use **Compare Systems** mode in the UI to see all four responses side-by-side for any query.

---

## Safety Classification (L0 → L5)

Every message is classified before reaching the LLM.

| Label | Risk Level | Example Trigger | Response |
|-------|-----------|-----------------|----------|
| `L0_NORMAL` | None | "Help me study calculus" | Full RAG response |
| `L1_STRESS` | Low | "I'm nervous about my exam" | RAG response, calm tone |
| `L2_DISTRESS` | Moderate | "I can't cope anymore" | RAG response + counselor reminder |
| `L3_CRISIS` | High | "I want to hurt myself" | Hard block → emergency services |
| `L4_MEDICAL` | High | "Do I have depression?" | Hard block → clinician referral |
| `L5_OUT_OF_SCOPE` | High | "How to make a bomb" | Hard block → polite refusal |

L3, L4, and L5 queries never reach Mistral. A hard-coded safe response is returned immediately.

---

## Key Features

| Feature | Detail |
|---------|--------|
| **Grounded answers** | Every response is cited from uploaded documents |
| **Three RAG modes** | AI synthesis · Corpus-only · Side-by-side comparison |
| **Safety-first design** | Six-tier risk classifier blocks harmful queries before LLM call |
| **Auto quiz generation** | MCQ-style questions ranked Easy / Medium / Hard from your notes |
| **Conversation history** | Full chat sessions stored in PostgreSQL |
| **Tunable retrieval** | Adjustable Top-K and similarity threshold from the UI |
| **Benchmark evaluation** | Precision@3, Recall@5, MRR, plus human evaluation scores |
| **Async throughout** | FastAPI + asyncpg + async Mistral client — non-blocking stack |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15 (App Router), React 19, Tailwind CSS v4 |
| UI Components | Radix UI, shadcn/ui, Lucide React |
| Backend | FastAPI, Python 3.13 |
| LLM | Mistral AI (`mistral-small-latest`) |
| Embeddings | `all-MiniLM-L6-v2` via sentence-transformers (384-dim) |
| Vector Store | PostgreSQL + pgvector (HNSW index, cosine similarity) |
| Database Driver | asyncpg |
| Package Manager | uv |

---

## Project Structure

```
mindbridge-rag/
├── frontend/                        # Next.js 15 application
│   ├── app/
│   │   ├── page.tsx                 # Chat interface (home)
│   │   ├── documents/page.tsx       # Document upload & management
│   │   ├── quiz/page.tsx            # Auto-generated quizzes
│   │   └── study-plan/page.tsx      # Daily schedule & deadlines
│   └── src/
│       └── components/
│           ├── AppShell.tsx         # Sidebar navigation
│           └── ChatView.tsx         # Chat UI with RAG controls
│
├── backend/
│   ├── main.py                      # FastAPI entry point
│   ├── config.py                    # Pydantic settings
│   ├── rag/
│   │   ├── embedder.py              # Async SentenceTransformer wrapper
│   │   ├── retriever.py             # pgvector cosine similarity search
│   │   └── db.py                    # asyncpg connection pool & schema
│   ├── services/
│   │   ├── orchestrator.py          # S0 / S1 / S2 / compare pipelines
│   │   ├── document_service.py      # Upload, chunk, embed, store
│   │   ├── quiz_service.py          # Quiz generation via Mistral
│   │   └── research_corpus.py       # MindBridge CSV corpus loader
│   ├── api/routes/
│   │   ├── chat.py                  # /chat and /chat/compare-systems
│   │   ├── documents.py             # /documents CRUD
│   │   ├── quiz.py                  # /quiz/generate
│   │   └── health.py                # /health
│   ├── scripts/
│   │   ├── build_mindbridge_dataset.py   # Build evaluation CSVs from QA corpus
│   │   ├── validate_mindbridge_dataset.py
│   │   ├── embed_corpus.py
│   │   ├── run_benchmark.py              # Run S0/S1/S2 benchmark tests
│   │   └── compute_evaluation_metrics.py # Compute Precision, Recall, MRR
│   └── data/                        # MindBridge evaluation CSV files
│
└── mindbridge_rag_templates/        # Group submission templates
```

---

## Getting Started

### Prerequisites

- **Node.js** 18+
- **Python** 3.13+
- **PostgreSQL** with the [pgvector](https://github.com/pgvector/pgvector) extension
- **uv** — Python package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))

---

### 1. Backend Setup

```bash
cd backend

# Install dependencies
uv sync

# Configure environment variables
cp .env.example .env
```

Edit `backend/.env`:

```env
MISTRAL_API_KEY=your_mistral_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/mindbridge
MISTRAL_MODEL=mistral-small-latest
CORS_ORIGIN=http://localhost:3000
```

```bash
# Start the API server
uv run uvicorn main:app --reload
# → http://localhost:8000
```

#### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MISTRAL_API_KEY` | ✓ | — | Mistral AI API key |
| `DATABASE_URL` | ✓ | — | PostgreSQL connection string (pgvector required) |
| `MISTRAL_MODEL` | ✗ | `mistral-small-latest` | Mistral model to use |
| `CORS_ORIGIN` | ✗ | `http://localhost:3000` | Allowed frontend origin |

---

### 2. Frontend Setup

```bash
cd frontend

npm install
npm run dev
# → http://localhost:3000
```

---

### 3. Ingest Study Materials *(optional)*

Pre-load reference PDFs from the `backend/study_materials/` directory:

```bash
cd backend
uv run python scripts/ingest.py
```

---

### 4. Build the Evaluation Dataset

```bash
cd backend

# Step 1 — Build MindBridge CSVs from QA corpus
uv run python scripts/build_mindbridge_dataset.py

# Step 2 — Validate the generated files
uv run python scripts/validate_mindbridge_dataset.py

# Step 3 — Generate embeddings for corpus chunks
uv run python scripts/embed_corpus.py

# Step 4 — Run S0 / S1 / S2 benchmark
uv run python scripts/run_benchmark.py

# Step 5 — Compute final metrics (Precision, Recall, MRR, etc.)
uv run python scripts/compute_evaluation_metrics.py
```

Results are written to `backend/data/mindbridge_final_results.csv`.

---

## Evaluation Metrics

### Retrieval Metrics (S1, S2)

| Metric | Description |
|--------|-------------|
| **Precision@3** | Fraction of top-3 retrieved chunks that are relevant |
| **Recall@5** | Fraction of all relevant chunks found in the top-5 results |
| **MRR** | Mean Reciprocal Rank — how highly the first correct chunk is ranked |

### Human Evaluation (1–5 scale)

| Score | Description |
|-------|-------------|
| **Relevance** | Does the answer address the question? |
| **Helpfulness** | Is the answer practically useful to a student? |
| **Faithfulness** | Is the answer grounded in the retrieved documents? |
| **Safety** | Does the answer avoid harmful or inappropriate content? |
| **Clarity** | Is the answer well-structured and easy to understand? |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/chat` | Send a message (modes: `ai`, `corpus`, `compare`) |
| `POST` | `/chat/compare-systems` | Run S0 / S1 / S2 side-by-side comparison |
| `GET` | `/documents` | List all indexed documents |
| `POST` | `/documents/upload` | Upload and index a PDF or DOCX |
| `DELETE` | `/documents/{filename}` | Remove a document and its chunks |
| `POST` | `/quiz/generate` | Generate quiz questions from indexed content |
| `GET` | `/conversations` | List all saved conversations |
| `GET` | `/conversations/{id}` | Retrieve a full conversation |

---

## Disclaimer

MindBridge-RAG is an educational support tool built for academic research purposes. It is **not** a substitute for professional medical advice, mental health therapy, or emergency services. If you or someone you know is in crisis, please contact your local emergency number or a qualified counselor immediately.

---

<div align="center">
  <sub>Built with FastAPI · Next.js · Mistral AI · pgvector</sub>
</div>
