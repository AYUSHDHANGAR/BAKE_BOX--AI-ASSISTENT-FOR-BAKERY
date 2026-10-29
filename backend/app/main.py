"""
BAKEBOX FastAPI Backend Application.
Shri Ram Baker's digital e-commerce and autonomous AI management platform.
Exclusively connected to IBM Db2 (instance IBMDB201).
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db import get_db, query_one
from app.routers import auth, products, choco, orders, admin

app = FastAPI(
    title="BAKEBOX API - Shri Ram Baker",
    description="Digital e-commerce, isolated authentication, and CHOCO autonomous AI management engine powered by IBM Db2, LlamaIndex, Hybrid RAG, and Gemini.",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local BAKEBOX catalog images directory robustly
catalog_candidates = [
    os.path.abspath("BAKEBOX_CATALOG"),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "BAKEBOX_CATALOG")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "BAKEBOX_CATALOG")),
]
catalog_dir = next((c for c in catalog_candidates if os.path.exists(c)), None)
if catalog_dir:
    app.mount("/catalog_images", StaticFiles(directory=catalog_dir), name="catalog_images")
    print(f"Mounted catalog images from: {catalog_dir}")

# Register Routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(choco.router)
app.include_router(orders.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {
        "platform": "BAKEBOX - Shri Ram Baker",
        "tagline": "Mathura's Premier Digital Bakery & Autonomous AI Management System",
        "database": "IBM Db2 (IBMDB201)",
        "ai_assistant": "CHOCO (Powered by LlamaIndex + Gemini 3.5 Flash + Hybrid RAG + CRAG + Self-RAG)",
        "status": "Online & Operational"
    }

@app.get("/health")
def health_check():
    try:
        with get_db() as conn:
            db_row = query_one(conn, "SELECT CURRENT TIMESTAMP as cur_time FROM SYSIBM.SYSDUMMY1")
            return {
                "status": "HEALTHY",
                "ibm_db2": "CONNECTED (IBMDB201)",
                "timestamp": str(db_row.get("CUR_TIME", ""))
            }
    except Exception as e:
        return {
            "status": "DEGRADED",
            "ibm_db2_error": str(e)
        }
