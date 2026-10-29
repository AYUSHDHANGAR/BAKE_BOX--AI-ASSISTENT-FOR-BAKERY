from fastapi import APIRouter, Depends, HTTPException
import ibm_db
from app.auth import get_current_user
from app.db import get_db, query_all, query_one
from app.models import CreateOrderRequest

router = APIRouter(prefix="/api/orders", tags=["Orders"])

@router.post("/")
def create_order(
    req: CreateOrderRequest,
    current_user: dict = Depends(get_current_user)
):
    if not req.items:
        raise HTTPException(status_code=400, detail="Order items cannot be empty.")
    
    user_id = current_user["ID"]
    total_amount = sum(item.unit_price * item.quantity for item in req.items)

    with get_db() as conn:
        order_sql = """
            INSERT INTO BB_ORDERS 
            (user_id, customer_name, customer_phone, delivery_address, order_type, order_status, total_amount, special_notes)
            VALUES (?, ?, ?, ?, ?, 'CONFIRMED', ?, ?)
        """
        cursor = conn.cursor()
        cursor.execute(order_sql, (
            user_id,
            req.customer_name,
            req.customer_phone,
            req.delivery_address,
            req.order_type,
            total_amount,
            req.special_notes or "Order via BAKEBOX"
        ))
        conn.commit()

        # Fetch created order ID
        created = query_one(conn, "SELECT MAX(order_id) as last_id FROM BB_ORDERS WHERE user_id = ?", (user_id,))
        order_id = created["LAST_ID"]

        # Insert items
        item_sql = """
            INSERT INTO BB_ORDER_ITEMS 
            (order_id, sku_id, item_name, quantity, unit_price, cake_base, cake_weight, custom_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        for item in req.items:
            cursor.execute(item_sql, (
                order_id,
                item.sku_id,
                item.item_name,
                item.quantity,
                item.unit_price,
                item.cake_base,
                item.cake_weight,
                item.custom_message or ""
            ))
        conn.commit()

        return {
            "order_id": order_id,
            "status": "CONFIRMED",
            "total_amount": total_amount,
            "baking_time": "3-4 hours fresh baking wait time",
            "message": "Ji shukriya! Aapka order Shri Ram Baker BAKEBOX mein successfully confirm ho gaya hai."
        }

@router.get("/my-orders")
def get_my_orders(current_user: dict = Depends(get_current_user)):
    user_id = current_user["ID"]
    with get_db() as conn:
        orders = query_all(conn, "SELECT * FROM BB_ORDERS WHERE user_id = ? ORDER BY order_id DESC", (user_id,))
        result = []
        for o in orders:
            items = query_all(conn, "SELECT * FROM BB_ORDER_ITEMS WHERE order_id = ?", (o["ORDER_ID"],))
            result.append({
                "order_id": o["ORDER_ID"],
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
