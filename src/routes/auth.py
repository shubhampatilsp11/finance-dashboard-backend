from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from jose import jwt
from datetime import datetime, timedelta
from src.db.database import get_db
import bcrypt
import os

router = APIRouter(prefix="/auth", tags=["Auth"])

SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey123")
ALGORITHM = "HS256"
EXPIRES_DAYS = int(os.getenv("JWT_EXPIRES_IN", 7))

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "viewer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register", status_code=201)
def register(body: RegisterRequest):
    if body.role not in ("viewer", "analyst", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (body.email,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=409, detail="Email already in use")

    hashed = hash_password(body.password)
    cursor = conn.execute(
        "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
        (body.name, body.email, hashed, body.role)
    )
    conn.commit()
    user = conn.execute(
        "SELECT id, name, email, role, status, created_at FROM users WHERE id = ?",
        (cursor.lastrowid,)
    ).fetchone()
    conn.close()
    return {"message": "User registered successfully", "user": dict(user)}

@router.post("/login")
def login(body: LoginRequest):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (body.email,)).fetchone()
    conn.close()

    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user["status"] == "inactive":
        raise HTTPException(status_code=403, detail="Account is inactive")

    token = jwt.encode(
        {"id": user["id"], "role": user["role"], "exp": datetime.utcnow() + timedelta(days=EXPIRES_DAYS)},
        SECRET_KEY, algorithm=ALGORITHM
    )
    return {"token": token, "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}}
