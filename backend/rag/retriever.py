import json
from rag.db import db
from rag.embedder import embedder
from rag.in_memory_db import memory_db


class Retriever:
    async def search(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        source_file: str | None = None,
    ) -> list[dict]:
        if not db.pool:
            query_embedding = embedder.embed(query)
            results = memory_db.search(query_embedding, top_k)
            if similarity_threshold > 0:
                results = [r for r in results if r.get("similarity", 1.0) >= similarity_threshold]
            if source_file:
                results = [r for r in results if r["source_file"] == source_file]
            return results

        try:
            query_embedding = embedder.embed(query)
            async with db.pool.acquire() as conn:
                if source_file:
                    rows = await conn.fetch(
                        """
                        SELECT id, source_file, content,
                               1 - (embedding <=> $1::vector) AS similarity
                        FROM legal_chunks
                        WHERE source_file = $4
                          AND 1 - (embedding <=> $1::vector) >= $3
                        ORDER BY embedding <=> $1::vector
                        LIMIT $2
                        """,
                        json.dumps(query_embedding), top_k, similarity_threshold, source_file,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT id, source_file, content,
                               1 - (embedding <=> $1::vector) AS similarity
                        FROM legal_chunks
                        WHERE 1 - (embedding <=> $1::vector) >= $3
                        ORDER BY embedding <=> $1::vector
                        LIMIT $2
                        """,
                        json.dumps(query_embedding), top_k, similarity_threshold,
                    )
                return [dict(r) for r in rows]
        except Exception as e:
            print(f"Error during retrieval: {e}")
            return []


retriever = Retriever()
