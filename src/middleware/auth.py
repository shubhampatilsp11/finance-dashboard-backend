from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from src.db.database import get_db
import os

SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey123")
ALGORITHM = "HS256"

bearer_scheme = HTTPBearer()

ROLE_LEVELS = {"viewer": 1, "analyst": 2, "admin": 3}

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    conn = get_db()
    user = conn.execute(
        "SELECT id, name, email, role, status FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()

    if not user or user["status"] == "inactive":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return dict(user)

def require_role(*roles):
    def checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to perform this action")
        return current_user
    return checker

def require_min_role(min_role: str):
    def checker(current_user: dict = Depends(get_current_user)):
        if ROLE_LEVELS.get(current_user["role"], 0) < ROLE_LEVELS.get(min_role, 0):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to perform this action")
        return current_user
    return checker
