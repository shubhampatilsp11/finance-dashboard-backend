from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, field_validator
from typing import Optional
from src.middleware.auth import require_role, require_min_role
from src.db.database import get_db
import re

router = APIRouter(prefix="/records", tags=["Records"])

class RecordCreate(BaseModel):
    amount: float
    type: str
    category: str
    date: str
    notes: Optional[str] = None

    @field_validator("amount")
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @field_validator("type")
    def valid_type(cls, v):
        if v not in ("income", "expense"):
            raise ValueError("Type must be income or expense")
        return v

    @field_validator("date")
    def valid_date(cls, v):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

class RecordUpdate(BaseModel):
    amount: Optional[float] = None
    type: Optional[str] = None
    category: Optional[str] = None
    date: Optional[str] = None
    notes: Optional[str] = None

@router.get("/")
def list_records(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(require_min_role("viewer"))
):
    offset = (page - 1) * limit
    conditions = ["deleted_at IS NULL"]
    params = []

    if type: conditions.append("type = ?"); params.append(type)
    if category: conditions.append("category = ?"); params.append(category)
    if date_from: conditions.append("date >= ?"); params.append(date_from)
    if date_to: conditions.append("date <= ?"); params.append(date_to)

    where = " AND ".join(conditions)
    conn = get_db()
    records = conn.execute(
        f"SELECT * FROM financial_records WHERE {where} ORDER BY date DESC LIMIT ? OFFSET ?",
        params + [limit, offset]
    ).fetchall()
    total = conn.execute(f"SELECT COUNT(*) as total FROM financial_records WHERE {where}", params).fetchone()["total"]
    conn.close()
    return {"records": [dict(r) for r in records], "total": total, "page": page, "limit": limit}

@router.get("/{record_id}")
def get_record(record_id: int, current_user: dict = Depends(require_min_role("viewer"))):
    conn = get_db()
    record = conn.execute(
        "SELECT * FROM financial_records WHERE id = ? AND deleted_at IS NULL", (record_id,)
    ).fetchone()
    conn.close()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return dict(record)

@router.post("/", status_code=201)
def create_record(body: RecordCreate, current_user: dict = Depends(require_role("admin"))):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO financial_records (user_id, amount, type, category, date, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (current_user["id"], body.amount, body.type, body.category, body.date, body.notes)
    )
    conn.commit()
    record = conn.execute("SELECT * FROM financial_records WHERE id = ?", (cursor.lastrowid,)).fetchone()
    conn.close()
    return dict(record)

@router.patch("/{record_id}")
def update_record(record_id: int, body: RecordUpdate, current_user: dict = Depends(require_role("admin"))):
    conn = get_db()
    record = conn.execute(
        "SELECT id FROM financial_records WHERE id = ? AND deleted_at IS NULL", (record_id,)
    ).fetchone()
    if not record:
        conn.close()
        raise HTTPException(status_code=404, detail="Record not found")

    fields, values = [], []
    if body.amount is not None: fields.append("amount = ?"); values.append(body.amount)
    if body.type: fields.append("type = ?"); values.append(body.type)
    if body.category: fields.append("category = ?"); values.append(body.category)
    if body.date: fields.append("date = ?"); values.append(body.date)
    if body.notes is not None: fields.append("notes = ?"); values.append(body.notes)

    if not fields:
        conn.close()
        raise HTTPException(status_code=400, detail="No valid fields to update")

    fields.append("updated_at = datetime('now')")
    values.append(record_id)
    conn.execute(f"UPDATE financial_records SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    updated = conn.execute("SELECT * FROM financial_records WHERE id = ?", (record_id,)).fetchone()
    conn.close()
    return dict(updated)

@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: int, current_user: dict = Depends(require_role("admin"))):
    conn = get_db()
    record = conn.execute(
        "SELECT id FROM financial_records WHERE id = ? AND deleted_at IS NULL", (record_id,)
    ).fetchone()
    if not record:
        conn.close()
        raise HTTPException(status_code=404, detail="Record not found")
    conn.execute("UPDATE financial_records SET deleted_at = datetime('now') WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
