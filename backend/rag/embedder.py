from sentence_transformers import SentenceTransformer
import numpy as np

class Embedder:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Embedder, cls).__new__(cls)
            cls._instance.model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._instance

    def embed(self, text: str) -> list[float]:
        # Returns a 384-dimensional list of floats
        embedding = self.model.encode(text)
        return embedding.tolist()

embedder = Embedder()
