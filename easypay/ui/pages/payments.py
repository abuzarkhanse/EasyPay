from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QDoubleSpinBox, QDateEdit, QTextEdit
from PySide6.QtCore import Qt, QDate
from ...core.db import connect, fetch_all
from ...services.payments import add_payment, edit_payment
from ...services.receipts import generate_receipt_pdf

class PaymentDialog(QDialog):
    def __init__(self, title: str, default_amount: float, is_edit: bool = False):
        super().__init__()
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        lay = QVBoxLayout(self)
        form = QFormLayout()

        self.amount = QDoubleSpinBox(); self.amount.setMaximum(1e12); self.amount.setDecimals(2)
        self.amount.setValue(default_amount)
        self.date = QDateEdit(); self.date.setCalendarPopup(True); self.date.setDate(QDate.currentDate())
        self.remarks = QTextEdit(); self.remarks.setFixedHeight(80)

        form.addRow("Amount*", self.amount)
        form.addRow("Actual Payment Date*", self.date)
        form.addRow("Remarks", self.remarks)
        lay.addLayout(form)

        btns = QHBoxLayout()
        self.save = QPushButton("Save")
        self.cancel = QPushButton("Cancel")
        self.cancel.setStyleSheet("background:#334155;")
        btns.addStretch(1)
        btns.addWidget(self.cancel)
        btns.addWidget(self.save)
        lay.addLayout(btns)

        self.cancel.clicked.connect(self.reject)
        self.save.clicked.connect(self.accept)

    def values(self) -> dict:
        return {
            "amount": float(self.amount.value()),
            "actual_payment_date": self.date.date().toString("yyyy-MM-dd"),
            "remarks": self.remarks.toPlainText().strip(),
        }

class PaymentsPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)

        header = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search unpaid installments (customer, item, due date)...")
        self.btn_pay = QPushButton("Add Payment")
        self.btn_edit = QPushButton("Edit Payment (selected payment)")
        header.addWidget(self.search, 1)
        header.addWidget(self.btn_pay)
        header.addWidget(self.btn_edit)
        root.addLayout(header)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            "Installment ID","Customer","Item","Inst #","Due Date","Amount Due","Amount Paid","Paid?","Plan ID","Last Payment ID"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, 1)

        self.search.textChanged.connect(self.refresh)
        self.btn_pay.clicked.connect(self.pay)
        self.btn_edit.clicked.connect(self.edit_last_payment)

        self.refresh()

    def refresh(self):
        q = self.search.text().strip()
        conn = connect()
        if q:
            rows = fetch_all(conn, """
                SELECT ins.id AS installment_id, c.full_name AS customer, p.item_name, ins.inst_no, ins.due_date,
                       ins.amount_due, ins.amount_paid, ins.is_paid, p.id AS plan_id,
                       (SELECT id FROM payments WHERE installment_id=ins.id ORDER BY id DESC LIMIT 1) AS last_payment_id
                FROM installments ins
                JOIN plans p ON p.id = ins.plan_id
                JOIN customers c ON c.id = p.customer_id
                WHERE c.full_name LIKE ? OR p.item_name LIKE ? OR ins.due_date LIKE ?
                ORDER BY ins.is_paid ASC, ins.due_date ASC
            """, (f"%{q}%", f"%{q}%", f"%{q}%"))
        else:
            rows = fetch_all(conn, """
                SELECT ins.id AS installment_id, c.full_name AS customer, p.item_name, ins.inst_no, ins.due_date,
                       ins.amount_due, ins.amount_paid, ins.is_paid, p.id AS plan_id,
                       (SELECT id FROM payments WHERE installment_id=ins.id ORDER BY id DESC LIMIT 1) AS last_payment_id
                FROM installments ins
                JOIN plans p ON p.id = ins.plan_id
                JOIN customers c ON c.id = p.customer_id
                ORDER BY ins.is_paid ASC, ins.due_date ASC
            """)
        conn.close()

        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            vals = [
                str(row["installment_id"]),
                row["customer"],
                row["item_name"],
                str(row["inst_no"]),
                row["due_date"],
                f"{row['amount_due']:.2f}",
                f"{row['amount_paid']:.2f}",
                "Yes" if row["is_paid"] else "No",
                str(row["plan_id"]),
                str(row["last_payment_id"] or ""),
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(r, c, it)

    def _sel_row(self):
        sel = self.table.selectedItems()
        if not sel: return None
        return self.table.currentRow()

    def pay(self):
        r = self._sel_row()
        if r is None:
            QMessageBox.information(self, "Select", "Select an installment row first.")
            return
        installment_id = int(self.table.item(r,0).text())
        amount_due = float(self.table.item(r,5).text())
        amount_paid = float(self.table.item(r,6).text())
        remaining = max(amount_due - amount_paid, 0.0)

        dlg = PaymentDialog("Add Payment", default_amount=remaining)
        if dlg.exec():
            v = dlg.values()
            try:
                payment_id = add_payment(installment_id, v["amount"], v["actual_payment_date"], v["remarks"])
                pdf = generate_receipt_pdf(payment_id, company_name="EasyPay")
                QMessageBox.information(self, "Receipt Generated", f"Receipt saved:\n{pdf}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
            self.refresh()

    def edit_last_payment(self):
        r = self._sel_row()
        if r is None:
            QMessageBox.information(self, "Select", "Select a row first.")
            return
        last_payment_id_txt = self.table.item(r,9).text().strip()
        if not last_payment_id_txt:
            QMessageBox.information(self, "No payment", "Selected installment has no payment yet.")
            return
        payment_id = int(last_payment_id_txt)

        # Default to same remaining (user can edit)
        amount_due = float(self.table.item(r,5).text())
        amount_paid = float(self.table.item(r,6).text())
        dlg = PaymentDialog("Edit Last Payment", default_amount=amount_paid, is_edit=True)
        if dlg.exec():
            v = dlg.values()
            try:
                edit_payment(payment_id, v["amount"], v["actual_payment_date"], v["remarks"])
                pdf = generate_receipt_pdf(payment_id, company_name="EasyPay")  # new receipt every edit
                QMessageBox.information(self, "Receipt Generated", f"Updated receipt saved:\n{pdf}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
            self.refresh()
