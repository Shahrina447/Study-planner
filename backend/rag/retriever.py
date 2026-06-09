import json

from rag.db import db


class Retriever:
    async def search(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        source_file: str | None = None,
    ) -> list[dict]:
        if not db.pool or not db.vector_enabled:
            raise RuntimeError("PostgreSQL with pgvector is not available.")

        try:
            from rag.embedder import embedder

            query_embedding = await embedder.embed(query)
            async with db.pool.acquire() as conn:
                if source_file:
                    rows = await conn.fetch(
                        """
                        SELECT id, chunk_id, source_file, content, category,
                               risk_level, language,
                               1 - (embedding <=> $1::vector) AS similarity
                        FROM corpus_chunks
                        WHERE source_file = $4
                          AND embedding IS NOT NULL
                          AND 1 - (embedding <=> $1::vector) >= $3
                        ORDER BY embedding <=> $1::vector
                        LIMIT $2
                        """,
                        json.dumps(query_embedding),
                        top_k,
                        similarity_threshold,
                        source_file,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT id, chunk_id, source_file, content, category,
                               risk_level, language,
                               1 - (embedding <=> $1::vector) AS similarity
                        FROM corpus_chunks
                        WHERE embedding IS NOT NULL
                          AND 1 - (embedding <=> $1::vector) >= $3
                        ORDER BY embedding <=> $1::vector
                        LIMIT $2
                        """,
                        json.dumps(query_embedding),
                        top_k,
                        similarity_threshold,
                    )
                return [dict(r) for r in rows]
        except Exception as error:
            raise RuntimeError("pgvector retrieval failed.") from error


retriever = Retriever()
