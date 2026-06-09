import asyncio
import os
import sys
import json

# Add parent directory to path so we can import from rag & services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.db import db
from rag.embedder import embedder
from services.pdf_extractor import pdf_extractor

STUDY_MATERIALS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "study_materials")

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """Splits text into overlapping chunks of characters."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

async def ingest_documents():
    print(f"Reading documents from {STUDY_MATERIALS_DIR}...")
    
    # Connect to DB
    await db.connect()
    if not db.pool:
        print("Database not connected. Exiting ingestion.")
        return

    # Iterate over files
    filenames = await asyncio.to_thread(os.listdir, STUDY_MATERIALS_DIR)
    for filename in filenames:
        if not filename.endswith(".pdf"):
            continue
            
        file_path = os.path.join(STUDY_MATERIALS_DIR, filename)
        print(f"Processing {filename}...")
        
        # 1. Extract text
        text = await asyncio.to_thread(pdf_extractor.extract_text, file_path)
        if not text:
            print(f"  Warning: No text extracted from {filename}")
            continue
            
        # 2. Chunk text
        chunks = chunk_text(text)
        print(f"  Created {len(chunks)} chunks.")
        
        # 3. Embed and Insert
        embeddings = await embedder.embed_many(chunks)
        async with db.pool.acquire() as conn:
            await conn.executemany(
                """
                    INSERT INTO corpus_chunks (source_file, chunk_index, content, embedding, doc_type)
                    VALUES ($1, $2, $3, $4::vector, $5)
                """,
                [
                    (
                        filename,
                        index,
                        chunk,
                        json.dumps(embedding),
                        "study_note",
                    )
                    for index, (chunk, embedding) in enumerate(
                        zip(chunks, embeddings, strict=True)
                    )
                ],
            )
        
        print(f"  Successfully ingested {filename}!")
        
    await db.disconnect()
    print("Ingestion complete!")

if __name__ == "__main__":
    asyncio.run(ingest_documents())
