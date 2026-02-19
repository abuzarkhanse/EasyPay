from __future__ import annotations

APP_QSS = """
QMainWindow { background: #0f172a; }
QWidget { color: #e5e7eb; font-family: Segoe UI; font-size: 12px; }
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    background: #111827; border: 1px solid #334155; border-radius: 10px;
    padding: 8px;
}
QPushButton {
    background: #2563eb; border: 0px; border-radius: 10px;
    padding: 10px 12px; font-weight: 600;
}
QPushButton:hover { background: #1d4ed8; }
QPushButton:disabled { background: #475569; }

QTableWidget {
    background: #0b1220; border: 1px solid #334155; border-radius: 12px;
    gridline-color: #1f2937;
}
QHeaderView::section {
    background: #111827; border: 0px; padding: 8px; font-weight: 700;
}
QTableWidget::item { padding: 6px; }
QFrame#Sidebar { background: #0b1220; border-right: 1px solid #1f2937; }
QLabel#Title { font-size: 18px; font-weight: 800; }
QLabel#Subtitle { color: #94a3b8; }
QPushButton#NavBtn {
    background: transparent; text-align: left; padding: 10px 12px;
    border-radius: 12px; font-weight: 600;
}
QPushButton#NavBtn:hover { background: #111827; }
QPushButton#NavBtn:checked { background: #1f2937; }
"""
