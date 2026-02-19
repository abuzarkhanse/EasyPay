from __future__ import annotations
from datetime import datetime, date
from typing import Optional, Tuple
from ..core.db import connect, fetch_all, fetch_one, exec_one, exec_many
from ..core.dates import add_months, today_iso

def compute_amounts(total_price: float, advance: float, profit_pct: float, discount: float, months: int) -> dict:
    # Business logic:
    # base = total - advance
    # final_amount = base + profit
    # final_payable = final_amount - discount
    base = max(total_price - advance, 0.0)
    profit = (base * profit_pct) / 100.0
    final_amount = round(base + profit, 2)
    final_payable = round(max(final_amount - discount, 0.0), 2)

    if months <= 0:
        raise ValueError("Months must be >= 1")

    # Split into months; last installment adjusted to keep exact total
    per = round(final_payable / months, 2)
    schedule = [per] * months
    total_sched = round(sum(schedule), 2)
    diff = round(final_payable - total_sched, 2)
    schedule[-1] = round(schedule[-1] + diff, 2)

    return {
        "base": base,
        "profit": round(profit, 2),
        "final_amount": final_amount,
        "final_payable": final_payable,
        "monthly_amounts": schedule,
    }

def create_plan(
    customer_id: int,
    item_name: str,
    total_price: float,
    advance_payment: float,
    profit_pct: float,
    months: int,
    start_date: str,
    discount: float = 0.0,
    investor_id: Optional[int] = None,
) -> int:
    amounts = compute_amounts(total_price, advance_payment, profit_pct, discount, months)
    conn = connect()
    exec_one(conn, """
        INSERT INTO plans(customer_id, investor_id, item_name, total_price, advance_payment, profit_pct, months, start_date,
                          discount, final_amount, final_payable, status, created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        customer_id, investor_id, item_name, float(total_price), float(advance_payment), float(profit_pct), int(months), start_date,
        float(discount), amounts["final_amount"], amounts["final_payable"], "active", datetime.now().isoformat(timespec="seconds")
    ))
    plan_id = fetch_one(conn, "SELECT last_insert_rowid() AS id")["id"]

    rows = []
    for i in range(1, months + 1):
        due = add_months(start_date, i-1)
        amt = amounts["monthly_amounts"][i-1]
        rows.append((plan_id, i, due, amt, 0.0, 0, ""))

    exec_many(conn, """
        INSERT INTO installments(plan_id, inst_no, due_date, amount_due, amount_paid, is_paid, remarks)
        VALUES(?,?,?,?,?,?,?)
    """, rows)
    conn.close()
    return int(plan_id)

def list_plans(q: str = ""):
    conn = connect()
    if q.strip():
        rows = fetch_all(conn, """
            SELECT p.*, c.full_name AS customer_name, i.full_name AS investor_name
            FROM plans p
            JOIN customers c ON c.id = p.customer_id
            LEFT JOIN investors i ON i.id = p.investor_id
            WHERE c.full_name LIKE ? OR p.item_name LIKE ? OR i.full_name LIKE ?
            ORDER BY p.id DESC
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        rows = fetch_all(conn, """
            SELECT p.*, c.full_name AS customer_name, i.full_name AS investor_name
            FROM plans p
            JOIN customers c ON c.id = p.customer_id
            LEFT JOIN investors i ON i.id = p.investor_id
            ORDER BY p.id DESC
        """)
    conn.close()
    return rows

def installments_for_plan(plan_id: int):
    conn = connect()
    rows = fetch_all(conn, "SELECT * FROM installments WHERE plan_id=? ORDER BY inst_no", (plan_id,))
    conn.close()
    return rows

def overdue_and_upcoming(from_date: str, to_date: str):
    conn = connect()
    rows = fetch_all(conn, """
        SELECT ins.*, p.item_name, c.full_name AS customer_name
        FROM installments ins
        JOIN plans p ON p.id = ins.plan_id
        JOIN customers c ON c.id = p.customer_id
        WHERE ins.due_date BETWEEN ? AND ?
        ORDER BY ins.due_date ASC
    """, (from_date, to_date))
    conn.close()
    return rows
