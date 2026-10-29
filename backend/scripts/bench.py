import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag.embeddings import DenseEmbeddingEngine, SparseTFIDFEngine
from app.rag.reranker import CrossEncoderReranker
from google import genai

t0 = time.time()
dense = DenseEmbeddingEngine.get_instance()
print(f"Dense init: {time.time()-t0:.2f}s")

t0 = time.time()
q_emb = dense.embed_query("red velvet cake")
print(f"Dense query embed: {time.time()-t0:.2f}s")

t0 = time.time()
reranker = CrossEncoderReranker.get_instance()
print(f"Reranker init: {time.time()-t0:.2f}s")

t0 = time.time()
ranked = reranker.rerank("red velvet cake", [{"id":"1","text":"red velvet cake with cream cheese"}, {"id":"2","text":"pineapple cake"}])
print(f"Rerank query: {time.time()-t0:.2f}s")

t0 = time.time()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
res = client.models.generate_content(model="gemini-flash-latest", contents="Hello CHOCO")
print(f"Gemini call: {time.time()-t0:.2f}s")
