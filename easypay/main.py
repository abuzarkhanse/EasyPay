from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from easypay.config import ensure_dirs, ASSETS_DIR
from easypay.core.db import init_db
from easypay.services.users import ensure_admin_user
from easypay.ui.style import APP_QSS
from easypay.ui.login import LoginWindow
from easypay.ui.main_window import MainWindow
from easypay.core.db import init_db

def run():
    ensure_dirs()
    init_db()
    ensure_admin_user()

    app = QApplication(sys.argv)

    from PySide6.QtGui import QPalette, QColor

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#0f172a"))
    palette.setColor(QPalette.WindowText, QColor("#e5e7eb"))
    palette.setColor(QPalette.Base, QColor("#111827"))
    palette.setColor(QPalette.AlternateBase, QColor("#1f2937"))
    palette.setColor(QPalette.Text, QColor("#e5e7eb"))
    palette.setColor(QPalette.Button, QColor("#1f2937"))
    palette.setColor(QPalette.ButtonText, QColor("#e5e7eb"))

    app.setPalette(palette)

    app.setStyleSheet(APP_QSS)

    icon_path = ASSETS_DIR / "EasyPay.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    main_ref = {"win": None}

    def on_success(username: str):
        w = MainWindow(username)
        main_ref["win"] = w
        w.show()

    login = LoginWindow(on_success=on_success)
    login.show()

    sys.exit(app.exec())
