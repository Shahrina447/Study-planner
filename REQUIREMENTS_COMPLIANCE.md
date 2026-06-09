# MindBridge-RAG Requirements Compliance

## Implemented

- S0 basic chatbot, S1 pgvector RAG, and S2 safety-aware RAG comparison
- L0-L5 risk classification with crisis, medical, and out-of-scope bypasses
- Explicit human-support recommendation for L2 distress
- PostgreSQL pgvector `vector(384)` embeddings and HNSW cosine index
- Asynchronous FastAPI routes, asyncpg access, model calls, and non-blocking
  embedding/document processing
- Required CSV schemas for sources, corpus, questions, ideal answers, labels,
  responses, human evaluation, and final results
- 50 linked corpus chunks, questions, ideal answers, and risk labels
- Exact chunk IDs returned by retrieval
- Per-system response latency returned by the comparison API
- Persistent conversations with list, reopen, rename, and delete support
- Repeatable dataset build and validation scripts

## Requires Human Completion

- At least 15 real S0/S1/S2 model-response test records
- At least 15 human evaluations scored from 1 to 5
- Final retrieval and safety metrics based on those evaluations
- Group member names, roll numbers, contribution statements, and submission date
- Final source-quality/ethics approval by the instructor
- 8-10 presentation slides

These items require actual testing, human judgment, or student identity data and
must not be generated as fictional results.
