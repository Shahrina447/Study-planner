"""Create pgvector embeddings for corpus rows that do not have one yet."""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.db import db


async def main() -> None:
    await db.connect()
    if not db.pool:
        raise SystemExit("Could not connect to PostgreSQL.")
    if not db.vector_enabled:
        await db.disconnect()
        raise SystemExit("The PostgreSQL vector extension is not available.")

    async with db.pool.acquire() as conn:
        await db._backfill_embeddings(conn)
        await db._ensure_vector_index(conn)
        total = await conn.fetchval("SELECT COUNT(*) FROM corpus_chunks")
        embedded = await conn.fetchval(
            "SELECT COUNT(*) FROM corpus_chunks WHERE embedding IS NOT NULL"
        )
        embedding_type = await conn.fetchval(
            """
            SELECT format_type(attribute.atttypid, attribute.atttypmod)
            FROM pg_attribute AS attribute
            JOIN pg_class AS table_info ON table_info.oid = attribute.attrelid
            WHERE table_info.relname = 'corpus_chunks'
              AND attribute.attname = 'embedding'
              AND attribute.attnum > 0
            """
        )
        vector_index = await conn.fetchval(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'corpus_chunks'
              AND indexname = 'idx_corpus_chunks_embedding_hnsw'
            """
        )

    await db.disconnect()
    print(f"Embedded corpus chunks: {embedded}/{total}")
    print(f"Embedding column: {embedding_type}")
    print(f"Vector index: {vector_index or 'missing'}")


if __name__ == "__main__":
    asyncio.run(main())
