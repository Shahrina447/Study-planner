import numpy as np

class InMemoryDB:
    def __init__(self):
        self.chunks = []
        self.embeddings = []

    def add_chunk(self, source_file: str, content: str, embedding: list[float]):
        self.chunks.append({
            "source_file": source_file,
            "content": content
        })
        self.embeddings.append(embedding)

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        if not self.embeddings:
            return []
        
        query_vec = np.array(query_embedding)
        doc_vecs = np.array(self.embeddings)
        
        query_norm = np.linalg.norm(query_vec)
        doc_norms = np.linalg.norm(doc_vecs, axis=1)
        
        if query_norm == 0:
            return []
            
        similarities = np.dot(doc_vecs, query_vec) / (doc_norms * query_norm)
        
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            chunk = self.chunks[idx].copy()
            chunk["similarity"] = float(similarities[idx])
            results.append(chunk)
                
        return results

memory_db = InMemoryDB()
