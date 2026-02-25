from __future__ import annotations
import sqlite3
from typing import Iterable, Any, Optional, Tuple
from ..config import DB_PATH, ensure_dirs


# ==========================================================
# CONNECTION
# ==========================================================

def connect() -> sqlite3.Connection:
    """
    Central SQLite connection creator.
    Includes WAL mode + timeout to prevent 'database is locked'.
    """
    ensure_dirs()

    conn = sqlite3.connect(
        DB_PATH,
        timeout=10,  # wait up to 10 seconds before throwing lock error
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    # 🔥 Critical for stability
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")      # prevents most locking issues
    conn.execute("PRAGMA synchronous = NORMAL;")    # safe + better performance
    conn.execute("PRAGMA busy_timeout = 5000;")     # wait 5 seconds if locked

    return conn


# ==========================================================
# HELPERS
# ==========================================================

def exec_many(conn: sqlite3.Connection, sql: str, rows: Iterable[Tuple[Any, ...]]) -> None:
    conn.executemany(sql, rows)
    conn.commit()


def exec_one(conn: sqlite3.Connection, sql: str, params: Tuple[Any, ...] = ()) -> None:
    conn.execute(sql, params)
    conn.commit()


def fetch_all(conn: sqlite3.Connection, sql: str, params: Tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    cur = conn.execute(sql, params)
    return cur.fetchall()


def fetch_one(conn: sqlite3.Connection, sql: str, params: Tuple[Any, ...] = ()) -> Optional[sqlite3.Row]:
    cur = conn.execute(sql, params)
    return cur.fetchone()


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

def init_db() -> None:
    conn = connect()

    try:

        # ---------------- USERS ----------------
        conn.execute("""
        CREATE TABLE IF NOT EXISTS plans(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_number TEXT UNIQUE NOT NULL,
            customer_id INTEGER NOT NULL,
            investor_id INTEGER,
            item_name TEXT NOT NULL,
            total_price REAL NOT NULL,
            advance_payment REAL NOT NULL,
            profit_pct REAL NOT NULL,
            months INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            discount REAL NOT NULL DEFAULT 0,
            final_amount REAL NOT NULL,
            final_payable REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
            FOREIGN KEY(investor_id) REFERENCES investors(id) ON DELETE SET NULL
        );
        """)

        # ---------------- CUSTOMERS ----------------
        conn.execute("""
        CREATE TABLE IF NOT EXISTS customers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            cnic TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)

        # ---------------- INVESTORS ----------------
        conn.execute("""
        CREATE TABLE IF NOT EXISTS investors(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            cnic TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)

        # ---------------- PLANS ----------------
        conn.execute("""
        CREATE TABLE IF NOT EXISTS plans(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            investor_id INTEGER,
            item_name TEXT NOT NULL,
            total_price REAL NOT NULL,
            advance_payment REAL NOT NULL,
            profit_pct REAL NOT NULL,
            months INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            discount REAL NOT NULL DEFAULT 0,
            final_amount REAL NOT NULL,
            final_payable REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
            FOREIGN KEY(investor_id) REFERENCES investors(id) ON DELETE SET NULL
        );
        """)

        # ---------------- INSTALLMENTS ----------------
        conn.execute("""
        CREATE TABLE IF NOT EXISTS installments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            inst_no INTEGER NOT NULL,
            due_date TEXT NOT NULL,
            amount_due REAL NOT NULL,
            amount_paid REAL NOT NULL DEFAULT 0,
            is_paid INTEGER NOT NULL DEFAULT 0,
            remarks TEXT,
            UNIQUE(plan_id, inst_no),
            FOREIGN KEY(plan_id) REFERENCES plans(id) ON DELETE CASCADE
        );
        """)

        # ---------------- PAYMENTS ----------------
        conn.execute("""
        CREATE TABLE IF NOT EXISTS payments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            installment_id INTEGER NOT NULL,
            actual_payment_date TEXT NOT NULL,
            amount REAL NOT NULL,
            remarks TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(installment_id) REFERENCES installments(id) ON DELETE CASCADE
        );
        """)

        # ---------------- RECEIPTS ----------------
        conn.execute("""
        CREATE TABLE IF NOT EXISTS receipts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_no TEXT UNIQUE NOT NULL,
            payment_id INTEGER NOT NULL,
            pdf_path TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(payment_id) REFERENCES payments(id) ON DELETE CASCADE
        );
        """)

        # ---------------- SETTINGS ----------------
        conn.execute("""
        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)

        conn.commit()

    finally:
        conn.close()