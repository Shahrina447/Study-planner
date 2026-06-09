from fastapi import APIRouter

from rag.db import db


router = APIRouter()


@router.get("/health")
async def health_check():
    if not db.pool or not db.vector_enabled:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "pgvector": False,
        }

    async with db.pool.acquire() as conn:
        pgvector_version = await conn.fetchval(
            "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
        )
        await conn.fetchval("SELECT 1")

    return {
        "status": "healthy",
        "database": "connected",
        "pgvector": True,
        "pgvector_version": pgvector_version,
    }
