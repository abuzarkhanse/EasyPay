from __future__ import annotations

from datetime import datetime

from easypay.core.db import connect, fetch_one, exec_one


# ==========================================================
# HELPERS
# ==========================================================
def _get_installment(conn, installment_id: int):
    return fetch_one(conn, "SELECT * FROM installments WHERE id=?", (installment_id,))


def _get_payment(conn, payment_id: int):
    return fetch_one(conn, "SELECT * FROM payments WHERE id=?", (payment_id,))


def _recalculate_installment_status(conn, installment_id: int) -> None:
    ins = _get_installment(conn, installment_id)
    if ins is None:
        raise ValueError("Installment not found")

    total_paid = fetch_one(
        conn,
        "SELECT COALESCE(SUM(amount), 0) AS s FROM payments WHERE installment_id=?",
        (installment_id,)
    )["s"]

    total_paid = round(float(total_paid), 2)
    due = round(float(ins["amount_due"]), 2)
    is_paid = 1 if total_paid >= due - 0.0001 else 0

    exec_one(
        conn,
        "UPDATE installments SET amount_paid=?, is_paid=? WHERE id=?",
        (total_paid, is_paid, installment_id)
    )


def _remaining_for_installment(conn, installment_id: int) -> float:
    ins = _get_installment(conn, installment_id)
    if ins is None:
        raise ValueError("Installment not found")

    due = round(float(ins["amount_due"]), 2)
    paid = round(float(ins["amount_paid"]), 2)
    remaining = round(due - paid, 2)

    if remaining < 0:
        remaining = 0.0

    return remaining


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

    try:
        ins = _get_installment(conn, installment_id)
        if ins is None:
            raise ValueError("Installment not found")

        remaining = _remaining_for_installment(conn, installment_id)
        amount = round(float(amount), 2)

        if remaining <= 0:
            raise ValueError("This installment is already fully paid.")

        if amount > remaining + 0.0001:
            raise ValueError(
                f"Payment exceeds remaining installment balance.\n"
                f"Remaining balance: {remaining:.2f}"
            )

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
            amount,
            remarks,
            datetime.now().isoformat(timespec="seconds")
        ))

        payment_id = fetch_one(conn, "SELECT last_insert_rowid() AS id")["id"]

        _recalculate_installment_status(conn, installment_id)

        return int(payment_id)

    finally:
        conn.close()


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

    try:
        pay = _get_payment(conn, payment_id)
        if pay is None:
            raise ValueError("Payment not found")

        installment_id = int(pay["installment_id"])

        ins = _get_installment(conn, installment_id)
        if ins is None:
            raise ValueError("Installment missing")

        # Remaining allowance excluding this payment
        other_payments_total = fetch_one(
            conn,
            """
            SELECT COALESCE(SUM(amount), 0) AS s
            FROM payments
            WHERE installment_id = ? AND id <> ?
            """,
            (installment_id, payment_id)
        )["s"]

        due = round(float(ins["amount_due"]), 2)
        other_payments_total = round(float(other_payments_total), 2)
        allowed_max = round(due - other_payments_total, 2)

        if allowed_max < 0:
            allowed_max = 0.0

        new_amount = round(float(new_amount), 2)

        if new_amount > allowed_max + 0.0001:
            raise ValueError(
                f"Updated payment exceeds installment due amount.\n"
                f"Maximum allowed: {allowed_max:.2f}"
            )

        exec_one(
            conn,
            "UPDATE payments SET amount=?, actual_payment_date=?, remarks=? WHERE id=?",
            (new_amount, actual_payment_date, remarks, payment_id)
        )

        _recalculate_installment_status(conn, installment_id)

    finally:
        conn.close()


# ==========================================================
# RECEIPT CONTEXT
# ==========================================================
def list_receipt_context(payment_id: int):
    conn = connect()

    try:
        row = fetch_one(conn, """
            SELECT pay.*, 
                   ins.inst_no,
                   ins.due_date,
                   ins.amount_due,
                   ins.amount_paid,
                   ins.is_paid,
                   p.id AS plan_id,
                   p.plan_number,
                   p.item_name,
                   p.discount,
                   p.discount_mode,
                   p.final_payable,
                   p.advance_payment,
                   c.full_name AS customer_name
            FROM payments pay
            JOIN installments ins ON ins.id = pay.installment_id
            JOIN plans p ON p.id = ins.plan_id
            JOIN customers c ON c.id = p.customer_id
            WHERE pay.id=?
        """, (payment_id,))

        return row

    finally:
        conn.close()


# ==========================================================
# REMAINING BALANCE
# ==========================================================
def remaining_balance_for_plan(plan_id: int) -> float:
    conn = connect()

    try:
        p = fetch_one(conn, "SELECT final_payable FROM plans WHERE id=?", (plan_id,))
        if p is None:
            return 0.0

        paid = fetch_one(conn, """
            SELECT COALESCE(SUM(amount_paid),0) AS s
            FROM installments
            WHERE plan_id=?
        """, (plan_id,))["s"]

        remaining = round(float(p["final_payable"]) - float(paid), 2)
        if remaining < 0:
            remaining = 0.0

        return remaining

    finally:
        conn.close()


# ==========================================================
# PLAN COMPLETION
# ==========================================================
def is_plan_completed(plan_id: int) -> bool:
    conn = connect()

    try:
        row = fetch_one(conn, """
            SELECT
                COUNT(*) AS total_count,
                SUM(CASE WHEN is_paid = 1 THEN 1 ELSE 0 END) AS paid_count
            FROM installments
            WHERE plan_id = ?
        """, (plan_id,))

        if not row:
            return False

        total_count = int(row["total_count"] or 0)
        paid_count = int(row["paid_count"] or 0)

        return total_count > 0 and total_count == paid_count

    finally:
        conn.close()
        