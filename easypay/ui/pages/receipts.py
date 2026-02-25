from __future__ import annotations
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from ...services.receipts import list_receipts

class ReceiptsPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)

        header = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search receipts (receipt no, customer, item)...")
        self.btn_open = QPushButton("Open PDF")
        header.addWidget(self.search, 1)
        header.addWidget(self.btn_open)
        root.addLayout(header)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Receipt No","Customer","Item","PDF Path","Created At","Receipt ID"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, 1)

        self.search.textChanged.connect(self.refresh)
        self.btn_open.clicked.connect(self.open_pdf)

        self.refresh()

    def refresh(self):
        rows = list_receipts(self.search.text())
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            vals = [
                row["receipt_no"],
                row["customer_name"],
                row["item_name"],
                row["pdf_path"],
                row["created_at"],
                str(row["id"]),
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(r, c, it)

    def open_pdf(self):
        sel = self.table.selectedItems()
        if not sel:
            QMessageBox.information(self, "Select", "Select a receipt row first.")
            return
        path = self.table.item(self.table.currentRow(), 3).text()
        if not os.path.exists(path):
            QMessageBox.warning(self, "Missing", f"File not found:\n{path}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
