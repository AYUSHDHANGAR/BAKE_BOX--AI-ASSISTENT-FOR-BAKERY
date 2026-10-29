"""
Cross-Encoder Reranker using FlashRank (BAAI/bge-reranker-large / ms-marco cross-encoders).
Reranks hybrid RRF candidate passages.
"""
from flashrank import Ranker, RerankRequest

class CrossEncoderReranker:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            print("Initializing Cross-Encoder Reranker...")
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # Default lightweight high-performance cross encoder
        self.ranker = Ranker()

    def rerank(self, query: str, candidate_docs: list[dict], top_k: int = 5) -> list[dict]:
        if not candidate_docs:
            return []
        
        passages = [{"id": d["id"], "text": d["text"]} for d in candidate_docs]
        rerank_req = RerankRequest(query=query, passages=passages)
        ranked = self.ranker.rerank(rerank_req)

        # Map back to original candidate dicts preserving metadata
        doc_map = {d["id"]: d for d in candidate_docs}
        results = []
        for r in ranked[:top_k]:
            original = doc_map.get(r["id"])
            if original:
                item = dict(original)
                item["rerank_score"] = float(r.get("score", 0.0))
                results.append(item)
        return results
