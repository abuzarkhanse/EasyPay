from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QDialog, QFormLayout, QComboBox,
    QDoubleSpinBox, QSpinBox, QDateEdit, QLabel,
    QCheckBox
)
from PySide6.QtCore import Qt, QDate

from ...services.parties import list_customers, list_investors
from ...services.plans import (
    create_plan,
    list_plans,
    installments_for_plan,
    delete_plan,
    calculate_plan_values,
)


# ==========================================================
# NEW PLAN DIALOG
# ==========================================================
class NewPlanDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Create Installment Plan")
        self.setMinimumWidth(600)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.customer = QComboBox()
        self.investor = QComboBox()
        self.investor.addItem("— None —", None)

        for c in list_customers(""):
            self.customer.addItem(f"{c['full_name']} (#{c['id']})", int(c["id"]))

        for i in list_investors(""):
            self.investor.addItem(f"{i['full_name']} (#{i['id']})", int(i["id"]))

        self.item = QLineEdit()

        self.total = QDoubleSpinBox()
        self.total.setMaximum(1e12)
        self.total.setDecimals(2)

        self.advance = QDoubleSpinBox()
        self.advance.setMaximum(1e12)
        self.advance.setDecimals(2)

        self.profit = QDoubleSpinBox()
        self.profit.setMaximum(1000)
        self.profit.setDecimals(2)

        self.months = QSpinBox()
        self.months.setRange(1, 600)
        self.months.setValue(12)

        self.start = QDateEdit()
        self.start.setCalendarPopup(True)
        self.start.setDate(QDate.currentDate())

        self.use_discount = QCheckBox("Apply Discount")

        self.discount_mode = QComboBox()
        self.discount_mode.addItem("Discount on Final Payment", "final")
        self.discount_mode.addItem("Discount on Principal", "principal")
        self.discount_mode.setEnabled(False)

        self.discount = QDoubleSpinBox()
        self.discount.setMaximum(1e12)
        self.discount.setDecimals(2)
        self.discount.setEnabled(False)

        self.preview = QLabel()
        self.preview.setWordWrap(True)
        self.preview.setStyleSheet("color:#94a3b8; padding:8px;")

        form.addRow("Customer*", self.customer)
        form.addRow("Item/Plan Name*", self.item)
        form.addRow("Total Price*", self.total)
        form.addRow("Advance Payment*", self.advance)
        form.addRow("Profit %*", self.profit)
        form.addRow("Months*", self.months)
        form.addRow("Start Date*", self.start)
        form.addRow("Investor (optional)", self.investor)
        form.addRow(self.use_discount)
        form.addRow("Discount Type", self.discount_mode)
        form.addRow("Discount", self.discount)

        layout.addLayout(form)
        layout.addWidget(self.preview)

        buttons = QHBoxLayout()
        self.save = QPushButton("Create Plan")
        self.cancel = QPushButton("Cancel")
        buttons.addStretch()
        buttons.addWidget(self.cancel)
        buttons.addWidget(self.save)

        layout.addLayout(buttons)

        self.cancel.clicked.connect(self.reject)
        self.save.clicked.connect(self._validate_and_accept)
        self.use_discount.toggled.connect(self._toggle_discount)

        for w in [self.total, self.advance, self.profit, self.months, self.discount]:
            w.valueChanged.connect(self._recalculate)

        self.discount_mode.currentIndexChanged.connect(self._recalculate)

        self._recalculate()

    def _toggle_discount(self, checked: bool):
        self.discount.setEnabled(checked)
        self.discount_mode.setEnabled(checked)

        if not checked:
            self.discount.setValue(0.0)

        self._recalculate()

    def _recalculate(self):
        total = self.total.value()
        advance = self.advance.value()
        profit_pct = self.profit.value()
        months = self.months.value()
        discount = self.discount.value() if self.use_discount.isChecked() else 0.0
        discount_mode = self.discount_mode.currentData() if self.use_discount.isChecked() else "final"

        calc = calculate_plan_values(
            total_price=total,
            advance_payment=advance,
            profit_percent=profit_pct,
            months=months,
            discount=discount,
            discount_mode=discount_mode,
        )

        mode_text = "Final Payment" if calc["discount_mode"] == "final" else "Principal"

        preview_lines = [
            "<b>Calculation Preview</b><br><br>",
        ]

        if calc["discount_mode"] == "principal":
            preview_lines.append(f"Adjusted Principal After Discount: {calc['adjusted_total_price']:.2f}<br>")

        preview_lines.extend([
            f"Remaining: {calc['remaining']:.2f}<br>",
            f"Profit: {calc['profit']:.2f}<br>",
            f"Final Before Discount: {calc['final_before_discount']:.2f}<br>",
            f"Discount: {calc['discount']:.2f}<br>",
            f"Discount Mode: {mode_text}<br><br>",
            f"<b>Final Payable: {calc['final_payable']:.2f}</b><br>",
            f"Monthly Payment: {calc['monthly_payment']:.2f}",
        ])

        self.preview.setText("".join(preview_lines))

    def _validate_and_accept(self):
        if self.customer.currentData() is None:
            QMessageBox.warning(self, "Missing Customer", "Please select a customer.")
            return

        if not self.item.text().strip():
            QMessageBox.warning(self, "Missing Item", "Please enter item or plan name.")
            return

        if self.total.value() <= 0:
            QMessageBox.warning(self, "Invalid Total", "Total price must be greater than 0.")
            return

        if self.advance.value() < 0:
            QMessageBox.warning(self, "Invalid Advance", "Advance payment cannot be negative.")
            return

        if self.months.value() <= 0:
            QMessageBox.warning(self, "Invalid Months", "Months must be at least 1.")
            return

        self.accept()

    def values(self):
        use_discount = self.use_discount.isChecked()

        return {
            "customer_id": self.customer.currentData(),
            "investor_id": self.investor.currentData(),
            "item_name": self.item.text().strip(),
            "total_price": float(self.total.value()),
            "advance_payment": float(self.advance.value()),
            "profit_pct": float(self.profit.value()),
            "months": int(self.months.value()),
            "start_date": self.start.date().toString("yyyy-MM-dd"),
            "discount": float(self.discount.value()) if use_discount else 0.0,
            "discount_mode": self.discount_mode.currentData() if use_discount else "final",
        }


