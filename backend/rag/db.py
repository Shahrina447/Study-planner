import asyncpg
from typing import Optional
from config import settings

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        if not settings.DATABASE_URL:
            print("WARNING: DATABASE_URL not set. Running in fallback mode.")
            return

        try:
            self.pool = await asyncpg.create_pool(settings.DATABASE_URL)
            print("Connected to PostgreSQL successfully.")
        except Exception as e:
            print(f"Failed to connect to DB: {e}. Running in fallback mode.")

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

db = Database()
