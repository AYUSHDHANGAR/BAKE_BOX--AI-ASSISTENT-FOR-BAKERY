from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.db import get_db, query_one, execute_dml
from app.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    role: Optional[str] = "CUSTOMER"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    with get_db() as conn:
        existing = query_one(conn, "SELECT id FROM BB_USERS WHERE email = ?", (req.email,))
        if existing:
            raise HTTPException(status_code=400, detail="An account with this email already exists.")
        
        pwd_hash = hash_password(req.password)
        sql = "INSERT INTO BB_USERS (email, password_hash, full_name, phone, role) VALUES (?, ?, ?, ?, ?)"
        execute_dml(conn, sql, (req.email, pwd_hash, req.full_name, req.phone or "", req.role.upper()))
        
        user = query_one(conn, "SELECT id, email, full_name, phone, role FROM BB_USERS WHERE email = ?", (req.email,))
        token = create_access_token({"sub": str(user["ID"]), "email": user["EMAIL"], "role": user["ROLE"]})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["ID"],
                "email": user["EMAIL"],
                "full_name": user["FULL_NAME"],
                "phone": user["PHONE"],
                "role": user["ROLE"]
            }
        }

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    with get_db() as conn:
        user = query_one(conn, "SELECT id, email, password_hash, full_name, phone, role FROM BB_USERS WHERE email = ?", (req.email,))
        if not user or not verify_password(req.password, user["PASSWORD_HASH"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
        
        token = create_access_token({"sub": str(user["ID"]), "email": user["EMAIL"], "role": user["ROLE"]})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["ID"],
                "email": user["EMAIL"],
                "full_name": user["FULL_NAME"],
                "phone": user["PHONE"],
                "role": user["ROLE"]
            }
        }

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["ID"],
        "email": current_user["EMAIL"],
        "full_name": current_user["FULL_NAME"],
        "phone": current_user["PHONE"],
        "role": current_user["ROLE"]
    }
