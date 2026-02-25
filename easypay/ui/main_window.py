from __future__ import annotations
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton, QStackedWidget, QMessageBox
from PySide6.QtCore import Qt

from .pages.dashboard import DashboardPage
from .pages.parties import CustomersPage, InvestorsPage
from .pages.plans import PlansPage
from .pages.payments import PaymentsPage
from .pages.tracking import TrackingPage
from .pages.receipts import ReceiptsPage
from .pages.reports import ReportsPage
from .pages.backup import BackupPage
from .pages.settings import SettingsPage

from PySide6.QtCore import QTimer
from easypay.services.backup import create_emergency_backup

class MainWindow(QMainWindow):
    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self.setWindowTitle("EasyPay")
        self.setMinimumSize(1200, 720)

        root = QWidget()
        self.setCentralWidget(root)

        layout = QHBoxLayout(root)
        layout.setContentsMargins(0,0,0,0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(260)
        sbl = QVBoxLayout(self.sidebar)
        sbl.setContentsMargins(16, 18, 16, 18)

        brand = QLabel("EasyPay")
        brand.setObjectName("Title")
        sub = QLabel("Offline Installments")
        sub.setObjectName("Subtitle")
        sbl.addWidget(brand)
        sbl.addWidget(sub)
        sbl.addSpacing(18)

        self.stack = QStackedWidget()

        # Auto emergency backup every 10 minutes (change if you want)
        self._auto_backup_timer = QTimer(self)
        self._auto_backup_timer.setInterval(10 * 60 * 1000)  # 10 minutes
        self._auto_backup_timer.timeout.connect(lambda: create_emergency_backup("timer"))
        self._auto_backup_timer.start()

        def closeEvent(self, event):
            create_emergency_backup("close")
            super().closeEvent(event)

        self.pages = [
            ("Dashboard", DashboardPage()),
            ("Customers", CustomersPage()),
            ("Investors", InvestorsPage()),
            ("Plans", PlansPage()),
            ("Payments", PaymentsPage()),
            ("Overdue & Upcoming", TrackingPage()),
            ("Receipts", ReceiptsPage()),
            ("Reports", ReportsPage()),
            ("Backup & Restore", BackupPage(on_restored=self.reload_all)),
            ("Settings", SettingsPage(username)),
        ]

        self.nav_buttons = []
        for idx, (name, page) in enumerate(self.pages):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setObjectName("NavBtn")
            btn.clicked.connect(lambda checked, i=idx: self.go(i))
            self.nav_buttons.append(btn)
            sbl.addWidget(btn)
            self.stack.addWidget(page)

        sbl.addStretch(1)
        logout = QPushButton("Logout")
        logout.setStyleSheet("background:#334155;")
        logout.clicked.connect(self._logout)
        sbl.addWidget(logout)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)

        self.go(0)

    def go(self, idx: int):
        self.stack.setCurrentIndex(idx)
        for i, b in enumerate(self.nav_buttons):
            b.setChecked(i == idx)
        # Refresh dashboard when returning
        name, page = self.pages[idx]
        if hasattr(page, "refresh"):
            try:
                page.refresh()
            except Exception:
                pass

    def reload_all(self):
        # simplest: recreate pages that read DB lists
        QMessageBox.information(self, "Reload", "Please restart the app to ensure all data is refreshed.")
        # For production you can implement deeper refresh hooks on each page.

    def _logout(self):
        QMessageBox.information(self, "Logout", "Restart the app to login again.")
        self.close()
