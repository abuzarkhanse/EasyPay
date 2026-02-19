from __future__ import annotations
import pandas as pd
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QComboBox
from ...core.db import connect, fetch_all

class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)

        header = QHBoxLayout()
        header.addWidget(QLabel("Export report to CSV:"))
        self.kind = QComboBox()
        self.kind.addItems(["Customers","Investors","Plans","Installments","Receipts"])
        self.btn = QPushButton("Export CSV")
        header.addWidget(self.kind)
        header.addWidget(self.btn)
        header.addStretch(1)
        root.addLayout(header)

        self.btn.clicked.connect(self.export)

        root.addWidget(QLabel("Tip: You can open the CSV in Excel. Everything is offline."))

    def export(self):
        k = self.kind.currentText()
        conn = connect()
        if k == "Customers":
            rows = fetch_all(conn, "SELECT * FROM customers ORDER BY id DESC")
        elif k == "Investors":
            rows = fetch_all(conn, "SELECT * FROM investors ORDER BY id DESC")
        elif k == "Plans":
            rows = fetch_all(conn, """
                SELECT p.*, c.full_name AS customer_name, i.full_name AS investor_name
                FROM plans p
                JOIN customers c ON c.id = p.customer_id
                LEFT JOIN investors i ON i.id = p.investor_id
                ORDER BY p.id DESC
            """)
        elif k == "Installments":
            rows = fetch_all(conn, """
                SELECT ins.*, p.item_name, c.full_name AS customer_name
                FROM installments ins
                JOIN plans p ON p.id = ins.plan_id
                JOIN customers c ON c.id = p.customer_id
                ORDER BY ins.due_date ASC
            """)
        else:
            rows = fetch_all(conn, """
                SELECT r.*, c.full_name AS customer_name, p.item_name
                FROM receipts r
                JOIN payments pay ON pay.id = r.payment_id
                JOIN installments ins ON ins.id = pay.installment_id
                JOIN plans p ON p.id = ins.plan_id
                JOIN customers c ON c.id = p.customer_id
                ORDER BY r.id DESC
            """)
        conn.close()

        if not rows:
            QMessageBox.information(self, "Empty", "No data to export.")
            return

        df = pd.DataFrame([dict(r) for r in rows])

        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", f"{k.lower()}.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            df.to_csv(path, index=False, encoding="utf-8-sig")
            QMessageBox.information(self, "Saved", f"Exported:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
