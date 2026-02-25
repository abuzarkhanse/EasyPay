from __future__ import annotations

APP_QSS = """
QMainWindow { background-color: #0f172a; }

QWidget {
    background-color: #0f172a;
    color: #e5e7eb;
    font-family: Segoe UI;
    font-size: 12px;
}

QLabel {
    color: #e5e7eb;
}

QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    background-color: #111827;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px;
    color: #e5e7eb;
}

QPushButton {
    background-color: #2563eb;
    border-radius: 8px;
    padding: 8px;
    color: white;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #1d4ed8;
}

QTableWidget {
    background-color: #111827;
    border: 1px solid #334155;
    alternate-background-color: #1f2937;
    color: #e5e7eb;
}

QHeaderView::section {
    background-color: #1f2937;
    color: #e5e7eb;
    padding: 6px;
    font-weight: bold;
}
"""