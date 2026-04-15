from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QMessageBox, QTableWidget,
    QTableWidgetItem, QDialog, QFormLayout,
    QDoubleSpinBox, QDateEdit, QTextEdit,
    QLabel, QGridLayout, QGroupBox, QSplitter
)
from PySide6.QtCore import Qt, QDate

from ...services.payments import (
    add_payment,
    edit_payment,
    is_plan_completed,
    fetch_payment,
    list_payment_customers,
    customer_payment_summary,
    installments_for_customer,
)
from ...services.receipts import generate_receipt_pdf


# ==========================================================
# PAYMENT DIALOG
# ==========================================================
class PaymentDialog(QDialog):
    def __init__(
        self,
        title: str,
        default_amount: float,
        default_date: str | None = None,
        default_remarks: str = ""
    ):
        super().__init__()

        self.setWindowTitle(title)
        self.setMinimumWidth(420)

        lay = QVBoxLayout(self)
        form = QFormLayout()

        self.amount = QDoubleSpinBox()
        self.amount.setMaximum(1e12)
        self.amount.setDecimals(2)
        self.amount.setValue(default_amount)

        self.date = QDateEdit()
        self.date.setCalendarPopup(True)

        if default_date:
            y, m, d = map(int, default_date.split("-"))
            self.date.setDate(QDate(y, m, d))
        else:
            self.date.setDate(QDate.currentDate())

        self.remarks = QTextEdit()
        self.remarks.setFixedHeight(80)
        self.remarks.setPlainText(default_remarks)

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

    def values(self):
        return {
            "amount": float(self.amount.value()),
            "actual_payment_date": self.date.date().toString("yyyy-MM-dd"),
            "remarks": self.remarks.toPlainText().strip(),
        }


