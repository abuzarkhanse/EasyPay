from __future__ import annotations
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"

APP_NAME = "EasyPay"

PROGRAM_DATA = Path(os.getenv("PROGRAMDATA", "C:/ProgramData"))
DATA_DIR = PROGRAM_DATA / APP_NAME

DB_PATH = DATA_DIR / "easypay.db"
RECEIPTS_DIR = DATA_DIR / "receipts"
BACKUP_DIR = DATA_DIR / "backups"
EMERGENCY_BACKUP_DIR = DATA_DIR / "emergency_backups"

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    EMERGENCY_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
