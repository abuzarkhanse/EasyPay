from __future__ import annotations

from datetime import date
from ..core.db import connect, fetch_one, fetch_all


def _month_key(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def _last_n_month_labels(last_n_months: int) -> list[str]:
    today = date.today()
    y = today.year
    m = today.month

    labels = []
    for _ in range(last_n_months):
        labels.append(_month_key(y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1

    labels.reverse()
    return labels


def dashboard_kpis():
    conn = connect()

    try:
        total_customers = fetch_one(
            conn,
            "SELECT COUNT(*) AS c FROM customers"
        )["c"] or 0

        total_investors = fetch_one(
            conn,
            "SELECT COUNT(*) AS c FROM investors"
        )["c"] or 0

        total_plans = fetch_one(
            conn,
            "SELECT COUNT(*) AS c FROM plans"
        )["c"] or 0

        completed_plans = fetch_one(conn, """
            SELECT COUNT(*) AS c
            FROM (
                SELECT p.id
                FROM plans p
                JOIN installments ins ON ins.plan_id = p.id
                GROUP BY p.id
                HAVING COUNT(ins.id) > 0
                   AND COUNT(ins.id) = SUM(CASE WHEN ins.is_paid = 1 THEN 1 ELSE 0 END)
            ) t
        """)["c"] or 0

        active_plans = max(int(total_plans) - int(completed_plans), 0)

        total_collected = fetch_one(
            conn,
            "SELECT COALESCE(SUM(amount), 0) AS s FROM payments"
        )["s"] or 0

        outstanding = fetch_one(conn, """
            SELECT COALESCE(SUM(
                CASE
                    WHEN p.final_payable - COALESCE(paid.s, 0) > 0
                    THEN p.final_payable - COALESCE(paid.s, 0)
                    ELSE 0
                END
            ), 0) AS s
            FROM plans p
            LEFT JOIN (
                SELECT ins.plan_id, COALESCE(SUM(ins.amount_paid), 0) AS s
                FROM installments ins
                GROUP BY ins.plan_id
            ) paid ON paid.plan_id = p.id
        """)["s"] or 0

        overdue_count = fetch_one(conn, """
            SELECT COUNT(*) AS c
            FROM installments
            WHERE is_paid = 0
              AND due_date < ?
        """, (date.today().isoformat(),))["c"] or 0

        this_month = fetch_one(conn, """
            SELECT COALESCE(SUM(amount), 0) AS s
            FROM payments
            WHERE SUBSTR(actual_payment_date, 1, 7) = ?
        """, (date.today().strftime("%Y-%m"),))["s"] or 0

        return {
            "total_customers": int(total_customers),
            "total_investors": int(total_investors),
            "active_plans": int(active_plans),
            "completed_plans": int(completed_plans),
            "total_collected": round(float(total_collected), 2),
            "outstanding": max(round(float(outstanding), 2), 0.0),
            "overdue_count": int(overdue_count),
            "this_month": round(float(this_month), 2),
        }

    finally:
        conn.close()


def monthly_collections(last_n_months: int = 12):
    conn = connect()

    try:
        rows = fetch_all(conn, """
            SELECT
                SUBSTR(actual_payment_date, 1, 7) AS ym,
                COALESCE(SUM(amount), 0) AS total
            FROM payments
            GROUP BY SUBSTR(actual_payment_date, 1, 7)
            ORDER BY ym ASC
        """)

        db_map = {r["ym"]: float(r["total"] or 0) for r in rows}
        labels = _last_n_month_labels(last_n_months)

        result = []
        for label in labels:
            result.append((label, db_map.get(label, 0.0)))

        return result

    finally:
        conn.close()
        