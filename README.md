# EasyPay – Offline Installment Management System (Rebuild)

This is a **fully offline** Windows desktop app rebuild with a modern dashboard-style UI.

**Tech stack**
- Python 3.11+
- PySide6 (Qt) for modern desktop UI
- SQLite (local file database)
- bcrypt for secure password hashing
- reportlab for PDF receipts
- pandas + matplotlib for exports + dashboard chart

## 1) Setup (Developer)

### Create venv
```bash
python -m venv .venv
.venv\Scripts\activate
```

### Install deps
```bash
pip install -r requirements.txt
```

### Run
```bash
python -m easypay
```

The first run will create:
- `data/easypay.db` (SQLite DB)
- An admin user:
  - username: `admin`
  - password: `admin123`  (change immediately from **Settings**)

## 2) Build Windows EXE (PyInstaller)
```bash
pyinstaller --noconfirm --clean --windowed --name EasyPay ^
  --icon assets/EasyPay.ico ^
  --add-data "assets;assets" ^
  --add-data "data;data" ^
  -m easypay
```

Output: `dist/EasyPay/EasyPay.exe`

## 3) Backup / Restore
Inside the app: **Backup & Restore**
- Backup creates a `.backup` file (a copy of the DB).
- Restore replaces the local DB with your backup.

## 4) Notes
- Everything is local: no internet calls, no cloud.
- If you want multi-PC sharing later, that becomes a different requirement (LAN sync / server).
