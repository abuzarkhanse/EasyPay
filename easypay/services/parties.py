from __future__ import annotations
from datetime import datetime
from typing import Optional
from ..core.db import connect, fetch_all, fetch_one, exec_one

def list_customers(q: str = ""):
    conn = connect()
    if q.strip():
        rows = fetch_all(conn, "SELECT * FROM customers WHERE full_name LIKE ? OR cnic LIKE ? OR phone LIKE ? ORDER BY id DESC",
                         (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        rows = fetch_all(conn, "SELECT * FROM customers ORDER BY id DESC")
    conn.close()
    return rows

def add_customer(full_name: str, cnic: str, phone: str, address: str):
    conn = connect()
    exec_one(conn, "INSERT INTO customers(full_name, cnic, phone, address, created_at) VALUES(?,?,?,?,?)",
             (full_name, cnic, phone, address, datetime.now().isoformat(timespec="seconds")))
    conn.close()

def update_customer(cid: int, full_name: str, cnic: str, phone: str, address: str):
    conn = connect()
    exec_one(conn, "UPDATE customers SET full_name=?, cnic=?, phone=?, address=? WHERE id=?",
             (full_name, cnic, phone, address, cid))
    conn.close()

def delete_customer(cid: int):
    conn = connect()
    exec_one(conn, "DELETE FROM customers WHERE id=?", (cid,))
    conn.close()

def list_investors(q: str = ""):
    conn = connect()
    if q.strip():
        rows = fetch_all(conn, "SELECT * FROM investors WHERE full_name LIKE ? OR cnic LIKE ? OR phone LIKE ? ORDER BY id DESC",
                         (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        rows = fetch_all(conn, "SELECT * FROM investors ORDER BY id DESC")
    conn.close()
    return rows

def add_investor(full_name: str, cnic: str, phone: str, address: str):
    conn = connect()
    exec_one(conn, "INSERT INTO investors(full_name, cnic, phone, address, created_at) VALUES(?,?,?,?,?)",
             (full_name, cnic, phone, address, datetime.now().isoformat(timespec="seconds")))
    conn.close()

def update_investor(iid: int, full_name: str, cnic: str, phone: str, address: str):
    conn = connect()
    exec_one(conn, "UPDATE investors SET full_name=?, cnic=?, phone=?, address=? WHERE id=?",
             (full_name, cnic, phone, address, iid))
    conn.close()

def delete_investor(iid: int):
    conn = connect()
    exec_one(conn, "DELETE FROM investors WHERE id=?", (iid,))
    conn.close()
