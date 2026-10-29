"""
Dense and Sparse Embedding Engines for BAKEBOX Hybrid RAG.
Dense: HuggingFace BAAI/bge-small-en-v1.5 (384 dimensions) via fastembed.
Sparse: Scikit-learn TF-IDF Vectorizer fitted across catalog and policy chunks.
"""
import numpy as np
from fastembed import TextEmbedding
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class DenseEmbeddingEngine:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            print("Initializing Dense Embedding Engine: BAAI/bge-small-en-v1.5...")
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    def embed_query(self, query: str) -> np.ndarray:
        embeddings = list(self.model.embed([query]))
        return np.array(embeddings[0], dtype=np.float32)

    def embed_documents(self, documents: list[str]) -> list[np.ndarray]:
        embeddings = list(self.model.embed(documents, batch_size=64))
        return [np.array(e, dtype=np.float32) for e in embeddings]


class SparseTFIDFEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b\w+\b"
        )
        self.tfidf_matrix = None
        self.doc_ids = []

    def fit(self, doc_ids: list[str], texts: list[str]):
        self.doc_ids = doc_ids
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)

    def search(self, query: str, top_k: int = 25) -> list[tuple[str, float]]:
        if self.tfidf_matrix is None or not self.doc_ids:
            return []
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score > 0.001:
                results.append((self.doc_ids[idx], score))
        return results
