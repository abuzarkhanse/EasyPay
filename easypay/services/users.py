from __future__ import annotations
from datetime import datetime
from typing import Optional
from ..core.db import connect, fetch_one, exec_one
from ..core.security import hash_password, verify_password
from ..config import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD

def ensure_admin_user() -> None:
    conn = connect()
    row = fetch_one(conn, "SELECT id FROM users LIMIT 1")
    if row is None:
        exec_one(conn,
            "INSERT INTO users(username, password_hash, role, created_at) VALUES(?,?,?,?)",
            (DEFAULT_ADMIN_USERNAME, hash_password(DEFAULT_ADMIN_PASSWORD), "admin", datetime.now().isoformat(timespec="seconds"))
        )
    conn.close()

def authenticate(username: str, password: str) -> bool:
    conn = connect()
    row = fetch_one(conn, "SELECT password_hash FROM users WHERE username=?", (username,))
    conn.close()
    if row is None:
        return False
    return verify_password(password, row["password_hash"])

def change_password(username: str, new_password: str) -> None:
    from ..core.security import hash_password
    conn = connect()
    exec_one(conn, "UPDATE users SET password_hash=? WHERE username=?", (hash_password(new_password), username))
    conn.close()
