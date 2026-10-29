from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    role: Optional[str] = "CUSTOMER"

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class ChocoChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default_session"

class ChocoChatResponse(BaseModel):
    reply: str
    ui_cards: List[dict]
    retrieved_count: int

class OrderItemSchema(BaseModel):
    sku_id: str
    item_name: str
    quantity: int = 1
    unit_price: float
    cake_base: Optional[str] = "Pure Veg Eggless"
    cake_weight: Optional[str] = "0.5kg"
    custom_message: Optional[str] = None

class CreateOrderRequest(BaseModel):
    customer_name: str
    customer_phone: str
    delivery_address: Optional[str] = "Mathura Local Delivery"
    order_type: Optional[str] = "DELIVERY"
    special_notes: Optional[str] = None
    items: List[OrderItemSchema]
