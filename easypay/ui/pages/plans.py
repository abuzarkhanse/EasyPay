from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QDialog, QFormLayout, QComboBox, QDoubleSpinBox, QSpinBox, QDateEdit, QLabel, QCheckBox
from PySide6.QtCore import Qt, QDate

from ...services.parties import list_customers, list_investors
from ...services.plans import create_plan, list_plans, installments_for_plan, compute_amounts

class NewPlanDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Create Installment Plan")
        self.setMinimumWidth(520)
        lay = QVBoxLayout(self)
        form = QFormLayout()

        self.customer = QComboBox()
        self.investor = QComboBox()
        self.investor.addItem("— None —", None)

        for c in list_customers(""):
            self.customer.addItem(f"{c['full_name']} (#{c['id']})", int(c["id"]))
        for i in list_investors(""):
            self.investor.addItem(f"{i['full_name']} (#{i['id']})", int(i["id"]))

        self.item = QLineEdit()
        self.total = QDoubleSpinBox(); self.total.setMaximum(1e12); self.total.setDecimals(2)
        self.advance = QDoubleSpinBox(); self.advance.setMaximum(1e12); self.advance.setDecimals(2)
        self.profit = QDoubleSpinBox(); self.profit.setMaximum(1000); self.profit.setDecimals(2)
        self.months = QSpinBox(); self.months.setRange(1, 600)
        self.start = QDateEdit(); self.start.setCalendarPopup(True); self.start.setDate(QDate.currentDate())

        self.ask_discount = QCheckBox("Apply discount after calculating final payable?")
        self.discount = QDoubleSpinBox(); self.discount.setMaximum(1e12); self.discount.setDecimals(2)
        self.discount.setEnabled(False)

        self.preview = QLabel("Final amount: — | Discount: — | Final payable: — | Monthly: —")
        self.preview.setStyleSheet("color:#94a3b8;")

        form.addRow("Customer*", self.customer)
        form.addRow("Item/Plan Name*", self.item)
        form.addRow("Total Price*", self.total)
        form.addRow("Advance Payment*", self.advance)
        form.addRow("Profit %*", self.profit)
        form.addRow("Months*", self.months)
        form.addRow("Start Date*", self.start)
        form.addRow("Investor (optional)", self.investor)
        form.addRow(self.ask_discount)
        form.addRow("Discount Amount", self.discount)
        lay.addLayout(form)
        lay.addWidget(self.preview)

        btns = QHBoxLayout()
        self.save = QPushButton("Create Plan")
        self.cancel = QPushButton("Cancel")
        self.cancel.setStyleSheet("background:#334155;")
        btns.addStretch(1)
        btns.addWidget(self.cancel)
        btns.addWidget(self.save)
        lay.addLayout(btns)

        self.cancel.clicked.connect(self.reject)
        self.save.clicked.connect(self.accept)
        self.ask_discount.toggled.connect(self._toggle_discount)

        for w in [self.total, self.advance, self.profit, self.months, self.discount]:
            w.valueChanged.connect(self._recalc)
        self.start.dateChanged.connect(lambda _: self._recalc())
        self._recalc()

    def _toggle_discount(self, on: bool):
        self.discount.setEnabled(on)
        if not on:
            self.discount.setValue(0.0)
        self._recalc()

    def _recalc(self):
        try:
            d = float(self.discount.value()) if self.ask_discount.isChecked() else 0.0
            amounts = compute_amounts(self.total.value(), self.advance.value(), self.profit.value(), d, self.months.value())
            monthly = amounts["monthly_amounts"][0] if amounts["monthly_amounts"] else 0
            self.preview.setText(
                f"Final amount: {amounts['final_amount']:.2f} | "
                f"Discount: {d:.2f} | Final payable: {amounts['final_payable']:.2f} | "
                f"Monthly (approx): {monthly:.2f}"
            )
        except Exception as e:
            self.preview.setText(f"Calculation error: {e}")

    def values(self) -> dict:
        discount = float(self.discount.value()) if self.ask_discount.isChecked() else 0.0
        return {
            "customer_id": self.customer.currentData(),
            "investor_id": self.investor.currentData(),
            "item_name": self.item.text().strip(),
            "total_price": float(self.total.value()),
            "advance_payment": float(self.advance.value()),
            "profit_pct": float(self.profit.value()),
            "months": int(self.months.value()),
            "start_date": self.start.date().toString("yyyy-MM-dd"),
            "discount": float(discount),
        }

class PlansPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)

        header = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search plans (customer, item, investor)...")
        self.btn_add = QPushButton("Create Plan")
        self.btn_view = QPushButton("View Installments")
        header.addWidget(self.search, 1)
        header.addWidget(self.btn_add)
        header.addWidget(self.btn_view)
        root.addLayout(header)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(["ID","Customer","Item","Investor","Total","Advance","Profit%","Discount","Final Payable"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, 1)

        self.search.textChanged.connect(self.refresh)
        self.btn_add.clicked.connect(self.add)
        self.btn_view.clicked.connect(self.view_installments)

        self.refresh()

    def refresh(self):
        rows = list_plans(self.search.text())
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            vals = [
                str(row["id"]),
                row["customer_name"],
                row["item_name"],
                row["investor_name"] or "—",
                f"{row['total_price']:.2f}",
                f"{row['advance_payment']:.2f}",
                f"{row['profit_pct']:.2f}",
                f"{row['discount']:.2f}",
                f"{row['final_payable']:.2f}",
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(r, c, it)

    def _selected_plan_id(self) -> int | None:
        sel = self.table.selectedItems()
        if not sel: return None
        return int(sel[0].text())

    def add(self):
        dlg = NewPlanDialog()
        if dlg.exec():
            v = dlg.values()
            if not v["customer_id"] or not v["item_name"]:
                QMessageBox.warning(self, "Validation", "Customer and Item name are required.")
                return
            try:
                create_plan(**v)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
            self.refresh()

    def view_installments(self):
        pid = self._selected_plan_id()
        if pid is None:
            QMessageBox.information(self, "Select", "Select a plan first.")
            return
        ins = installments_for_plan(pid)
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Installments for Plan #{pid}")
        dlg.setMinimumWidth(760)
        lay = QVBoxLayout(dlg)
        t = QTableWidget(0, 7)
        t.setHorizontalHeaderLabels(["Inst #","Due Date","Amount Due","Amount Paid","Paid?","Remarks","Installment ID"])
        t.verticalHeader().setVisible(False)
        t.setRowCount(len(ins))
        for r, row in enumerate(ins):
            vals = [
                str(row["inst_no"]),
                row["due_date"],
                f"{row['amount_due']:.2f}",
                f"{row['amount_paid']:.2f}",
                "Yes" if row["is_paid"] else "No",
                row["remarks"] or "",
                str(row["id"]),
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                t.setItem(r, c, it)
        lay.addWidget(t)
        dlg.exec()
