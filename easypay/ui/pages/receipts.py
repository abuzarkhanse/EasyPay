from __future__ import annotations

import os
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

from ...services.receipts import (
    list_receipts,
    completed_plans_for_receipts,
    generate_receipt_pdf,
    generate_final_completion_receipt,
)


class ReceiptsPage(QWidget):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)

        header = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search receipts by customer, item, receipt no, or plan no...")

        self.btn_generate = QPushButton("Generate PDF")
        self.btn_generate.setStyleSheet("background:#0f766e; color:white;")

        self.btn_open = QPushButton("Open PDF")

        header.addWidget(self.search, 1)
        header.addWidget(self.btn_generate)
        header.addWidget(self.btn_open)
        root.addLayout(header)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Receipt Type",
            "Receipt No / Plan No",
            "Customer",
            "Item",
            "Amount",
            "Date",
            "PDF Status",
            "Hidden ID",
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, 1)

        # hide internal ID column from user
        self.table.setColumnHidden(7, True)

        self.search.textChanged.connect(self.refresh)
        self.btn_open.clicked.connect(self.open_pdf)
        self.btn_generate.clicked.connect(self.generate_missing_pdf)
        self.table.doubleClicked.connect(lambda *_: self.open_pdf())

        self.refresh()

    def _parse_date(self, value: str):
        value = (value or "").strip()
        if not value:
            return datetime.min
        try:
            return datetime.fromisoformat(value)
        except Exception:
            try:
                return datetime.strptime(value, "%Y-%m-%d")
            except Exception:
                return datetime.min

    def refresh(self):
        search_text = self.search.text().strip()

        normal_receipts = list_receipts(search_text)
        final_receipts = completed_plans_for_receipts(search_text)

        all_rows = []

        for row in normal_receipts:
            pdf_path = str(row.get("pdf_path", ""))
            all_rows.append({
                "receipt_type": row.get("receipt_type", "Installment"),
                "display_no": str(row.get("receipt_no", "")),
                "customer_name": str(row.get("customer_name", "")),
                "item_name": str(row.get("item_name", "")),
                "amount": f"{float(row.get('amount', 0) or 0):,.2f}",
                "date": str(row.get("actual_payment_date") or row.get("created_at") or ""),
                "pdf_status": "Ready" if os.path.exists(pdf_path) else "Missing",
                "pdf_path": pdf_path,
                "internal_id": str(row.get("id", "")),
            })

        for row in final_receipts:
            pdf_path = str(row.get("pdf_path", ""))
            all_rows.append({
                "receipt_type": row.get("receipt_type", "Final Completion"),
                "display_no": str(row.get("plan_number") or f"PLAN-{row.get('plan_id')}"),
                "customer_name": str(row.get("customer_name", "")),
                "item_name": str(row.get("item_name", "")),
                "amount": f"{float(row.get('final_payable', 0) or 0):,.2f}",
                "date": str(row.get("completion_date") or ""),
                "pdf_status": "Ready" if os.path.exists(pdf_path) else "Missing",
                "pdf_path": pdf_path,
                "internal_id": f"PLAN:{row.get('plan_id', '')}",
            })

        all_rows.sort(key=lambda x: self._parse_date(x["date"]), reverse=True)

        self.table.setRowCount(len(all_rows))

        for r, row in enumerate(all_rows):
            vals = [
                row["receipt_type"],
                row["display_no"],
                row["customer_name"],
                row["item_name"],
                row["amount"],
                row["date"],
                row["pdf_status"],
                row["internal_id"],
            ]

            for c, v in enumerate(vals):
                it = QTableWidgetItem(str(v))
                it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(r, c, it)

        self.table.resizeColumnsToContents()

    def _selected_row_data(self):
        row_index = self.table.currentRow()
        if row_index < 0:
            return None

        internal_id = self.table.item(row_index, 7).text()
        receipt_type = self.table.item(row_index, 0).text()

        search_text = self.search.text().strip()
        normal_receipts = list_receipts(search_text)
        final_receipts = completed_plans_for_receipts(search_text)

        if receipt_type == "Installment":
            for row in normal_receipts:
                if str(row.get("id", "")) == internal_id:
                    return {
                        "receipt_type": "Installment",
                        "pdf_path": str(row.get("pdf_path", "")),
                        "internal_id": internal_id,
                    }

        elif receipt_type == "Final Completion":
            for row in final_receipts:
                expected = f"PLAN:{row.get('plan_id', '')}"
                if expected == internal_id:
                    return {
                        "receipt_type": "Final Completion",
                        "pdf_path": str(row.get("pdf_path", "")),
                        "internal_id": internal_id,
                    }

        return None

    def generate_missing_pdf(self):
        selected = self._selected_row_data()
        if not selected:
            QMessageBox.information(self, "Select", "Select a receipt row first.")
            return

        try:
            receipt_type = selected["receipt_type"]
            internal_id = selected["internal_id"]

            if receipt_type == "Installment":
                payment_id = int(internal_id)
                path = generate_receipt_pdf(payment_id)

            elif receipt_type == "Final Completion":
                if not internal_id.startswith("PLAN:"):
                    raise ValueError("Invalid final receipt plan ID.")
                plan_id = int(internal_id.split(":", 1)[1])
                path = generate_final_completion_receipt(plan_id)

            else:
                raise ValueError("Unknown receipt type.")

            self.refresh()

            QMessageBox.information(
                self,
                "PDF Generated",
                f"Receipt PDF generated successfully:\n\n{path}",
            )

        except Exception as e:
            QMessageBox.critical(self, "Generate Failed", str(e))

    def open_pdf(self):
        selected = self._selected_row_data()
        if not selected:
            QMessageBox.information(self, "Select", "Select a receipt row first.")
            return

        path = selected["pdf_path"]

        if not os.path.exists(path):
            ask = QMessageBox.question(
                self,
                "PDF Not Found",
                "This receipt PDF does not exist yet.\n\nDo you want to generate it now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )

            if ask == QMessageBox.Yes:
                self.generate_missing_pdf()
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        