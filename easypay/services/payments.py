from __future__ import annotations

from datetime import datetime
from typing import Optional

from easypay.core.db import connect, fetch_one, fetch_all, exec_one


# ==========================================================
# ADD PAYMENT
# ==========================================================
def add_payment(
    installment_id: int,
    amount: float,
    actual_payment_date: str,
    remarks: str = ""
) -> int:

    if amount <= 0:
        raise ValueError("Amount must be > 0")

    conn = connect()

    ins = fetch_one(conn, "SELECT * FROM installments WHERE id=?", (installment_id,))
    if ins is None:
        conn.close()
        raise ValueError("Installment not found")

    new_paid = round(float(ins["amount_paid"]) + float(amount), 2)
    due = float(ins["amount_due"])
    is_paid = 1 if new_paid >= due - 0.0001 else 0  # float tolerance

    exec_one(conn, """
        INSERT INTO payments(
            installment_id,
            actual_payment_date,
            amount,
            remarks,
            created_at
        )
        VALUES(?,?,?,?,?)
    """, (
        installment_id,
        actual_payment_date,
        float(amount),
        remarks,
        datetime.now().isoformat(timespec="seconds")
    ))

    payment_id = fetch_one(conn, "SELECT last_insert_rowid() AS id")["id"]

    exec_one(
        conn,
        "UPDATE installments SET amount_paid=?, is_paid=? WHERE id=?",
        (new_paid, is_paid, installment_id)
    )

    conn.close()
    return int(payment_id)


# ==========================================================
# EDIT PAYMENT
# ==========================================================
def edit_payment(
    payment_id: int,
    new_amount: float,
    actual_payment_date: str,
    remarks: str = ""
) -> None:

    if new_amount <= 0:
        raise ValueError("Amount must be > 0")

    conn = connect()

    pay = fetch_one(conn, "SELECT * FROM payments WHERE id=?", (payment_id,))
    if pay is None:
        conn.close()
        raise ValueError("Payment not found")

    ins = fetch_one(conn, "SELECT * FROM installments WHERE id=?", (pay["installment_id"],))
    if ins is None:
        conn.close()
        raise ValueError("Installment missing")

    # Update payment
    exec_one(
        conn,
        "UPDATE payments SET amount=?, actual_payment_date=?, remarks=? WHERE id=?",
        (float(new_amount), actual_payment_date, remarks, payment_id)
    )

    # Recalculate installment totals
    total = fetch_one(
        conn,
        "SELECT COALESCE(SUM(amount),0) AS s FROM payments WHERE installment_id=?",
        (pay["installment_id"],)
    )["s"]

    total = round(float(total), 2)
    due = float(ins["amount_due"])
    is_paid = 1 if total >= due - 0.0001 else 0

    exec_one(
        conn,
        "UPDATE installments SET amount_paid=?, is_paid=? WHERE id=?",
        (total, is_paid, ins["id"])
    )

    conn.close()


# ==========================================================
# RECEIPT CONTEXT
# ==========================================================
def list_receipt_context(payment_id: int):
    conn = connect()

    row = fetch_one(conn, """
        SELECT pay.*, 
               ins.inst_no,
               ins.due_date,
               ins.amount_due,
               ins.amount_paid,
               ins.is_paid,
               p.item_name,
               p.discount,
               p.final_payable,
               p.advance_payment,
               c.full_name AS customer_name
        FROM payments pay
        JOIN installments ins ON ins.id = pay.installment_id
        JOIN plans p ON p.id = ins.plan_id
        JOIN customers c ON c.id = p.customer_id
        WHERE pay.id=?
    """, (payment_id,))

    conn.close()
    return row


# ==========================================================
# REMAINING BALANCE
# ==========================================================
def remaining_balance_for_plan(plan_id: int) -> float:
    conn = connect()

    p = fetch_one(conn, "SELECT final_payable FROM plans WHERE id=?", (plan_id,))
    if p is None:
        conn.close()
        return 0.0

    paid = fetch_one(conn, """
        SELECT COALESCE(SUM(amount_paid),0) AS s
        FROM installments WHERE plan_id=?
    """, (plan_id,))["s"]

    conn.close()

    return round(float(p["final_payable"]) - float(paid), 2)