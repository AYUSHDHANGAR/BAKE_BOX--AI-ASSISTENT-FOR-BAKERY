from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import ibm_db
from app.auth import require_admin
from app.db import get_db, query_all, query_one, execute_dml

router = APIRouter(prefix="/api/admin", tags=["Admin & Operators"])

class UpdateStatusRequest(BaseModel):
    status: str

@router.get("/metrics")
def get_dashboard_metrics(current_user: dict = Depends(require_admin)):
    with get_db() as conn:
        cakes_c = query_one(conn, "SELECT COUNT(*) as c FROM BB_CAKES")["C"]
        custom_c = query_one(conn, "SELECT COUNT(*) as c FROM BB_CUSTOM_CAKES")["C"]
        party_c = query_one(conn, "SELECT COUNT(*) as c FROM BB_PARTY_ACCESSORIES")["C"]
        raw_c = query_one(conn, "SELECT COUNT(*) as c FROM BB_BAKERY_RAW")["C"]
        users_c = query_one(conn, "SELECT COUNT(*) as c FROM BB_USERS")["C"]
        orders_c = query_one(conn, "SELECT COUNT(*) as c, COALESCE(SUM(total_amount), 0) as rev FROM BB_ORDERS")
        rag_c = query_one(conn, "SELECT COUNT(*) as c FROM BB_RAG_CHUNKS")["C"]
        ops = query_all(conn, "SELECT * FROM BB_ADMIN_OPERATORS")

        return {
            "total_cakes": cakes_c,
            "total_custom_cakes": custom_c,
            "total_party_items": party_c,
            "total_raw_snacks": raw_c,
            "total_users": users_c,
            "total_orders": orders_c["C"],
            "total_revenue": float(orders_c["REV"]),
            "total_rag_chunks_ibmdb2": rag_c,
            "operators_count": len(ops),
            "operators": ops
        }

@router.get("/orders")
def get_all_orders(current_user: dict = Depends(require_admin)):
    with get_db() as conn:
        orders = query_all(conn, "SELECT * FROM BB_ORDERS ORDER BY order_id DESC")
        result = []
        for o in orders:
            items = query_all(conn, "SELECT * FROM BB_ORDER_ITEMS WHERE order_id = ?", (o["ORDER_ID"],))
            result.append({
                "order_id": o["ORDER_ID"],
                "user_id": o["USER_ID"],
                "customer_name": o["CUSTOMER_NAME"],
                "customer_phone": o["CUSTOMER_PHONE"],
                "delivery_address": o["DELIVERY_ADDRESS"],
                "order_type": o["ORDER_TYPE"],
                "order_status": o["ORDER_STATUS"],
                "total_amount": float(o["TOTAL_AMOUNT"]),
                "special_notes": o["SPECIAL_NOTES"],
                "created_at": str(o["CREATED_AT"]),
                "items": items
            })
        return {"orders": result}

@router.patch("/orders/{order_id}/status")
def update_order_status(order_id: int, req: UpdateStatusRequest, current_user: dict = Depends(require_admin)):
    valid_statuses = ["PENDING", "CONFIRMED", "BAKING", "READY", "DELIVERED", "CANCELLED"]
    st = req.status.upper()
    if st not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    with get_db() as conn:
        execute_dml(conn, "UPDATE BB_ORDERS SET order_status = ? WHERE order_id = ?", (st, order_id))
        return {"order_id": order_id, "updated_status": st, "message": "Order status updated successfully."}

@router.patch("/inventory/{sku_id}/toggle")
def toggle_inventory_item(sku_id: str, current_user: dict = Depends(require_admin)):
    with get_db() as conn:
        # Check standard cakes
        item = query_one(conn, "SELECT is_active FROM BB_CAKES WHERE sku_id = ?", (sku_id,))
        if item:
            new_val = 0 if item["IS_ACTIVE"] == 1 else 1
            execute_dml(conn, "UPDATE BB_CAKES SET is_active = ? WHERE sku_id = ?", (new_val, sku_id))
            return {"sku_id": sku_id, "is_active": new_val}
        
        # Check custom cakes
        item2 = query_one(conn, "SELECT is_active FROM BB_CUSTOM_CAKES WHERE sku_id = ?", (sku_id,))
        if item2:
            new_val = 0 if item2["IS_ACTIVE"] == 1 else 1
            execute_dml(conn, "UPDATE BB_CUSTOM_CAKES SET is_active = ? WHERE sku_id = ?", (new_val, sku_id))
            return {"sku_id": sku_id, "is_active": new_val}

        raise HTTPException(status_code=404, detail="Product SKU not found in inventory.")
