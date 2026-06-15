import asyncio
import json
from typing import Optional
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit

import asyncpg

from config import get_env_value


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _database_name(database_url: str) -> str:
    path = urlsplit(database_url).path.lstrip("/")
    return unquote(path.split("/", 1)[0])


def _url_for_database(database_url: str, database: str) -> str:
    parsed = urlsplit(database_url)
    path = "/" + quote(database)
    query = urlencode(parse_qsl(parsed.query, keep_blank_values=True))
    return urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            path,
            query,
            parsed.fragment,
        )
    )


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url: str | None = None
        self.vector_enabled = False

    async def connect(self):
        self.database_url = get_env_value("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is required.")

        try:
            await self._ensure_database_exists(self.database_url)
            self.pool = await asyncpg.create_pool(
                self.database_url,
                timeout=5,
                command_timeout=15,
            )
            await self.ensure_schema()
            print("Connected to PostgreSQL successfully.")
        except Exception as e:
            if self.pool:
                await self.pool.close()
                self.pool = None
            raise RuntimeError(f"PostgreSQL/pgvector startup failed: {e}") from e

    async def _ensure_database_exists(self, database_url: str) -> None:
        target_database = _database_name(database_url)
        if not target_database:
            raise ValueError("DATABASE_URL must include a database name.")

        maintenance_errors = []
        for maintenance_database in ("postgres", "template1"):
            maintenance_url = _url_for_database(database_url, maintenance_database)
            try:
                connection = await asyncpg.connect(maintenance_url, timeout=5)
                try:
                    exists = await connection.fetchval(
                        "SELECT 1 FROM pg_database WHERE datname = $1",
                        target_database,
                    )
                    if not exists:
                        await connection.execute(
                            f"CREATE DATABASE {_quote_identifier(target_database)}"
                        )
                        print(f"Created PostgreSQL database '{target_database}'.")
                    return
                finally:
                    await connection.close()
            except Exception as error:
                maintenance_errors.append(f"{maintenance_database}: {error}")

        raise RuntimeError(
            "Could not connect to a maintenance database to create "
            f"'{target_database}'. Attempts: {'; '.join(maintenance_errors)}"
        )

    async def ensure_schema(self):
        if not self.pool:
            return

        async with self.pool.acquire() as conn:
            await self._ensure_vector_extension(conn)
            self.vector_enabled = True
            await conn.execute(
                """
                DROP TABLE IF EXISTS legal_chunks;

                CREATE TABLE IF NOT EXISTS conversations (
                    id BIGSERIAL PRIMARY KEY,
                    title TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS corpus_chunks (
                    id BIGSERIAL PRIMARY KEY,
                    chunk_id TEXT UNIQUE,
                    source_file TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    category TEXT,
                    question TEXT,
                    topic TEXT,
                    risk_level TEXT,
                    title TEXT,
                    source_id TEXT,
                    allowed_use TEXT,
                    blocked_use TEXT,
                    language TEXT,
                    content TEXT NOT NULL,
                    embedding vector(384),
                    doc_type TEXT NOT NULL,
                    source_url TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                ALTER TABLE corpus_chunks ADD COLUMN IF NOT EXISTS topic TEXT;
                ALTER TABLE corpus_chunks ADD COLUMN IF NOT EXISTS risk_level TEXT;
                ALTER TABLE corpus_chunks ADD COLUMN IF NOT EXISTS title TEXT;
                ALTER TABLE corpus_chunks ADD COLUMN IF NOT EXISTS source_id TEXT;
                ALTER TABLE corpus_chunks ADD COLUMN IF NOT EXISTS allowed_use TEXT;
                ALTER TABLE corpus_chunks ADD COLUMN IF NOT EXISTS blocked_use TEXT;
                ALTER TABLE corpus_chunks ADD COLUMN IF NOT EXISTS language TEXT;

                CREATE TABLE IF NOT EXISTS messages (
                    id BIGSERIAL PRIMARY KEY,
                    conversation_id BIGINT NOT NULL
                        REFERENCES conversations(id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    mode TEXT,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            embedding_type = await self._ensure_vector_column(conn)
            if embedding_type != "vector":
                raise RuntimeError(
                    "corpus_chunks.embedding must use the pgvector vector type."
                )
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_corpus_chunks_source_file
                ON corpus_chunks (source_file);
                """
            )
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_corpus_chunks_doc_type
                ON corpus_chunks (doc_type);
                """
            )
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
                ON messages (conversation_id, created_at);
                """
            )
            await self._seed_csv_corpus(conn)
            await self._backfill_embeddings(conn)
            await self._ensure_vector_index(conn)

    async def _ensure_vector_column(self, conn) -> str | None:
        embedding_type = await conn.fetchval(
            """
            SELECT udt_name
            FROM information_schema.columns
            WHERE table_name = 'corpus_chunks'
              AND column_name = 'embedding'
            """
        )
        if embedding_type == "vector":
            return embedding_type

        try:
            await conn.execute(
                """
                ALTER TABLE corpus_chunks
                ALTER COLUMN embedding TYPE vector(384)
                USING CASE
                    WHEN embedding IS NULL OR embedding = '' THEN NULL
                    ELSE embedding::vector
                END
                """
            )
            return "vector"
        except Exception as error:
            raise RuntimeError(
                "Could not migrate corpus embeddings to pgvector."
            ) from error

    async def _seed_csv_corpus(self, conn) -> None:
        from services.research_corpus import research_corpus

        await asyncio.to_thread(research_corpus.load)
        if not research_corpus.rows:
            return

        await conn.execute(
            """
            DELETE FROM corpus_chunks
            WHERE doc_type = 'qa_corpus'
               OR source_file = 'qa_corpus.csv'
            """
        )
        await conn.executemany(
            """
            INSERT INTO corpus_chunks (
                chunk_id,
                source_file,
                chunk_index,
                category,
                question,
                topic,
                risk_level,
                title,
                source_id,
                allowed_use,
                blocked_use,
                language,
                content,
                doc_type,
                source_url
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                $13, 'mindbridge_corpus', $14
            )
            ON CONFLICT (chunk_id) DO UPDATE SET
                category = EXCLUDED.category,
                question = EXCLUDED.question,
                topic = EXCLUDED.topic,
                risk_level = EXCLUDED.risk_level,
                title = EXCLUDED.title,
                source_id = EXCLUDED.source_id,
                allowed_use = EXCLUDED.allowed_use,
                blocked_use = EXCLUDED.blocked_use,
                language = EXCLUDED.language,
                embedding = CASE
                    WHEN corpus_chunks.content IS DISTINCT FROM EXCLUDED.content
                    THEN NULL
                    ELSE corpus_chunks.embedding
                END,
                content = EXCLUDED.content,
                source_url = EXCLUDED.source_url
            """,
            [
                (
                    row["id"],
                    row["source_file"],
                    index,
                    row["category"],
                    row["question"],
                    row["topic"],
                    row["risk_level"],
                    row["title"],
                    row["source_id"],
                    row["allowed_use"],
                    row["blocked_use"],
                    row["language"],
                    row["content"],
                    row["source_url"],
                )
                for index, row in enumerate(research_corpus.rows)
            ],
        )

    async def _backfill_embeddings(self, conn) -> None:
        rows = await conn.fetch(
            """
            SELECT id, content
            FROM corpus_chunks
            WHERE embedding IS NULL
            ORDER BY id
            """
        )
        if not rows:
            return

        from rag.embedder import embedder

        embeddings = await embedder.embed_many([row["content"] for row in rows])
        await conn.executemany(
            """
            UPDATE corpus_chunks
            SET embedding = $1::vector
            WHERE id = $2
            """,
            [
                (json.dumps(embedding), row["id"])
                for row, embedding in zip(rows, embeddings, strict=True)
            ],
        )
        print(f"Generated vector embeddings for {len(rows)} corpus chunks.")

    async def _ensure_vector_index(self, conn) -> None:
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_corpus_chunks_embedding_hnsw
            ON corpus_chunks
            USING hnsw (embedding vector_cosine_ops);
            """
        )

    async def record_exchange(
        self,
        user_message: str,
        result: dict,
        mode: str,
        conversation_id: int | None = None,
    ) -> int | None:
        if not self.pool:
            return None

        assistant_content = self._assistant_content(result)
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                if conversation_id is not None:
                    exists = await conn.fetchval(
                        "SELECT 1 FROM conversations WHERE id = $1",
                        conversation_id,
                    )
                    if not exists:
                        conversation_id = None

                if conversation_id is None:
                    conversation_id = await conn.fetchval(
                        """
                        INSERT INTO conversations (title)
                        VALUES ($1)
                        RETURNING id
                        """,
                        user_message[:120],
                    )

                await conn.executemany(
                    """
                    INSERT INTO messages (
                        conversation_id, role, content, mode, metadata
                    )
                    VALUES ($1, $2, $3, $4, $5::jsonb)
                    """,
                    [
                        (
                            conversation_id,
                            "user",
                            user_message,
                            mode,
                            "{}",
                        ),
                        (
                            conversation_id,
                            "assistant",
                            assistant_content,
                            mode,
                            json.dumps(result, default=str),
                        ),
                    ],
                )
                await conn.execute(
                    """
                    UPDATE conversations
                    SET updated_at = NOW()
                    WHERE id = $1
                    """,
                    conversation_id,
                )
        return conversation_id

    async def list_conversations(self) -> list[dict]:
        if not self.pool:
            raise RuntimeError("PostgreSQL is not connected.")

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT conversations.id,
                       conversations.title,
                       conversations.created_at,
                       conversations.updated_at,
                       COUNT(messages.id) AS message_count
                FROM conversations
                LEFT JOIN messages
                  ON messages.conversation_id = conversations.id
                GROUP BY conversations.id
                ORDER BY conversations.updated_at DESC
                """
            )
        return [
            {
                "id": row["id"],
                "title": row["title"] or "Untitled chat",
                "message_count": row["message_count"],
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(),
            }
            for row in rows
        ]

    async def get_conversation(self, conversation_id: int) -> dict | None:
        if not self.pool:
            raise RuntimeError("PostgreSQL is not connected.")

        async with self.pool.acquire() as conn:
            conversation = await conn.fetchrow(
                """
                SELECT id, title, created_at, updated_at
                FROM conversations
                WHERE id = $1
                """,
                conversation_id,
            )
            if not conversation:
                return None

            messages = await conn.fetch(
                """
                SELECT id, role, content, mode, metadata, created_at
                FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at, id
                """,
                conversation_id,
            )

        return {
            "id": conversation["id"],
            "title": conversation["title"] or "Untitled chat",
            "created_at": conversation["created_at"].isoformat(),
            "updated_at": conversation["updated_at"].isoformat(),
            "messages": [
                {
                    "id": message["id"],
                    "role": message["role"],
                    "content": message["content"],
                    "mode": message["mode"],
                    "metadata": (
                        json.loads(message["metadata"])
                        if isinstance(message["metadata"], str)
                        else message["metadata"]
                    ),
                    "created_at": message["created_at"].isoformat(),
                }
                for message in messages
            ],
        }

    async def update_conversation(
        self,
        conversation_id: int,
        title: str,
    ) -> dict | None:
        if not self.pool:
            raise RuntimeError("PostgreSQL is not connected.")

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE conversations
                SET title = $2,
                    updated_at = NOW()
                WHERE id = $1
                RETURNING id, title, created_at, updated_at
                """,
                conversation_id,
                title,
            )
        if not row:
            return None
        return {
            "id": row["id"],
            "title": row["title"],
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
        }

    async def delete_conversation(self, conversation_id: int) -> bool:
        if not self.pool:
            raise RuntimeError("PostgreSQL is not connected.")

        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM conversations WHERE id = $1",
                conversation_id,
            )
        return result == "DELETE 1"

    def _assistant_content(self, result: dict) -> str:
        if result.get("response"):
            return str(result["response"])
        if result.get("ai_response") or result.get("corpus_response"):
            return "\n\n".join(
                part
                for part in (
                    str(result.get("ai_response") or ""),
                    str(result.get("corpus_response") or ""),
                )
                if part
            )
        return json.dumps(result, default=str)

    async def _ensure_vector_extension(self, conn) -> None:
        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        except Exception as error:
            raise RuntimeError(
                "The PostgreSQL pgvector extension is required."
            ) from error

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

db = Database()