# ==========================================================
# PAYMENTS PAGE
# ==========================================================
class PaymentsPage(QWidget):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        # ---------------- SEARCH ----------------
        header = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search customer by name, phone or CNIC...")
        header.addWidget(self.search)
        root.addLayout(header)

        # ---------------- MAIN SPLITTER ----------------
        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, 1)

        # ======================================================
        # LEFT SIDE: CUSTOMER LIST
        # ======================================================
        left_box = QGroupBox("Customers")
        left_layout = QVBoxLayout(left_box)

        self.customer_table = QTableWidget(0, 6)
        self.customer_table.setHorizontalHeaderLabels([
            "Customer",
            "Phone",
            "Plans",
            "Remaining Amount",
            "Remaining Inst.",
            "Customer ID",
        ])
        self.customer_table.verticalHeader().setVisible(False)
        self.customer_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.customer_table.setAlternatingRowColors(True)
        self.customer_table.setColumnHidden(5, True)

        left_layout.addWidget(self.customer_table)
        splitter.addWidget(left_box)

        # ======================================================
        # RIGHT SIDE: SUMMARY + INSTALLMENTS
        # ======================================================
        right_box = QWidget()
        right_layout = QVBoxLayout(right_box)
        right_layout.setSpacing(12)

        self.customer_title = QLabel("Select a customer")
        self.customer_title.setStyleSheet("font-size:16px; font-weight:700;")
        right_layout.addWidget(self.customer_title)

        # ---------------- SUMMARY ----------------
        summary_box = QGroupBox("Customer Payment Summary")
        summary_grid = QGridLayout(summary_box)

        self.lbl_total_plans = QLabel("0")
        self.lbl_total_installments = QLabel("0")
        self.lbl_paid_installments = QLabel("0")
        self.lbl_unpaid_installments = QLabel("0")
        self.lbl_total_payable = QLabel("0.00")
        self.lbl_total_paid = QLabel("0.00")
        self.lbl_remaining_amount = QLabel("0.00")

        summary_grid.addWidget(QLabel("Total Plans"), 0, 0)
        summary_grid.addWidget(self.lbl_total_plans, 0, 1)

        summary_grid.addWidget(QLabel("Total Installments"), 0, 2)
        summary_grid.addWidget(self.lbl_total_installments, 0, 3)

        summary_grid.addWidget(QLabel("Paid Installments"), 1, 0)
        summary_grid.addWidget(self.lbl_paid_installments, 1, 1)

        summary_grid.addWidget(QLabel("Unpaid Installments"), 1, 2)
        summary_grid.addWidget(self.lbl_unpaid_installments, 1, 3)

        summary_grid.addWidget(QLabel("Total Payable"), 2, 0)
        summary_grid.addWidget(self.lbl_total_payable, 2, 1)

        summary_grid.addWidget(QLabel("Total Paid"), 2, 2)
        summary_grid.addWidget(self.lbl_total_paid, 2, 3)

        summary_grid.addWidget(QLabel("Remaining Amount"), 3, 0)
        summary_grid.addWidget(self.lbl_remaining_amount, 3, 1)

        right_layout.addWidget(summary_box)

        # ---------------- BUTTONS ----------------
        btn_row = QHBoxLayout()
        self.btn_pay = QPushButton("Add Payment")
        self.btn_edit = QPushButton("Edit Last Payment")
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_pay)
        btn_row.addWidget(self.btn_edit)
        right_layout.addLayout(btn_row)

        # ---------------- INSTALLMENTS TABLE ----------------
        installments_box = QGroupBox("Customer Installments")
        installments_layout = QVBoxLayout(installments_box)

        self.table = QTableWidget(0, 12)
        self.table.setHorizontalHeaderLabels([
            "Installment ID",
            "Plan No",
            "Item",
            "Inst #",
            "Due Date",
            "Amount Due",
            "Amount Paid",
            "Remaining",
            "Status",
            "Last Payment Date",
            "Plan ID",
            "Last Payment ID",
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)

        # Hide technical columns
        self.table.setColumnHidden(0, True)   # Installment ID
        self.table.setColumnHidden(10, True)  # Plan ID
        self.table.setColumnHidden(11, True)  # Last Payment ID

        installments_layout.addWidget(self.table)
        right_layout.addWidget(installments_box, 1)

        splitter.addWidget(right_box)
        splitter.setSizes([320, 900])

        # ---------------- CONNECTIONS ----------------
        self.search.textChanged.connect(self.refresh_customers)
        self.customer_table.itemSelectionChanged.connect(self._on_customer_changed)
        self.btn_pay.clicked.connect(self.pay)
        self.btn_edit.clicked.connect(self.edit_last_payment)

        self.refresh_customers()

    # ======================================================
    def money(self, value: float) -> str:
        return f"{float(value):,.2f}"

    # ======================================================
    def _selected_customer_id(self):
        row = self.customer_table.currentRow()
        if row < 0:
            return None

        item = self.customer_table.item(row, 5)
        if not item:
            return None

        try:
            return int(item.text())
        except Exception:
            return None

    # ======================================================
    def _selected_installment_data(self):
        row = self.table.currentRow()
        if row < 0:
            return None

        try:
            return {
                "installment_id": int(self.table.item(row, 0).text()),
                "plan_number": self.table.item(row, 1).text(),
                "item_name": self.table.item(row, 2).text(),
                "inst_no": self.table.item(row, 3).text(),
                "due_date": self.table.item(row, 4).text(),
                "amount_due": float(self.table.item(row, 5).text()),
                "amount_paid": float(self.table.item(row, 6).text()),
                "remaining": float(self.table.item(row, 7).text()),
                "status": self.table.item(row, 8).text(),
                "last_payment_date": self.table.item(row, 9).text(),
                "plan_id": int(self.table.item(row, 10).text()),
                "last_payment_id": self.table.item(row, 11).text().strip(),
            }
        except Exception:
            return None

    # ======================================================
    def refresh_customers(self):
        current_customer = self._selected_customer_id()
        rows = list_payment_customers(self.search.text())

        self.customer_table.setRowCount(len(rows))

        row_to_select = 0

        for r, row in enumerate(rows):
            vals = [
                row["full_name"],
                row.get("phone") or "",
                str(row.get("total_plans", 0)),
                self.money(row.get("remaining_amount", 0)),
                str(row.get("unpaid_installments", 0)),
                str(row["customer_id"]),
            ]

            if current_customer is not None and int(row["customer_id"]) == current_customer:
                row_to_select = r

            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.customer_table.setItem(r, c, item)

        self.customer_table.resizeColumnsToContents()

        if rows:
            self.customer_table.selectRow(row_to_select)
            self._load_customer_details(int(rows[row_to_select]["customer_id"]))
        else:
            self._clear_details()

    # ======================================================
    def _on_customer_changed(self):
        customer_id = self._selected_customer_id()
        if customer_id is None:
            self._clear_details()
            return

        self._load_customer_details(customer_id)

    # ======================================================
    def _clear_details(self):
        self.customer_title.setText("Select a customer")

        self.lbl_total_plans.setText("0")
        self.lbl_total_installments.setText("0")
        self.lbl_paid_installments.setText("0")
        self.lbl_unpaid_installments.setText("0")
        self.lbl_total_payable.setText("0.00")
        self.lbl_total_paid.setText("0.00")
        self.lbl_remaining_amount.setText("0.00")

        self.table.setRowCount(0)

    # ======================================================
    def _load_customer_details(self, customer_id: int):
        summary = customer_payment_summary(customer_id)
        if not summary:
            self._clear_details()
            return

        self.customer_title.setText(
            f"{summary['full_name']}  |  Phone: {summary.get('phone') or '-'}"
        )

        self.lbl_total_plans.setText(str(summary.get("total_plans", 0)))
        self.lbl_total_installments.setText(str(summary.get("total_installments", 0)))
        self.lbl_paid_installments.setText(str(summary.get("paid_installments", 0)))
        self.lbl_unpaid_installments.setText(str(summary.get("unpaid_installments", 0)))
        self.lbl_total_payable.setText(self.money(summary.get("total_final_payable", 0)))
        self.lbl_total_paid.setText(self.money(summary.get("total_paid", 0)))
        self.lbl_remaining_amount.setText(self.money(summary.get("remaining_amount", 0)))

        rows = installments_for_customer(customer_id)
        self.table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            status = "Paid" if row["is_paid"] else "Unpaid"

            vals = [
                str(row["installment_id"]),
                row.get("plan_number") or f"PLAN-{row['plan_id']}",
                row["item_name"],
                str(row["inst_no"]),
                row["due_date"],
                f"{float(row['amount_due']):.2f}",
                f"{float(row['amount_paid']):.2f}",
                f"{float(row['remaining_amount']):.2f}",
                status,
                row.get("last_payment_date") or "",
                str(row["plan_id"]),
                str(row.get("last_payment_id") or ""),
            ]

            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(r, c, item)

        self.table.resizeColumnsToContents()

    # ======================================================
    def _show_payment_success_message(self, pdf: str, plan_id: int):
        message = f"Receipt saved:\n{pdf}"

        try:
            if is_plan_completed(plan_id):
                message += (
                    "\n\nPlan fully completed."
                    "\nFinal completion receipt is now available in Receipts page."
                )
        except Exception:
            pass

        QMessageBox.information(self, "Receipt Generated", message)

    # ======================================================
    def pay(self):
        selected = self._selected_installment_data()
        if not selected:
            QMessageBox.information(self, "Select", "Select an installment first.")
            return

        remaining = max(selected["remaining"], 0.0)

        dlg = PaymentDialog("Add Payment", default_amount=remaining)

        if dlg.exec():
            v = dlg.values()
            try:
                payment_id = add_payment(
                    selected["installment_id"],
                    v["amount"],
                    v["actual_payment_date"],
                    v["remarks"]
                )

                pdf = generate_receipt_pdf(payment_id, company_name="EasyPay")

                customer_id = self._selected_customer_id()
                self.refresh_customers()
                if customer_id is not None:
                    self._load_customer_details(customer_id)

                self._show_payment_success_message(pdf, selected["plan_id"])

            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    # ======================================================
    def edit_last_payment(self):
        selected = self._selected_installment_data()
        if not selected:
            QMessageBox.information(self, "Select", "Select an installment first.")
            return

        if not selected["last_payment_id"]:
            QMessageBox.information(self, "No payment", "No payment exists for this installment.")
            return

        payment_id = int(selected["last_payment_id"])
        pay = fetch_payment(payment_id)

        if not pay:
            QMessageBox.warning(self, "Error", "Payment not found.")
            return

        dlg = PaymentDialog(
            "Edit Last Payment",
            default_amount=float(pay["amount"]),
            default_date=pay["actual_payment_date"],
            default_remarks=pay["remarks"] or ""
        )

        if dlg.exec():
            v = dlg.values()
            try:
                edit_payment(
                    payment_id,
                    v["amount"],
                    v["actual_payment_date"],
                    v["remarks"]
                )

                pdf = generate_receipt_pdf(payment_id, company_name="EasyPay")

                customer_id = self._selected_customer_id()
                self.refresh_customers()
                if customer_id is not None:
                    self._load_customer_details(customer_id)

                message = f"Updated receipt saved:\n{pdf}"
                try:
                    if is_plan_completed(selected["plan_id"]):
                        message += (
                            "\n\nPlan fully completed."
                            "\nFinal completion receipt is now available in Receipts page."
                        )
                except Exception:
                    pass

                QMessageBox.information(self, "Receipt Updated", message)

            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                