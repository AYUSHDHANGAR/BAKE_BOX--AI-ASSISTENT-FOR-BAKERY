"""
Corrective RAG (CRAG) Pipeline Module.
Implements Retrieval Evaluation, Query Transformation, and Corrective Fallback Retrieval.
"""
import re

class CorrectiveRAGEvaluator:
    def __init__(self, confidence_threshold: float = 0.25):
        self.confidence_threshold = confidence_threshold

    def evaluate_retrieval(self, query: str, retrieved_docs: list[dict]) -> tuple[str, list[dict]]:
        """
        Grades the retrieved documents.
        Returns (status: 'CORRECT' | 'AMBIGUOUS' | 'INCORRECT', processed_docs)
        """
        if not retrieved_docs:
            return "INCORRECT", []

        # Check maximum rerank or RRF score
        top_score = max(d.get("rerank_score", 0.0) for d in retrieved_docs)
        
        # Keyword alignment check
        query_terms = set(re.findall(r"\b\w{3,}\b", query.lower()))
        any_term_matched = False
        for doc in retrieved_docs[:3]:
            doc_text = doc.get("text", "").lower()
            if any(t in doc_text for t in query_terms):
                any_term_matched = True
                break

        if top_score >= self.confidence_threshold and any_term_matched:
            return "CORRECT", retrieved_docs
        elif top_score >= 0.05 or any_term_matched:
            return "AMBIGUOUS", retrieved_docs
        else:
            return "INCORRECT", retrieved_docs

    def transform_query(self, query: str) -> str:
        """
        Query Transformation (Expansion & Decomposition):
        Expands Hinglish slang and common bakery terminology into standard catalog search keywords.
        """
        q = query.lower()
        replacements = [
            (r"\bkillo\b|\bkilo\b|\bkg\b", "kg weight"),
            (r"\bbina ande\b|\beggless\b|\bveg\b", "Pure Veg Khoaa Eggless"),
            (r"\bande wala\b|\begg\b", "Egg variant"),
            (r"\bchhota\b|\bsmall\b|\b0\.5\b|\baadha\b", "0.5kg"),
            (r"\bbada\b|\blarge\b|\b1\b|\bek kg\b", "1kg"),
            (r"\bbirthday\b|\bjanamdin\b", "celebration birthday party"),
            (r"\banniversary\b|\bsaal girah\b", "anniversary heart red velvet"),
            (r"\bgaram\b|\bpetis\b|\bpatty\b|\bpatties\b", "masala patty puff oven item"),
            (r"\bcandle\b|\bmombatti\b|\bsparkler\b", "candles sparklers party accessories"),
            (r"\bdoll\b|\bbarbie\b|\bprincess\b", "Barbie Doll 3D gown custom designer"),
            (r"\bcustom\b|\bdesign\b|\bphoto\b", "1-on-1 Personal Baker Call Customization Service")
        ]
        expanded = q
        for pattern, replacement in replacements:
            if re.search(pattern, q):
                expanded += " " + replacement
        return expanded.strip()
