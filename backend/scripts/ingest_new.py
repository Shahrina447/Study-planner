"""
Ingest corpus data into the database.

Handles two sources:
  1. qa_corpus.csv  — the MindBridge QA corpus in backend/qa_corpus.csv
  2. PDFs           — study material PDFs in backend/study_materials/

Run from the backend/ directory:
    uv run python scripts/ingest_new.py
"""

import asyncio
import csv
import json
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.db import db
from rag.embedder import embedder

BACKEND_DIR = Path(__file__).resolve().parent.parent
STUDY_MATERIALS_DIR = BACKEND_DIR / "study_materials"
QA_CORPUS_PATH = BACKEND_DIR / "qa_corpus.csv"
CHUNK_SIZE = 300  # words — matches the upload endpoint


# ── PDF helpers ───────────────────────────────────────────────────────────────

def extract_pdf_text(path: str) -> str:
    import fitz
    doc = fitz.open(path)
    return "\n".join(page.get_text() for page in doc)


def chunk_by_words(text: str, size: int = CHUNK_SIZE) -> list[str]:
    words = text.split()
    return [" ".join(words[i : i + size]) for i in range(0, len(words), size)]


# ── CSV corpus ingestion ──────────────────────────────────────────────────────

async def ingest_qa_corpus(conn) -> None:
    if not QA_CORPUS_PATH.exists():
        print(f"⚠  {QA_CORPUS_PATH} not found — skipping CSV ingestion.")
        return

    print(f"📋  Reading {QA_CORPUS_PATH.name} …")

    rows = []
    with QA_CORPUS_PATH.open(newline="", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.DictReader(f), 1):
            question = (row.get("Question") or "").strip()
            answer   = (row.get("Detailed Answer") or "").strip()
            if not question and not answer:
                continue

            row_num  = (row.get("#") or str(i)).strip() or str(i)
            chunk_id = f"QA_{int(row_num):03d}" if row_num.isdigit() else f"QA_{i:03d}"
            category = (row.get("Category") or "Research Corpus").strip()
            summary  = (row.get("Key Points (Summary)") or "").strip()
            source   = (row.get("Source / URL") or "qa_corpus.csv").strip()

            content = "\n".join(filter(None, [
                f"Category: {category}",
                f"Research question: {question}",
                f"Detailed answer: {answer}",
                f"Key points: {summary}" if summary else "",
                f"Source: {source}",
            ]))

            rows.append((
                chunk_id,       # chunk_id
                "qa_corpus.csv",# source_file
                i,              # chunk_index
                category,       # category
                question,       # question
                category,       # topic
                "L0_NORMAL",    # risk_level
                question.rstrip("?"),  # title
                "",             # source_id
                "Academic and study support",  # allowed_use
                "Diagnosis; medication; clinical treatment",  # blocked_use
                "English",      # language
                content,        # content
                source,         # source_url
            ))

    if not rows:
        print("   ⚠  No valid rows found in qa_corpus.csv.")
        return

    print(f"   {len(rows)} rows loaded — generating embeddings …")
    contents = [r[12] for r in rows]  # content is index 12
    embeddings = await embedder.embed_many(contents)

    # Delete stale qa_corpus rows then re-insert fresh
    await conn.execute(
        "DELETE FROM corpus_chunks WHERE source_file = 'qa_corpus.csv'"
    )

    await conn.executemany(
        """
        INSERT INTO corpus_chunks (
            chunk_id, source_file, chunk_index, category, question,
            topic, risk_level, title, source_id, allowed_use, blocked_use,
            language, content, doc_type, source_url, embedding
        ) VALUES (
            $1, $2, $3, $4, $5,
            $6, $7, $8, $9, $10, $11,
            $12, $13, 'qa_corpus', $14, $15::vector
        )
        ON CONFLICT (chunk_id) DO UPDATE SET
            content    = EXCLUDED.content,
            embedding  = EXCLUDED.embedding,
            category   = EXCLUDED.category,
            question   = EXCLUDED.question,
            source_url = EXCLUDED.source_url
        """,
        [
            (*row, json.dumps(emb))
            for row, emb in zip(rows, embeddings, strict=True)
        ],
    )
    print(f"   ✅  {len(rows)} qa_corpus chunks upserted.\n")


# ── PDF ingestion ─────────────────────────────────────────────────────────────

async def ingest_pdfs(conn) -> None:
    if not STUDY_MATERIALS_DIR.exists():
        print("⚠  study_materials/ directory not found — skipping PDF ingestion.")
        return

    indexed_rows = await conn.fetch(
        "SELECT DISTINCT source_file FROM corpus_chunks WHERE doc_type = 'study_material'"
    )
    indexed = {r["source_file"] for r in indexed_rows}

    all_pdfs = [f.name for f in STUDY_MATERIALS_DIR.iterdir() if f.suffix.lower() == ".pdf"]
    new_pdfs = [f for f in all_pdfs if f not in indexed]

    if not new_pdfs:
        print("✅  All PDFs are already indexed.")
        return

    print(f"📄  New PDFs to index: {new_pdfs}\n")

    for filename in new_pdfs:
        path = str(STUDY_MATERIALS_DIR / filename)
        print(f"   Processing {filename} …")

        text = await asyncio.to_thread(extract_pdf_text, path)
        text = text.replace("\x00", "")
        if not text.strip():
            print(f"   ⚠  No text extracted — skipping.")
            continue

        chunks = [c for c in chunk_by_words(text) if c.strip()]
        print(f"   {len(chunks)} chunks — generating embeddings …")
        embeddings = await embedder.embed_many(chunks)

        await conn.executemany(
            """
            INSERT INTO corpus_chunks (source_file, chunk_index, content, embedding, doc_type)
            VALUES ($1, $2, $3, $4::vector, $5)
            """,
            [
                (filename, i, chunk.replace("\x00", ""), json.dumps(emb), "study_material")
                for i, (chunk, emb) in enumerate(zip(chunks, embeddings, strict=True))
            ],
        )
        print(f"   ✅  {filename} ingested ({len(chunks)} chunks)\n")


# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    print("Connecting to PostgreSQL …")
    await db.connect()

    if not db.pool:
        print("❌  Could not connect to PostgreSQL. Check DATABASE_URL in backend/.env")
        return

    async with db.pool.acquire() as conn:
        await ingest_qa_corpus(conn)
        await ingest_pdfs(conn)

    await db.disconnect()
    print("🎉  Ingestion complete!")


if __name__ == "__main__":
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
