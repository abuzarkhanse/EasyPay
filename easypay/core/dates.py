from __future__ import annotations
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

ISO_FMT = "%Y-%m-%d"

def today_iso() -> str:
    return date.today().strftime(ISO_FMT)

def to_date(iso: str) -> date:
    return datetime.strptime(iso, ISO_FMT).date()

def add_months(iso: str, months: int) -> str:
    d = to_date(iso)
    d2 = d + relativedelta(months=months)
    return d2.strftime(ISO_FMT)
