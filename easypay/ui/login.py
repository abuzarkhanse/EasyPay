from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt
from ..services.users import authenticate

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

    def try_login(self):
        u = self.user.text().strip()
        p = self.passw.text()
        if not u or not p:
            QMessageBox.warning(self, "Validation", "Enter username and password.")
            return
        if authenticate(u, p):
            self.close()
            self.on_success(u)
        else:
            QMessageBox.critical(self, "Login Failed", "Incorrect username or password.")
