from __future__ import annotations

from pathlib import Path

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import portrait

from easypay.config import RECEIPTS_DIR
from easypay.core.db import connect, fetch_one, fetch_all


# ==========================================================
# HELPERS
# ==========================================================

def _safe_filename(name: str) -> str:
    bad = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for ch in bad:
        name = name.replace(ch, "_")
    return name.strip()


def _ensure_receipts_dir() -> None:
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)


def _is_plan_completed(conn, plan_id: int) -> bool:
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


def _resolve_profit_mode(plan: dict) -> str:
    """
    New field is profit_mode.
    Fallback to old discount_mode for compatibility with older saved plans.
    """
    profit_mode = (plan.get("profit_mode") or "").strip().lower()
    if profit_mode in {"total", "principal"}:
        return profit_mode

    legacy_discount_mode = (plan.get("discount_mode") or "").strip().lower()
    if legacy_discount_mode == "final":
        return "total"
    if legacy_discount_mode == "principal":
        return "principal"

    return "principal"


def _profit_mode_text(profit_mode: str) -> str:
    return "Total Price" if profit_mode == "total" else "Principal (Total - Advance)"


# ==========================================================
# PROFESSIONAL THERMAL RECEIPT (58mm)
# ==========================================================
def generate_receipt_pdf(payment_id: int, company_name: str = "EasyPay") -> str:
    """
    Creates a printable PDF receipt suitable for 58mm thermal printers.
    Stores PDF in receipts folder.
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
               p.id AS plan_id,
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

    _ensure_receipts_dir()

    width = 58 * mm
    height = 220 * mm
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

    elements.append(Paragraph(f"<b>{company_name}</b>", center))
    elements.append(Paragraph("Offline Installments Receipt", center))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("-" * 32, center))

    elements.append(Paragraph(f"Receipt #: {row['id']}", normal))
    elements.append(Paragraph(f"Paid Date: {row['actual_payment_date']}", normal))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph(f"Customer: {row['customer_name']}", normal))
    elements.append(Paragraph(f"Item/Plan: {row['item_name']}", normal))
    elements.append(Spacer(1, 4))

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

    if row.get("remarks"):
        elements.append(Paragraph(f"Remarks: {row['remarks']}", normal))
        elements.append(Spacer(1, 4))

    elements.append(Paragraph("Thank you!", center))
    elements.append(Paragraph("Please keep this receipt", center))

    doc.build(elements)
    return str(pdf_path)


# ==========================================================
# FINAL COMPLETION RECEIPT
# ==========================================================
def generate_final_completion_receipt(plan_id: int, company_name: str = "EasyPay") -> str:
    """
    Generate one final summary receipt when all installments are completed.
    """
    conn = connect()

    plan = fetch_one(conn, """
        SELECT
            p.id,
            p.plan_number,
            p.item_name,
            p.total_price,
            p.advance_payment,
            p.profit_pct,
            p.discount,
            p.discount_mode,
            p.profit_mode,
            p.final_amount,
            p.final_payable,
            p.start_date,
            p.created_at,
            c.full_name AS customer_name,
            c.phone AS customer_phone,
            c.cnic AS customer_cnic
        FROM plans p
        JOIN customers c ON c.id = p.customer_id
        WHERE p.id = ?
    """, (plan_id,))

    if not plan:
        conn.close()
        raise ValueError("Plan not found.")

    if not _is_plan_completed(conn, plan_id):
        conn.close()
        raise ValueError("Final completion receipt can only be generated when all installments are fully paid.")

    installments = fetch_all(conn, """
        SELECT
            inst_no,
            due_date,
            amount_due,
            amount_paid,
            is_paid
        FROM installments
        WHERE plan_id = ?
        ORDER BY inst_no
    """, (plan_id,))

    paid_summary = fetch_one(conn, """
        SELECT
            COUNT(pay.id) AS total_payment_entries,
            COALESCE(SUM(pay.amount), 0) AS total_paid,
            MAX(pay.actual_payment_date) AS last_payment_date
        FROM payments pay
        JOIN installments ins ON ins.id = pay.installment_id
        WHERE ins.plan_id = ?
    """, (plan_id,))

    conn.close()

    plan = dict(plan)
    installments = [dict(x) for x in installments]
    paid_summary = dict(paid_summary) if paid_summary else {}

    _ensure_receipts_dir()

    safe_customer = _safe_filename(plan["customer_name"])
    pdf_path = Path(RECEIPTS_DIR) / f"final_receipt_plan_{plan_id}_{safe_customer}.pdf"

    width = 58 * mm
    height = 260 * mm

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
    normal = ParagraphStyle(name="normal", parent=styles["Normal"], fontSize=8.5)

    elements = []

    elements.append(Paragraph(f"<b>{company_name}</b>", center))
    elements.append(Paragraph("Final Completion Receipt", center))
    elements.append(Paragraph("Installment Plan Fully Paid", center))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("-" * 32, center))

    elements.append(Paragraph(f"Plan ID: {plan['id']}", normal))
    elements.append(Paragraph(f"Plan No: {plan.get('plan_number') or '-'}", normal))
    elements.append(Paragraph(f"Completion Date: {paid_summary.get('last_payment_date') or '-'}", normal))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph(f"Customer: {plan['customer_name']}", normal))
    if plan.get("customer_phone"):
        elements.append(Paragraph(f"Phone: {plan['customer_phone']}", normal))
    if plan.get("customer_cnic"):
        elements.append(Paragraph(f"CNIC: {plan['customer_cnic']}", normal))
    elements.append(Paragraph(f"Item/Plan: {plan['item_name']}", normal))
    elements.append(Spacer(1, 5))

    elements.append(Paragraph("-" * 32, center))

    profit_mode = _resolve_profit_mode(plan)
    profit_mode_text = _profit_mode_text(profit_mode)

    summary_data = [
        ["Total Price", f"{float(plan['total_price']):,.2f}"],
        ["Advance", f"{float(plan['advance_payment']):,.2f}"],
        ["Profit %", f"{float(plan['profit_pct']):,.2f}"],
        ["Discount", f"{float(plan['discount']):,.2f}"],
        ["Profit Apply On", profit_mode_text],
        ["Final Amount", f"{float(plan['final_amount']):,.2f}"],
        ["Final Payable", f"{float(plan['final_payable']):,.2f}"],
        ["Installments", str(len(installments))],
        ["Payment Entries", str(int(paid_summary.get('total_payment_entries') or 0))],
        ["Total Paid", f"{float(paid_summary.get('total_paid') or 0):,.2f}"],
    ]

    tbl = Table(summary_data, colWidths=[26 * mm, 26 * mm])
    tbl.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    elements.append(tbl)

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("-" * 32, center))
    elements.append(Paragraph("<b>Completion Status: FULLY PAID</b>", center))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("All installments for this plan have been completed successfully.", center))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Thank you!", center))
    elements.append(Paragraph("Final payment completed receipt", center))

    doc.build(elements)
    return str(pdf_path)


# ==========================================================
# PLAN COMPLETION CHECK
# ==========================================================
def is_plan_fully_paid(plan_id: int) -> bool:
    conn = connect()
    try:
        return _is_plan_completed(conn, plan_id)
    finally:
        conn.close()


def completed_plans_for_receipts(search: str = ""):
    conn = connect()

    if search:
        rows = fetch_all(conn, """
            SELECT
                p.id AS plan_id,
                p.plan_number,
                p.item_name,
                p.final_payable,
                c.full_name AS customer_name,
                MAX(pay.actual_payment_date) AS completion_date,
                COUNT(ins.id) AS total_installments,
                SUM(CASE WHEN ins.is_paid = 1 THEN 1 ELSE 0 END) AS paid_installments
            FROM plans p
            JOIN customers c ON c.id = p.customer_id
            JOIN installments ins ON ins.plan_id = p.id
            LEFT JOIN payments pay ON pay.installment_id = ins.id
            WHERE c.full_name LIKE ?
               OR p.item_name LIKE ?
               OR p.plan_number LIKE ?
            GROUP BY p.id, p.plan_number, p.item_name, p.final_payable, c.full_name
            HAVING COUNT(ins.id) = SUM(CASE WHEN ins.is_paid = 1 THEN 1 ELSE 0 END)
            ORDER BY p.id DESC
        """, (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        rows = fetch_all(conn, """
            SELECT
                p.id AS plan_id,
                p.plan_number,
                p.item_name,
                p.final_payable,
                c.full_name AS customer_name,
                MAX(pay.actual_payment_date) AS completion_date,
                COUNT(ins.id) AS total_installments,
                SUM(CASE WHEN ins.is_paid = 1 THEN 1 ELSE 0 END) AS paid_installments
            FROM plans p
            JOIN customers c ON c.id = p.customer_id
            JOIN installments ins ON ins.plan_id = p.id
            LEFT JOIN payments pay ON pay.installment_id = ins.id
            GROUP BY p.id, p.plan_number, p.item_name, p.final_payable, c.full_name
            HAVING COUNT(ins.id) = SUM(CASE WHEN ins.is_paid = 1 THEN 1 ELSE 0 END)
            ORDER BY p.id DESC
        """)

    conn.close()

    result = []
    for r in rows:
        r = dict(r)
        r["receipt_type"] = "Final Completion"
        r["pdf_path"] = str(
            RECEIPTS_DIR / f"final_receipt_plan_{r['plan_id']}_{_safe_filename(r['customer_name'])}.pdf"
        )
        result.append(r)

    return result


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
                p.item_name,
                p.id AS plan_id
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
                p.item_name,
                p.id AS plan_id
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
        r["receipt_type"] = "Installment"
        r["pdf_path"] = str(RECEIPTS_DIR / f"receipt_{rid}.pdf") if rid else ""
        result.append(r)

    return result
