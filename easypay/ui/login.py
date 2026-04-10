from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFileDialog,
)

from ..services.users import authenticate
from ..core.db import connect, fetch_one
from ..services.backup import BACKUP_LOCATION_KEY, get_backup_root, set_backup_root


class LoginWindow(QWidget):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.setWindowTitle("EasyPay - Login")
        self.setFixedSize(380, 320)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)

        t = QLabel("EasyPay")
        t.setStyleSheet("font-size:22px;font-weight:900;")

        s = QLabel("Offline Installment Management")
        s.setStyleSheet("color:#94a3b8;")

        root.addWidget(t)
        root.addWidget(s)

        self.user = QLineEdit()
        self.user.setPlaceholderText("Username")

        self.passw = QLineEdit()
        self.passw.setPlaceholderText("Password")
        self.passw.setEchoMode(QLineEdit.Password)

        self.btn = QPushButton("Login")
        self.btn2 = QPushButton("Exit")
        self.btn2.setStyleSheet("background:#334155;")

        root.addSpacing(16)
        root.addWidget(self.user)
        root.addWidget(self.passw)
        root.addSpacing(10)
        root.addWidget(self.btn)
        root.addWidget(self.btn2)
        root.addStretch(1)

        self.btn.clicked.connect(self.try_login)
        self.btn2.clicked.connect(self.close)

    def _has_saved_backup_location(self) -> bool:
        conn = connect()
        try:
            row = fetch_one(
                conn,
                "SELECT value FROM settings WHERE key=?",
                (BACKUP_LOCATION_KEY,)
            )
            return bool(row and row["value"])
        finally:
            conn.close()

    def _ensure_backup_location_after_login(self):
        """
        Ask backup location only the first time after successful login.
        """
        if self._has_saved_backup_location():
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("Set Backup Location")
        msg.setIcon(QMessageBox.Information)
        msg.setText(
            "Please select a permanent location for Emergency and Auto backups.\n\n"
            "Recommended:\n"
            "- D Drive\n"
            "- Another partition\n"
            "- External drive\n\n"
            "This helps protect backups if Windows or C drive gets damaged."
        )
        msg.exec()

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Permanent Backup Folder",
            str(get_backup_root()),
        )

        if folder:
            set_backup_root(folder)
        else:
            # save fallback default if user cancels
            set_backup_root(get_backup_root())

    def try_login(self):
        u = self.user.text().strip()
        p = self.passw.text()

        if not u or not p:
            QMessageBox.warning(self, "Validation", "Enter username and password.")
            return

        if authenticate(u, p):
            try:
                self._ensure_backup_location_after_login()
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Backup Location",
                    f"Login successful, but backup location setup had an issue:\n\n{e}"
                )

            self.close()
            self.on_success(u)
        else:
            QMessageBox.critical(self, "Login Failed", "Incorrect username or password.")
            