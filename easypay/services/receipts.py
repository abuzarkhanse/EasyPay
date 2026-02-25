from __future__ import annotations

from pathlib import Path
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import portrait

from easypay.config import RECEIPTS_DIR
from easypay.core.db import connect, fetch_one, fetch_all


# ==========================================================
# PROFESSIONAL THERMAL RECEIPT (58mm)
# ==========================================================
def generate_receipt_pdf(payment_id: int, company_name: str = "EasyPay") -> str:
    """
    Creates a printable PDF receipt suitable for 58mm thermal printers.
    Stores PDF in ProgramData receipts folder.
    """
    conn = connect()

    row = fetch_one(conn, """
        SELECT pay.id,
               pay.actual_payment_date,
               pay.amount,
               pay.remarks,
               ins.inst_no,
               ins.due_date,
               ins.amount_due,
               ins.amount_paid,
               p.item_name,
               p.final_payable,
               c.full_name AS customer_name
        FROM payments pay
        JOIN installments ins ON ins.id = pay.installment_id
        JOIN plans p ON p.id = ins.plan_id
        JOIN customers c ON c.id = p.customer_id
        WHERE pay.id=?
    """, (payment_id,))

    conn.close()

    if not row:
        raise ValueError("Payment not found for receipt.")
    
    row = dict(row)

    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

    # 58mm roll width
    width = 58 * mm
    height = 220 * mm  # enough for most receipts
    pdf_path = Path(RECEIPTS_DIR) / f"receipt_{payment_id}.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=portrait((width, height)),
        leftMargin=4,
        rightMargin=4,
        topMargin=8,
        bottomMargin=8,
    )

    styles = getSampleStyleSheet()
    center = ParagraphStyle(name="center", parent=styles["Normal"], alignment=1, fontSize=10)
    normal = ParagraphStyle(name="normal", parent=styles["Normal"], fontSize=9)

    elements = []

    # Header
    elements.append(Paragraph(f"<b>{company_name}</b>", center))
    elements.append(Paragraph("Offline Installments Receipt", center))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("-" * 32, center))

    # Meta
    elements.append(Paragraph(f"Receipt #: {row['id']}", normal))
    elements.append(Paragraph(f"Paid Date: {row['actual_payment_date']}", normal))
    elements.append(Spacer(1, 4))

    # Customer & Item
    elements.append(Paragraph(f"Customer: {row['customer_name']}", normal))
    elements.append(Paragraph(f"Item/Plan: {row['item_name']}", normal))
    elements.append(Spacer(1, 4))

    # Installment
    elements.append(Paragraph(f"Installment #: {row['inst_no']}", normal))
    elements.append(Paragraph(f"Due Date: {row['due_date']}", normal))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("-" * 32, center))

    remaining = float(row["final_payable"]) - float(row["amount_paid"])
    if remaining < 0:
        remaining = 0.0

    data = [
        ["Amount Due", f"{float(row['amount_due']):,.2f}"],
        ["Amount Paid", f"{float(row['amount']):,.2f}"],
        ["Remaining", f"{float(remaining):,.2f}"],
    ]

    tbl = Table(data, colWidths=[30 * mm, 22 * mm])
    tbl.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))

    elements.append(tbl)
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("-" * 32, center))

    # Remarks
    if row.get("remarks"):
        elements.append(Paragraph(f"Remarks: {row['remarks']}", normal))
        elements.append(Spacer(1, 4))

    elements.append(Paragraph("Thank you!", center))
    elements.append(Paragraph("Please keep this receipt", center))

    doc.build(elements)
    return str(pdf_path)


# ==========================================================
# LIST RECEIPTS (for UI)
# ==========================================================

def list_receipts(search: str = ""):
    conn = connect()

    if search:
        rows = fetch_all(conn, """
            SELECT
                pay.id AS id,
                pay.id AS receipt_no,
                pay.created_at,
                pay.actual_payment_date,
                pay.amount,
                COALESCE(pay.remarks,'') AS remarks,
                c.full_name AS customer_name,
                p.item_name
            FROM payments pay
            JOIN installments ins ON ins.id = pay.installment_id
            JOIN plans p ON p.id = ins.plan_id
            JOIN customers c ON c.id = p.customer_id
            WHERE c.full_name LIKE ?
               OR p.item_name LIKE ?
               OR pay.actual_payment_date LIKE ?
               OR pay.created_at LIKE ?
            ORDER BY pay.id DESC
        """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        rows = fetch_all(conn, """
            SELECT
                pay.id AS id,
                pay.id AS receipt_no,
                pay.created_at,
                pay.actual_payment_date,
                pay.amount,
                COALESCE(pay.remarks,'') AS remarks,
                c.full_name AS customer_name,
                p.item_name
            FROM payments pay
            JOIN installments ins ON ins.id = pay.installment_id
            JOIN plans p ON p.id = ins.plan_id
            JOIN customers c ON c.id = p.customer_id
            ORDER BY pay.id DESC
        """)

    conn.close()

    result = []
    for r in rows:
        r = dict(r)
        rid = r.get("id")
        r["pdf_path"] = str(RECEIPTS_DIR / f"receipt_{rid}.pdf") if rid else ""
        result.append(r)

    return result