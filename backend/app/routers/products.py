from fastapi import APIRouter, Query
from typing import Optional
from app.db import get_db, query_all, query_one

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("/cakes")
def list_cakes(
    category: Optional[str] = None,
    flavor: Optional[str] = None,
    weight: Optional[float] = None,
    search: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0
):
    sql = "SELECT sku_id, design_code, name, category, flavor, sub_category, available_base_variants, weight_kg, price, servings, has_chocochip, visual_features, image_path, prep_time, is_active FROM BB_CAKES WHERE is_active = 1"
    params = []

    if category:
        sql += " AND UPPER(category) = UPPER(?)"
        params.append(category)
    if flavor:
        sql += " AND UPPER(flavor) LIKE UPPER(?)"
        params.append(f"%{flavor}%")
    if weight:
        sql += " AND weight_kg = ?"
        params.append(weight)
    if search:
        sql += " AND (UPPER(name) LIKE UPPER(?) OR UPPER(flavor) LIKE UPPER(?))"
        params.extend([f"%{search}%", f"%{search}%"])

    sql += f" ORDER BY price ASC LIMIT {limit} OFFSET {offset}"

    with get_db() as conn:
        cnt_row = query_one(conn, "SELECT COUNT(*) as cnt FROM BB_CAKES WHERE is_active = 1")
        total_cnt = cnt_row["CNT"] if cnt_row and "CNT" in cnt_row else 0
        rows = query_all(conn, sql, tuple(params) if params else None)
        return {"total": total_cnt, "count": len(rows), "items": rows}

@router.get("/custom-cakes")
def list_custom_cakes(
    search: Optional[str] = None,
    flavor: Optional[str] = None,
    limit: int = 200,
    offset: int = 0
):
    sql = "SELECT id, sku_id, design_code, name, category, flavor, sub_category, available_base_variants, service_type, weight_kg, servings, image_path, price_inr, ordering_channel, customization_options, price_status FROM BB_CUSTOM_CAKES WHERE is_active = 1"
    params = []

    if flavor:
        sql += " AND UPPER(flavor) LIKE UPPER(?)"
        params.append(f"%{flavor}%")
    if search:
        sql += " AND (UPPER(name) LIKE UPPER(?) OR UPPER(flavor) LIKE UPPER(?))"
        params.extend([f"%{search}%", f"%{search}%"])

    sql += f" ORDER BY id ASC LIMIT {limit} OFFSET {offset}"

    with get_db() as conn:
        cnt_row = query_one(conn, "SELECT COUNT(*) as cnt FROM BB_CUSTOM_CAKES WHERE is_active = 1")
        total_cnt = cnt_row["CNT"] if cnt_row and "CNT" in cnt_row else 0
        rows = query_all(conn, sql, tuple(params) if params else None)
        return {"total": total_cnt, "count": len(rows), "items": rows}

@router.get("/accessories")
def list_accessories():
    sql = "SELECT sku_id, item_name, category, sub_category, pack_size_or_servings, price_inr, is_vegetarian, image_path, visual_features, description FROM BB_PARTY_ACCESSORIES WHERE is_active = 1 ORDER BY price_inr ASC"
    with get_db() as conn:
        rows = query_all(conn, sql)
        return {"total": len(rows), "items": rows}

@router.get("/bakery-raw")
def list_bakery_raw():
    sql = "SELECT sku_id, item_name, category_section, shape, has_onion, has_paneer, is_eggless, shelf_life_hours, thermal_type, price_inr, description FROM BB_BAKERY_RAW WHERE is_active = 1 ORDER BY price_inr ASC"
    with get_db() as conn:
        rows = query_all(conn, sql)
        return {"total": len(rows), "items": rows}

@router.get("/{sku_id}")
def get_product_by_sku(sku_id: str):
    with get_db() as conn:
        # Check standard cakes
        cake = query_one(conn, "SELECT * FROM BB_CAKES WHERE sku_id = ?", (sku_id,))
        if cake:
            return {"type": "CAKE", "product": cake}
        
        # Check custom cakes
        custom = query_one(conn, "SELECT * FROM BB_CUSTOM_CAKES WHERE sku_id = ?", (sku_id,))
        if custom:
            return {"type": "CUSTOM_CAKE", "product": custom}

        # Check accessories
        acc = query_one(conn, "SELECT * FROM BB_PARTY_ACCESSORIES WHERE sku_id = ?", (sku_id,))
        if acc:
            return {"type": "PARTY_ACCESSORIES", "product": acc}

        # Check bakery raw
        raw = query_one(conn, "SELECT * FROM BB_BAKERY_RAW WHERE sku_id = ?", (sku_id,))
        if raw:
            return {"type": "BAKERY_RAW", "product": raw}

        return {"error": "Product not found", "sku_id": sku_id}
