from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDateEdit, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt, QDate
from ...core.db import connect, fetch_all
from ...core.dates import today_iso

class TrackingPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)

        header = QHBoxLayout()
        header.addWidget(QLabel("From:"))
        self.d1 = QDateEdit(); self.d1.setCalendarPopup(True); self.d1.setDate(QDate.currentDate().addMonths(-1))
        header.addWidget(self.d1)
        header.addWidget(QLabel("To:"))
        self.d2 = QDateEdit(); self.d2.setCalendarPopup(True); self.d2.setDate(QDate.currentDate().addMonths(2))
        header.addWidget(self.d2)
        self.btn = QPushButton("Refresh")
        header.addWidget(self.btn)
        header.addStretch(1)
        root.addLayout(header)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Customer","Item","Inst #","Due Date","Amount Due","Amount Paid","Paid?","Overdue?"])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        root.addWidget(self.table, 1)

        self.btn.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self):
        from_date = self.d1.date().toString("yyyy-MM-dd")
        to_date = self.d2.date().toString("yyyy-MM-dd")
        conn = connect()
        rows = fetch_all(conn, """
            SELECT c.full_name AS customer, p.item_name, ins.inst_no, ins.due_date, ins.amount_due, ins.amount_paid, ins.is_paid
            FROM installments ins
            JOIN plans p ON p.id = ins.plan_id
            JOIN customers c ON c.id = p.customer_id
            WHERE ins.due_date BETWEEN ? AND ?
            ORDER BY ins.is_paid ASC, ins.due_date ASC
        """, (from_date, to_date))
        conn.close()

        today = today_iso()
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            overdue = (row["is_paid"] == 0 and row["due_date"] < today)
            vals = [
                row["customer"],
                row["item_name"],
                str(row["inst_no"]),
                row["due_date"],
                f"{row['amount_due']:.2f}",
                f"{row['amount_paid']:.2f}",
                "Yes" if row["is_paid"] else "No",
                "OVERDUE" if overdue else "",
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                if overdue and c == 7:
                    it.setForeground(Qt.red)
                self.table.setItem(r, c, it)
