from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QDialog, QLabel, QTextEdit, QFormLayout
from PySide6.QtCore import Qt

from ...services.parties import (
    list_customers, add_customer, update_customer, delete_customer,
    list_investors, add_investor, update_investor, delete_investor
)

class PartyDialog(QDialog):
    def __init__(self, title: str, data: dict | None = None):
        super().__init__()
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit()
        self.cnic = QLineEdit()
        self.phone = QLineEdit()
        self.addr = QTextEdit()
        self.addr.setFixedHeight(80)
        form.addRow("Full Name*", self.name)
        form.addRow("CNIC / ID*", self.cnic)
        form.addRow("Phone*", self.phone)
        form.addRow("Address*", self.addr)
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

        if data:
            self.name.setText(data.get("full_name",""))
            self.cnic.setText(data.get("cnic",""))
            self.phone.setText(data.get("phone",""))
            self.addr.setPlainText(data.get("address",""))

    def values(self) -> dict:
        return {
            "full_name": self.name.text().strip(),
            "cnic": self.cnic.text().strip(),
            "phone": self.phone.text().strip(),
            "address": self.addr.toPlainText().strip(),
        }

def _set_row(table: QTableWidget, row: int, values: list[str]):
    for col, v in enumerate(values):
        it = QTableWidgetItem(v)
        it.setFlags(it.flags() ^ Qt.ItemIsEditable)
        table.setItem(row, col, it)

class CustomersPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)

        header = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search customers (name, CNIC, phone)...")
        self.btn_add = QPushButton("Add Customer")
        header.addWidget(self.search, 1)
        header.addWidget(self.btn_add)
        root.addLayout(header)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Full Name", "CNIC", "Phone", "Address"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, 1)

        footer = QHBoxLayout()
        self.btn_edit = QPushButton("Edit")
        self.btn_del = QPushButton("Delete")
        self.btn_del.setStyleSheet("background:#dc2626;")
        footer.addStretch(1)
        footer.addWidget(self.btn_edit)
        footer.addWidget(self.btn_del)
        root.addLayout(footer)

        self.search.textChanged.connect(self.refresh)
        self.btn_add.clicked.connect(self.add)
        self.btn_edit.clicked.connect(self.edit)
        self.btn_del.clicked.connect(self.remove)

        self.refresh()

    def refresh(self):
        rows = list_customers(self.search.text())
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            _set_row(self.table, r, [str(row["id"]), row["full_name"], row["cnic"], row["phone"], row["address"]])

    def _selected_id(self) -> int | None:
        sel = self.table.selectedItems()
        if not sel: return None
        return int(sel[0].text())

    def add(self):
        dlg = PartyDialog("Add Customer")
        if dlg.exec():
            v = dlg.values()
            if not all(v.values()):
                QMessageBox.warning(self, "Validation", "All fields are required.")
                return
            add_customer(**v)
            self.refresh()

    def edit(self):
        cid = self._selected_id()
        if cid is None:
            QMessageBox.information(self, "Select", "Select a customer row first.")
            return
        # read current row values from table
        r = self.table.currentRow()
        data = {
            "full_name": self.table.item(r,1).text(),
            "cnic": self.table.item(r,2).text(),
            "phone": self.table.item(r,3).text(),
            "address": self.table.item(r,4).text(),
        }
        dlg = PartyDialog("Edit Customer", data)
        if dlg.exec():
            v = dlg.values()
            if not all(v.values()):
                QMessageBox.warning(self, "Validation", "All fields are required.")
                return
            update_customer(cid, **v)
            self.refresh()

    def remove(self):
        cid = self._selected_id()
        if cid is None:
            QMessageBox.information(self, "Select", "Select a customer row first.")
            return
        if QMessageBox.question(self, "Confirm", "Delete selected customer? (Plans linked to customer cannot be deleted)") == QMessageBox.Yes:
            try:
                delete_customer(cid)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
            self.refresh()

class InvestorsPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)

        header = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search investors (name, CNIC, phone)...")
        self.btn_add = QPushButton("Add Investor")
        header.addWidget(self.search, 1)
        header.addWidget(self.btn_add)
        root.addLayout(header)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Full Name", "CNIC", "Phone", "Address"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, 1)

        footer = QHBoxLayout()
        self.btn_edit = QPushButton("Edit")
        self.btn_del = QPushButton("Delete")
        self.btn_del.setStyleSheet("background:#dc2626;")
        footer.addStretch(1)
        footer.addWidget(self.btn_edit)
        footer.addWidget(self.btn_del)
        root.addLayout(footer)

        self.search.textChanged.connect(self.refresh)
        self.btn_add.clicked.connect(self.add)
        self.btn_edit.clicked.connect(self.edit)
        self.btn_del.clicked.connect(self.remove)

        self.refresh()

    def refresh(self):
        rows = list_investors(self.search.text())
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            _set_row(self.table, r, [str(row["id"]), row["full_name"], row["cnic"], row["phone"], row["address"]])

    def _selected_id(self) -> int | None:
        sel = self.table.selectedItems()
        if not sel: return None
        return int(sel[0].text())

    def add(self):
        dlg = PartyDialog("Add Investor")
        if dlg.exec():
            v = dlg.values()
            if not all(v.values()):
                QMessageBox.warning(self, "Validation", "All fields are required.")
                return
            add_investor(**v)
            self.refresh()

    def edit(self):
        iid = self._selected_id()
        if iid is None:
            QMessageBox.information(self, "Select", "Select an investor row first.")
            return
        r = self.table.currentRow()
        data = {
            "full_name": self.table.item(r,1).text(),
            "cnic": self.table.item(r,2).text(),
            "phone": self.table.item(r,3).text(),
            "address": self.table.item(r,4).text(),
        }
        dlg = PartyDialog("Edit Investor", data)
        if dlg.exec():
            v = dlg.values()
            if not all(v.values()):
                QMessageBox.warning(self, "Validation", "All fields are required.")
                return
            update_investor(iid, **v)
            self.refresh()

    def remove(self):
        iid = self._selected_id()
        if iid is None:
            QMessageBox.information(self, "Select", "Select an investor row first.")
            return
        if QMessageBox.question(self, "Confirm", "Delete selected investor?") == QMessageBox.Yes:
            try:
                delete_investor(iid)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
            self.refresh()
