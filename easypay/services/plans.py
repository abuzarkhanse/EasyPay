from __future__ import annotations
from datetime import datetime
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP

from ..core.db import connect, fetch_all, fetch_one, exec_one, exec_many
from ..core.dates import add_months


# ==========================================================
# COMPUTE PLAN AMOUNTS
# ==========================================================

def _to_decimal(value) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except Exception:
        return Decimal("0")


def round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _split_installments(total: Decimal, months: int) -> list[float]:
    """
    Split total into equal monthly amounts while keeping final sum exact.
    Example:
        100 / 3 => [33.33, 33.33, 33.34]
    """
    if months <= 0:
        months = 1

    total = round_money(total)
    base = (total / Decimal(str(months))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    amounts = [base for _ in range(months)]
    current_sum = sum(amounts, Decimal("0.00"))
    diff = round_money(total - current_sum)

    if diff != Decimal("0.00"):
        amounts[-1] = round_money(amounts[-1] + diff)

    return [float(a) for a in amounts]


def calculate_plan_values(
    total_price,
    advance_payment,
    profit_percent,
    months,
    discount=0,
    profit_mode="principal",   # "total" or "principal"
):
    total_price = _to_decimal(total_price)
    advance_payment = _to_decimal(advance_payment)
    profit_percent = _to_decimal(profit_percent)
    discount = _to_decimal(discount)
    months = int(months or 1)

    if months <= 0:
        months = 1

    if total_price < 0:
        total_price = Decimal("0")
    if advance_payment < 0:
        advance_payment = Decimal("0")
    if discount < 0:
        discount = Decimal("0")

    # Principal always means total - advance
    principal = total_price - advance_payment
    if principal < 0:
        principal = Decimal("0")

    # Profit can apply on full total or on principal
    if profit_mode == "total":
        profit_base = total_price
    else:
        profit_mode = "principal"
        profit_base = principal

    profit = (profit_base * profit_percent) / Decimal("100")
    profit = round_money(profit)

    final_before_discount = round_money(principal + profit)
    final_payable = round_money(final_before_discount - discount)

    if final_payable < 0:
        final_payable = Decimal("0")

    monthly_amounts = _split_installments(final_payable, months)

    return {
        "principal": float(round_money(principal)),
        "profit_base": float(round_money(profit_base)),
        "profit": float(round_money(profit)),
        "final_amount": float(round_money(final_before_discount)),
        "final_before_discount": float(round_money(final_before_discount)),
        "final_payable": float(round_money(final_payable)),
        "monthly_payment": float(round_money(final_payable / Decimal(str(months)))),
        "monthly_amounts": monthly_amounts,
        "discount": float(round_money(discount)),
        "profit_mode": profit_mode,
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
    profit_mode: str = "principal",
) -> int:
    amounts = calculate_plan_values(
        total_price=total_price,
        advance_payment=advance_payment,
        profit_percent=profit_pct,
        months=months,
        discount=discount,
        profit_mode=profit_mode,
    )

    conn = connect()

    plan_number = "PLN-" + datetime.now().strftime("%Y%m%d%H%M%S")

    # legacy compatibility for older code that still reads discount_mode
    legacy_discount_mode = "final" if profit_mode == "total" else "principal"

    exec_one(conn, """
    INSERT INTO plans(
        plan_number,
        customer_id,
        investor_id,
        item_name,
        total_price,
        advance_payment,
        profit_pct,
        months,
        start_date,
        discount,
        discount_mode,
        profit_mode,
        final_amount,
        final_payable,
        status,
        created_at
    )
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        plan_number,
        customer_id,
        investor_id,
        item_name,
        float(total_price),
        float(advance_payment),
        float(profit_pct),
        int(months),
        start_date,
        float(discount),
        legacy_discount_mode,
        profit_mode,
        amounts["final_amount"],
        amounts["final_payable"],
        "active",
        datetime.now().isoformat(timespec="seconds")
    ))

    plan_id = fetch_one(conn, "SELECT last_insert_rowid() AS id")["id"]

    # Create installments
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
# DELETE PLAN
# ==========================================================

def delete_plan(plan_id: int) -> None:
    """
    Since foreign keys already use ON DELETE CASCADE,
    deleting the plan automatically removes related records.
    """
    with connect() as conn:
        conn.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
        conn.commit()
        