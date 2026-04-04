from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from src.middleware.auth import require_role
from src.db.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])

class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None

@router.get("/")
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role("admin"))
):
    offset = (page - 1) * limit
    conn = get_db()
    users = conn.execute(
        "SELECT id, name, email, role, status, created_at FROM users LIMIT ? OFFSET ?",
        (limit, offset)
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) as total FROM users").fetchone()["total"]
    conn.close()
    return {"users": [dict(u) for u in users], "total": total, "page": page, "limit": limit}

@router.get("/{user_id}")
def get_user(user_id: int, current_user: dict = Depends(require_role("admin"))):
    conn = get_db()
    user = conn.execute(
        "SELECT id, name, email, role, status, created_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(user)

@router.patch("/{user_id}")
def update_user(user_id: int, body: UpdateUserRequest, current_user: dict = Depends(require_role("admin"))):
    if body.role and body.role not in ("viewer", "analyst", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    if body.status and body.status not in ("active", "inactive"):
        raise HTTPException(status_code=400, detail="Invalid status")

    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    fields, values = [], []
    if body.name: fields.append("name = ?"); values.append(body.name)
    if body.role: fields.append("role = ?"); values.append(body.role)
    if body.status: fields.append("status = ?"); values.append(body.status)

    if not fields:
        conn.close()
        raise HTTPException(status_code=400, detail="No valid fields to update")

    fields.append("updated_at = datetime('now')")
    values.append(user_id)
    conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    updated = conn.execute(
        "SELECT id, name, email, role, status, created_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return dict(updated)
