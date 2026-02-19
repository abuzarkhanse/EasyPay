from __future__ import annotations
from datetime import datetime
from pathlib import Path
import random
import string
from reportlab.lib.pagesizes import A6
from reportlab.pdfgen import canvas
from ..config import RECEIPTS_DIR, APP_NAME
from ..core.db import connect, exec_one, fetch_one
from .payments import list_receipt_context, remaining_balance_for_plan

def _new_receipt_no() -> str:
    # Offline-safe unique-ish number
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = ''.join(random.choices(string.digits, k=4))
    return f"R{now}{rand}"

def generate_receipt_pdf(payment_id: int, company_name: str = "EasyPay") -> Path:
    ctx = list_receipt_context(payment_id)
    if ctx is None:
        raise ValueError("Cannot generate receipt: missing payment context")

    receipt_no = _new_receipt_no()
    pdf_path = RECEIPTS_DIR / f"{receipt_no}.pdf"

    # Calculate remaining balance from plan
    # Need plan_id:
    from ..core.db import connect, fetch_one
    conn = connect()
    plan_id = fetch_one(conn, """
        SELECT p.id AS plan_id
        FROM payments pay
        JOIN installments ins ON ins.id = pay.installment_id
        JOIN plans p ON p.id = ins.plan_id
        WHERE pay.id=?
    """, (payment_id,))["plan_id"]
    conn.close()
    remaining = remaining_balance_for_plan(int(plan_id))

    c = canvas.Canvas(str(pdf_path), pagesize=A6)
    w, h = A6
    y = h - 20

    def line(txt, dy=14, bold=False):
        nonlocal y
        if bold:
            c.setFont("Helvetica-Bold", 9)
        else:
            c.setFont("Helvetica", 8.5)
        c.drawString(12, y, str(txt))
        y -= dy

    line(company_name, bold=True, dy=16)
    line(f"Receipt No: {receipt_no}")
    line(f"Customer: {ctx['customer_name']}")
    line(f"Plan/Item: {ctx['item_name']}")
    line(f"Installment #: {ctx['inst_no']}")
    line(f"Due Date: {ctx['due_date']}")
    line(f"Payment Date: {ctx['actual_payment_date']}")
    line(f"Amount Due: {ctx['amount_due']}")
    line(f"Amount Paid (this): {ctx['amount']}")
    line(f"Total Paid (inst): {ctx['amount_paid']}")
    line(f"Discount (plan): {ctx['discount']}")
    line(f"Remaining Balance: {remaining}")
    if ctx["remarks"]:
        line(f"Remarks: {ctx['remarks']}", dy=16)

    line("Thank you", bold=True)
    c.showPage()
    c.save()

    # Store receipt record
    conn = connect()
    exec_one(conn, "INSERT INTO receipts(receipt_no, payment_id, pdf_path, created_at) VALUES(?,?,?,?)",
             (receipt_no, int(payment_id), str(pdf_path), datetime.now().isoformat(timespec="seconds")))
    conn.close()

    return pdf_path

def list_receipts(q: str = ""):
    conn = connect()
    if q.strip():
        rows = conn.execute("""
            SELECT r.*, c.full_name AS customer_name, p.item_name
            FROM receipts r
            JOIN payments pay ON pay.id = r.payment_id
            JOIN installments ins ON ins.id = pay.installment_id
            JOIN plans p ON p.id = ins.plan_id
            JOIN customers c ON c.id = p.customer_id
            WHERE r.receipt_no LIKE ? OR c.full_name LIKE ? OR p.item_name LIKE ?
            ORDER BY r.id DESC
        """, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    else:
        rows = conn.execute("""
            SELECT r.*, c.full_name AS customer_name, p.item_name
            FROM receipts r
            JOIN payments pay ON pay.id = r.payment_id
            JOIN installments ins ON ins.id = pay.installment_id
            JOIN plans p ON p.id = ins.plan_id
            JOIN customers c ON c.id = p.customer_id
            ORDER BY r.id DESC
        """).fetchall()
    conn.close()
    return rows