# ==========================================================
# PLANS PAGE
# ==========================================================
class PlansPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)

        header = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search plans...")

        self.btn_add = QPushButton("Create Plan")
        self.btn_delete = QPushButton("Delete Selected")
        self.btn_delete.setStyleSheet("background:#ef4444; color:white; font-weight:bold;")

        header.addWidget(self.search, 1)
        header.addWidget(self.btn_add)
        header.addWidget(self.btn_delete)

        layout.addLayout(header)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            "Select", "ID", "Customer", "Item", "Investor",
            "Total", "Advance", "Profit%", "Discount", "Final Payable"
        ])
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.search.textChanged.connect(self.refresh)
        self.btn_add.clicked.connect(self.add_plan)
        self.btn_delete.clicked.connect(self.delete_selected)

        self.refresh()

    def refresh(self):
        rows = list_plans(self.search.text())
        self.table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Unchecked)
            self.table.setItem(r, 0, chk)

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

            for c, v in enumerate(vals, start=1):
                item = QTableWidgetItem(v)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(r, c, item)

    def add_plan(self):
        dlg = NewPlanDialog()
        if dlg.exec():
            try:
                create_plan(**dlg.values())
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def delete_selected(self):
        selected_ids = []

        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                plan_id = int(self.table.item(row, 1).text())
                selected_ids.append(plan_id)

        if not selected_ids:
            QMessageBox.warning(self, "Select Plans", "Please tick at least one plan.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete {len(selected_ids)} selected plan(s)?\n"
            f"This will permanently delete all related data.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                for pid in selected_ids:
                    delete_plan(pid)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Delete Failed", str(e))
                