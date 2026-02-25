from __future__ import annotations
from datetime import date, datetime
from ..core.db import connect, fetch_one, fetch_all
from ..core.dates import today_iso, to_date

def dashboard_kpis():
    conn = connect()
    total_customers = fetch_one(conn, "SELECT COUNT(*) AS c FROM customers")["c"]
    total_investors = fetch_one(conn, "SELECT COUNT(*) AS c FROM investors")["c"]
    active_plans = fetch_one(conn, "SELECT COUNT(*) AS c FROM plans WHERE status='active'")["c"]
    total_discounts = fetch_one(conn, "SELECT COALESCE(SUM(discount),0) AS s FROM plans")["s"]

    outstanding = fetch_one(conn, """
        SELECT COALESCE(SUM(p.final_payable - paid.s),0) AS s
        FROM plans p
        LEFT JOIN (
            SELECT ins.plan_id, COALESCE(SUM(ins.amount_paid),0) AS s
            FROM installments ins
            GROUP BY ins.plan_id
        ) paid ON paid.plan_id = p.id
        WHERE p.status='active'
    """)["s"]

    overdue = fetch_one(conn, """
        SELECT COUNT(*) AS c
        FROM installments ins
        WHERE ins.is_paid=0 AND ins.due_date < ?
    """, (today_iso(),))["c"]

    upcoming = fetch_one(conn, """
        SELECT COUNT(*) AS c
        FROM installments ins
        WHERE ins.is_paid=0 AND ins.due_date >= ?
    """, (today_iso(),))["c"]

    conn.close()
    return {
        "total_customers": int(total_customers),
        "total_investors": int(total_investors),
        "active_plans": int(active_plans),
        "outstanding": float(round(outstanding, 2)),
        "total_discounts": float(round(total_discounts, 2)),
        "overdue_count": int(overdue),
        "upcoming_count": int(upcoming),
    }

def monthly_collections(last_n_months: int = 12):
    # Sum payments by month (based on actual_payment_date)
    conn = connect()
    rows = fetch_all(conn, """
        SELECT SUBSTR(actual_payment_date,1,7) AS ym, COALESCE(SUM(amount),0) AS total
        FROM payments
        GROUP BY ym
        ORDER BY ym ASC
    """)
    conn.close()
    # keep last_n_months
    if len(rows) > last_n_months:
        rows = rows[-last_n_months:]
    return [(r["ym"], float(r["total"])) for r in rows]
