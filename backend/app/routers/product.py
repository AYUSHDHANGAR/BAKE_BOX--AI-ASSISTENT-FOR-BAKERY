"""
Product router for BAKEBOX backend.
Provides simple read‑only endpoints for product lookup.
We rely on the ingestion script to populate the DB.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from app import db

router = APIRouter()

@router.get("/", response_model=List[dict])
async def list_products(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    """Return a paginated list of products (basic fields)."""
    with db.get_db() as conn:
        rows = db.query_all(
            conn,
            "SELECT sku_id, name, category, price_inr, image_url FROM products ORDER BY sku_id LIMIT ? OFFSET ?",
            (limit, offset),
        )
    return rows

@router.get("/{sku_id}", response_model=dict)
async def get_product(sku_id: str):
    """Fetch a single product by its SKU."""
    with db.get_db() as conn:
        prod = db.query_one(conn, "SELECT * FROM products WHERE sku_id = ?", (sku_id,))
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return prod
