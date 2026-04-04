from fastapi import APIRouter, Depends, Query
from src.middleware.auth import require_min_role
from src.db.database import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
def summary(current_user: dict = Depends(require_min_role("analyst"))):
    conn = get_db()
    income = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM financial_records WHERE type='income' AND deleted_at IS NULL"
    ).fetchone()["total"]
    expenses = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM financial_records WHERE type='expense' AND deleted_at IS NULL"
    ).fetchone()["total"]
    conn.close()
    return {"total_income": income, "total_expenses": expenses, "net_balance": income - expenses}

@router.get("/categories")
def category_totals(current_user: dict = Depends(require_min_role("analyst"))):
    conn = get_db()
    rows = conn.execute(
        """SELECT category, type, COALESCE(SUM(amount), 0) as total, COUNT(*) as count
           FROM financial_records WHERE deleted_at IS NULL
           GROUP BY category, type ORDER BY total DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.get("/recent")
def recent_activity(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(require_min_role("analyst"))
):
    conn = get_db()
    rows = conn.execute(
        """SELECT id, amount, type, category, date, notes, created_at
           FROM financial_records WHERE deleted_at IS NULL
           ORDER BY created_at DESC LIMIT ?""", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.get("/trends/monthly")
def monthly_trends(current_user: dict = Depends(require_min_role("analyst"))):
    conn = get_db()
    rows = conn.execute(
        """SELECT strftime('%Y-%m', date) as month, type,
                  COALESCE(SUM(amount), 0) as total, COUNT(*) as count
           FROM financial_records WHERE deleted_at IS NULL
           GROUP BY month, type ORDER BY month DESC LIMIT 24"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.get("/trends/weekly")
def weekly_trends(current_user: dict = Depends(require_min_role("analyst"))):
    conn = get_db()
    rows = conn.execute(
        """SELECT strftime('%Y-W%W', date) as week, type,
                  COALESCE(SUM(amount), 0) as total, COUNT(*) as count
           FROM financial_records WHERE deleted_at IS NULL
           GROUP BY week, type ORDER BY week DESC LIMIT 12"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
