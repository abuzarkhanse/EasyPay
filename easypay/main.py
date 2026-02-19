from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from .config import ensure_dirs, ASSETS_DIR
from .core.db import init_db
from .services.users import ensure_admin_user
from .ui.style import APP_QSS
from .ui.login import LoginWindow
from .ui.main_window import MainWindow

def run():
    ensure_dirs()
    init_db()
    ensure_admin_user()

    app = QApplication(sys.argv)
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
