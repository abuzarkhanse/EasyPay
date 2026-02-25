from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from easypay.config import DB_PATH, RECEIPTS_DIR, BACKUP_DIR, EMERGENCY_BACKUP_DIR


def _timestamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


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
                    # store under receipts/...
                    zf.write(p, arcname=str(Path("receipts") / p.relative_to(RECEIPTS_DIR)))

    return target_zip_path


def create_emergency_backup(reason: str = "auto") -> Path | None:
    """
    Silent automatic backup to ProgramData emergency folder.
    """
    try:
        name = f"EmergencyBackup_{reason}_{_timestamp()}.zip"
        path = EMERGENCY_BACKUP_DIR / name
        return create_backup_zip(path)
    except Exception:
        # do not crash the app because of backup failure
        return None


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
    Manual backup to user-chosen file path (must end with .zip ideally).
    """
    zip_file_path = Path(zip_file_path)
    if zip_file_path.suffix.lower() != ".zip":
        zip_file_path = zip_file_path.with_suffix(".zip")
    return create_backup_zip(zip_file_path)


def restore_from_backup_zip(zip_path: Path) -> None:
    """
    Restores DB + receipts from a ZIP.
    (Use carefully; overwrite existing)
    """
    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise FileNotFoundError(str(zip_path))

    # Ensure dirs exist
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(zip_path, "r") as zf:
        # Restore DB
        with zf.open("easypay.db") as src, open(DB_PATH, "wb") as dst:
            shutil.copyfileobj(src, dst)

        # Restore receipts (if included)
        for member in zf.namelist():
            if member.startswith("receipts/") and not member.endswith("/"):
                out_path = RECEIPTS_DIR / Path(member).relative_to("receipts")
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src, open(out_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)