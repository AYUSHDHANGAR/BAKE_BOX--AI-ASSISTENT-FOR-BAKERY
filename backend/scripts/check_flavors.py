import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
from app.db import get_db, query_all

with get_db() as conn:
    rows = query_all(conn, "SELECT DISTINCT source_type, COUNT(*) as cnt FROM BB_RAG_CHUNKS GROUP BY source_type")
    for r in rows:
        print(r)
