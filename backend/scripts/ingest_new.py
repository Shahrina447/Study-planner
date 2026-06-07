"""
Ingest only PDFs that are not yet indexed in the database.
Run from the backend/ directory:
    python scripts/ingest_new.py
"""

import asyncio
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.db import db
from rag.embedder import embedder

STUDY_MATERIALS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "study_materials")
CHUNK_SIZE = 300  # words — matches the upload endpoint


def extract_pdf_text(path: str) -> str:
    import fitz
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    return text


def chunk_by_words(text: str, size: int = CHUNK_SIZE) -> list[str]:
    words = text.split()
    return [" ".join(words[i : i + size]) for i in range(0, len(words), size)]


async def main():
    await db.connect()

    if not db.pool:
        print("❌  Could not connect to PostgreSQL. Exiting.")
        return

    # Ensure table + extension exist
    async with db.pool.acquire() as conn:
        await conn.execute("""
            CREATE EXTENSION IF NOT EXISTS vector;
            CREATE TABLE IF NOT EXISTS legal_chunks (
                id SERIAL PRIMARY KEY,
                source_file TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding vector(384),
                doc_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # Fetch already-indexed filenames
        rows = await conn.fetch("SELECT DISTINCT source_file FROM legal_chunks")
        indexed = {r["source_file"] for r in rows}

    print(f"Already indexed: {indexed}\n")

    # Find PDFs not yet indexed
    all_pdfs = [f for f in os.listdir(STUDY_MATERIALS_DIR) if f.lower().endswith(".pdf")]
    new_pdfs = [f for f in all_pdfs if f not in indexed]

    if not new_pdfs:
        print("✅  All PDFs are already indexed. Nothing to do.")
        await db.disconnect()
        return

    print(f"New PDFs to index: {new_pdfs}\n")

    for filename in new_pdfs:
        path = os.path.join(STUDY_MATERIALS_DIR, filename)
        print(f"📄  Processing {filename} …")

        text = extract_pdf_text(path)
        text = text.replace("\x00", "")
        if not text.strip():
            print(f"   ⚠  No text extracted — skipping.")
            continue

        chunks = [c for c in chunk_by_words(text) if c.strip()]
        print(f"   {len(chunks)} chunks created")

        async with db.pool.acquire() as conn:
            for i, chunk in enumerate(chunks):
                chunk = chunk.replace("\x00", "")
                emb = embedder.embed(chunk)
                await conn.execute(
                    """
                    INSERT INTO legal_chunks (source_file, chunk_index, content, embedding, doc_type)
                    VALUES ($1, $2, $3, $4::vector, $5)
                    """,
                    filename, i, chunk, json.dumps(emb), "study_material",
                )

        print(f"   ✅  {filename} ingested ({len(chunks)} chunks)\n")

    await db.disconnect()
    print("🎉  Ingestion complete!")


if __name__ == "__main__":
    asyncio.run(main())
