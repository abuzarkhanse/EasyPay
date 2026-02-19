from __future__ import annotations
import os
from pathlib import Path

APP_NAME = "EasyPay"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"

DB_PATH = DATA_DIR / "easypay.db"
RECEIPTS_DIR = DATA_DIR / "receipts"
BACKUP_DIR = DATA_DIR / "backups"

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

def ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    RECEIPTS_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)
