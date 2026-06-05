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

    # Create table if it doesn't exist
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

    # Iterate over files
    for filename in os.listdir(STUDY_MATERIALS_DIR):
        if not filename.endswith(".pdf"):
            continue
            
        file_path = os.path.join(STUDY_MATERIALS_DIR, filename)
        print(f"Processing {filename}...")
        
        # 1. Extract text
        text = pdf_extractor.extract_text(file_path)
        if not text:
            print(f"  Warning: No text extracted from {filename}")
            continue
            
        # 2. Chunk text
        chunks = chunk_text(text)
        print(f"  Created {len(chunks)} chunks.")
        
        # 3. Embed and Insert
        async with db.pool.acquire() as conn:
            for i, chunk in enumerate(chunks):
                embedding = embedder.embed(chunk)
                await conn.execute("""
                    INSERT INTO legal_chunks (source_file, chunk_index, content, embedding, doc_type)
                    VALUES ($1, $2, $3, $4::vector, $5)
                """, filename, i, chunk, json.dumps(embedding), "study_note")
        
        print(f"  Successfully ingested {filename}!")
        
    await db.disconnect()
    print("Ingestion complete!")

if __name__ == "__main__":
    asyncio.run(ingest_documents())
