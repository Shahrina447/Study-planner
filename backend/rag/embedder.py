import asyncio

from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self) -> None:
        self._model: SentenceTransformer | None = None
        self._lock = asyncio.Lock()

    async def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = await asyncio.to_thread(
                SentenceTransformer,
                "all-MiniLM-L6-v2",
            )
        return self._model

    async def embed(self, text: str) -> list[float]:
        embeddings = await self.embed_many([text])
        return embeddings[0]

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        async with self._lock:
            model = await self._get_model()
            embeddings = await asyncio.to_thread(
                model.encode,
                texts,
                batch_size=32,
                show_progress_bar=False,
            )
        return embeddings.tolist()


embedder = Embedder()
