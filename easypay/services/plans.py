from __future__ import annotations
from datetime import datetime
from typing import Optional
from ..core.db import connect, fetch_all, fetch_one, exec_one, exec_many
from ..core.dates import add_months


# ==========================================================
# COMPUTE PLAN AMOUNTS
# ==========================================================
def compute_amounts(
    total_price: float,
    advance: float,
    profit_pct: float,
    discount: float,
    months: int
) -> dict:

    base = max(total_price - advance, 0.0)
    profit = (base * profit_pct) / 100.0

    final_amount = round(base + profit, 2)
    final_payable = round(max(final_amount - discount, 0.0), 2)

    if months <= 0:
        raise ValueError("Months must be >= 1")

    per_month = round(final_payable / months, 2)
    schedule = [per_month] * months

    # Adjust last installment for rounding difference
    total_sched = round(sum(schedule), 2)
    diff = round(final_payable - total_sched, 2)
    schedule[-1] = round(schedule[-1] + diff, 2)

    return {
        "base": round(base, 2),
        "profit": round(profit, 2),
        "final_amount": final_amount,
        "final_payable": final_payable,
        "monthly_amounts": schedule,
    }


# ==========================================================
# CREATE PLAN
# ==========================================================
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

    amounts = compute_amounts(
        total_price,
        advance_payment,
        profit_pct,
        discount,
        months
    )

    conn = connect()

    # Insert Plan
    exec_one(conn, """
        INSERT INTO plans(
            customer_id,
            investor_id,
            item_name,
            total_price,
            advance_payment,
            profit_pct,
            months,
            start_date,
            discount,
            final_amount,
            final_payable,
            status,
            created_at
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        customer_id,
        investor_id,
        item_name,
        float(total_price),
        float(advance_payment),
        float(profit_pct),
        int(months),
        start_date,
        float(discount),
        amounts["final_amount"],
        amounts["final_payable"],
        "active",
        datetime.now().isoformat(timespec="seconds")
    ))

    plan_id = fetch_one(conn, "SELECT last_insert_rowid() AS id")["id"]

    # Create Installments
    rows = []
    for i in range(1, months + 1):
        due_date = add_months(start_date, i - 1)
        amount_due = amounts["monthly_amounts"][i - 1]

        rows.append((
            plan_id,
            i,
            due_date,
            amount_due,
            0.0,
            0,
            ""
        ))

    exec_many(conn, """
        INSERT INTO installments(
            plan_id,
            inst_no,
            due_date,
            amount_due,
            amount_paid,
            is_paid,
            remarks
        )
        VALUES(?,?,?,?,?,?,?)
    """, rows)

    conn.close()
    return int(plan_id)


# ==========================================================
# LIST PLANS
# ==========================================================
def list_plans(q: str = ""):
    conn = connect()

    if q.strip():
        rows = fetch_all(conn, """
            SELECT p.*,
                   c.full_name AS customer_name,
                   i.full_name AS investor_name
            FROM plans p
            JOIN customers c ON c.id = p.customer_id
            LEFT JOIN investors i ON i.id = p.investor_id
            WHERE c.full_name LIKE ?
               OR p.item_name LIKE ?
               OR i.full_name LIKE ?
            ORDER BY p.id DESC
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        rows = fetch_all(conn, """
            SELECT p.*,
                   c.full_name AS customer_name,
                   i.full_name AS investor_name
            FROM plans p
            JOIN customers c ON c.id = p.customer_id
            LEFT JOIN investors i ON i.id = p.investor_id
            ORDER BY p.id DESC
        """)

    conn.close()
    return rows


# ==========================================================
# INSTALLMENTS FOR PLAN
# ==========================================================
def installments_for_plan(plan_id: int):
    conn = connect()
    rows = fetch_all(
        conn,
        "SELECT * FROM installments WHERE plan_id=? ORDER BY inst_no",
        (plan_id,)
    )
    conn.close()
    return rows


# ==========================================================
# OVERDUE / UPCOMING
# ==========================================================
def overdue_and_upcoming(from_date: str, to_date: str):
    conn = connect()

    rows = fetch_all(conn, """
        SELECT ins.*,
               p.item_name,
               c.full_name AS customer_name
        FROM installments ins
        JOIN plans p ON p.id = ins.plan_id
        JOIN customers c ON c.id = p.customer_id
        WHERE ins.due_date BETWEEN ? AND ?
        ORDER BY ins.due_date ASC
    """, (from_date, to_date))

    conn.close()
    return rows


# ==========================================================
# DELETE PLAN (PROPER VERSION)
# ==========================================================
def delete_plan(plan_id: int) -> None:
    """
    Proper delete.

    Since your schema already uses:
    FOREIGN KEY(plan_id) REFERENCES plans(id) ON DELETE CASCADE

    Deleting the plan automatically deletes:
        installments
        payments (via installments)
        receipts (via payments)

    So we ONLY delete from plans.
    """

    with connect() as conn:
        conn.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
        conn.commit()