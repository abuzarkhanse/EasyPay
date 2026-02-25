from __future__ import annotations
import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox
from ...services.users import change_password
from ...core.db import connect, fetch_one, exec_one

class SettingsPage(QWidget):
    def __init__(self, username: str):
        super().__init__()
        self.username = username
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)

        form = QFormLayout()
        self.company = QLineEdit()
        self.newpass = QLineEdit(); self.newpass.setEchoMode(QLineEdit.Password)
        self.newpass2 = QLineEdit(); self.newpass2.setEchoMode(QLineEdit.Password)

        form.addRow("Company name (for receipts)", self.company)
        form.addRow("New password", self.newpass)
        form.addRow("Confirm password", self.newpass2)
        root.addLayout(form)

        self.btn_save = QPushButton("Save Settings")
        root.addWidget(self.btn_save)
        self.btn_save.clicked.connect(self.save)

        self.load()

    def load(self):
        conn = connect()
        row = fetch_one(conn, "SELECT value FROM settings WHERE key='company_name'")
        conn.close()
        self.company.setText(row["value"] if row else "EasyPay")

    def save(self):
        company = self.company.text().strip() or "EasyPay"
        if self.newpass.text().strip():
            if self.newpass.text() != self.newpass2.text():
                QMessageBox.warning(self, "Validation", "Passwords do not match.")
                return
            if len(self.newpass.text()) < 6:
                QMessageBox.warning(self, "Validation", "Password must be at least 6 characters.")
                return
            try:
                change_password(self.username, self.newpass.text())
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                return

        conn = connect()
        exec_one(conn, "INSERT INTO settings(key,value) VALUES('company_name',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (company,))
        conn.close()
        QMessageBox.information(self, "Saved", "Settings updated.")
