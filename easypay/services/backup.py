from __future__ import annotations
from pathlib import Path
import shutil
from datetime import datetime
from ..config import DB_PATH, BACKUP_DIR, ensure_dirs

def make_backup() -> Path:
    ensure_dirs()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = BACKUP_DIR / f"easypay_{stamp}.backup"
    shutil.copy2(DB_PATH, dst)
    return dst

def restore_backup(backup_file: Path) -> None:
    ensure_dirs()
    if not backup_file.exists():
        raise FileNotFoundError(str(backup_file))
    shutil.copy2(backup_file, DB_PATH)
