from __future__ import annotations

import shutil
import time
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from easypay.config import DB_PATH, RECEIPTS_DIR
from easypay.core.db import connect, fetch_one, exec_one


# ==========================================================
# SETTINGS KEYS
# ==========================================================

BACKUP_LOCATION_KEY = "backup_location"


# ==========================================================
# INTERNAL HELPERS
# ==========================================================

def _timestamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def _default_backup_root() -> Path:
    """
    Fallback backup root if user has not selected any custom location yet.
    """
    # Same folder as database parent + backups
    return DB_PATH.parent / "backups"


def get_backup_root() -> Path:
    """
    Permanent backup root selected by user.
    Stored in settings table.
    """
    conn = connect()
    try:
        row = fetch_one(conn, "SELECT value FROM settings WHERE key=?", (BACKUP_LOCATION_KEY,))
        if row and row["value"]:
            path = Path(row["value"])
        else:
            path = _default_backup_root()
    finally:
        conn.close()

    path.mkdir(parents=True, exist_ok=True)
    return path


def set_backup_root(folder: Path | str) -> Path:
    """
    Save permanent backup location in DB settings.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    conn = connect()
    try:
        exec_one(
            conn,
            """
            INSERT INTO settings(key, value)
            VALUES(?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            (BACKUP_LOCATION_KEY, str(folder))
        )
    finally:
        conn.close()

    return folder


def ensure_backup_root() -> Path:
    """
    Returns the permanent backup location.
    If none saved yet, creates and saves default fallback.
    """
    conn = connect()
    try:
        row = fetch_one(conn, "SELECT value FROM settings WHERE key=?", (BACKUP_LOCATION_KEY,))
        if row and row["value"]:
            folder = Path(row["value"])
        else:
            folder = _default_backup_root()
            exec_one(
                conn,
                """
                INSERT INTO settings(key, value)
                VALUES(?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (BACKUP_LOCATION_KEY, str(folder))
            )
    finally:
        conn.close()

    folder.mkdir(parents=True, exist_ok=True)
    return folder


def get_emergency_backup_dir() -> Path:
    path = ensure_backup_root() / "emergency_backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_auto_backup_dir() -> Path:
    path = ensure_backup_root() / "auto_backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


# ==========================================================
# CREATE BACKUP ZIP
# ==========================================================

def create_backup_zip(target_zip_path: Path) -> Path:
    """
    Creates a ZIP containing:
    - easypay.db
    - receipts folder (optional)
    """
    target_zip_path = Path(target_zip_path)
    target_zip_path.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(target_zip_path, "w", compression=ZIP_DEFLATED) as zf:
        if DB_PATH.exists():
            zf.write(DB_PATH, arcname="easypay.db")

        if RECEIPTS_DIR.exists():
            for p in RECEIPTS_DIR.rglob("*"):
                if p.is_file():
                    zf.write(
                        p,
                        arcname=str(Path("receipts") / p.relative_to(RECEIPTS_DIR))
                    )

    return target_zip_path


# ==========================================================
# EMERGENCY / AUTO BACKUPS
# ==========================================================

def create_emergency_backup(reason: str = "auto") -> Path | None:
    """
    Silent automatic backup to selected permanent backup location.
    """
    try:
        name = f"EmergencyBackup_{reason}_{_timestamp()}.zip"
        path = get_emergency_backup_dir() / name
        return create_backup_zip(path)
    except Exception:
        # do not crash the app because of backup failure
        return None


def create_auto_backup() -> Path | None:
    """
    Silent auto backup to selected permanent backup location.
    """
    try:
        name = f"AutoBackup_{_timestamp()}.zip"
        path = get_auto_backup_dir() / name
        return create_backup_zip(path)
    except Exception:
        return None


# ==========================================================
# MANUAL BACKUPS
# ==========================================================

def create_manual_backup_to_folder(folder: Path) -> Path:
    """
    Manual backup to user-chosen folder.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    name = f"EasyPayBackup_{_timestamp()}.zip"
    return create_backup_zip(folder / name)


def create_manual_backup_to_file(zip_file_path: Path) -> Path:
    """
    Manual backup to user-chosen file path.
    """
    zip_file_path = Path(zip_file_path)
    if zip_file_path.suffix.lower() != ".zip":
        zip_file_path = zip_file_path.with_suffix(".zip")
    return create_backup_zip(zip_file_path)


# ==========================================================
# RESTORE
# ==========================================================

def restore_from_backup_zip(zip_path: Path) -> None:
    """
    Restores DB + receipts from a ZIP.
    (Use carefully; overwrite existing)
    """
    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise FileNotFoundError(str(zip_path))

    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(zip_path, "r") as zf:
        with zf.open("easypay.db") as src, open(DB_PATH, "wb") as dst:
            shutil.copyfileobj(src, dst)

        for member in zf.namelist():
            if member.startswith("receipts/") and not member.endswith("/"):
                out_path = RECEIPTS_DIR / Path(member).relative_to("receipts")
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src, open(out_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                    