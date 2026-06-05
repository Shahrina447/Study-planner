import asyncio
from httpx import AsyncClient
from main import app

async def test():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/chat", json={"message": "What is a 7 day study plan?"})
        print(response.status_code)
        print(response.text)

asyncio.run(test())
