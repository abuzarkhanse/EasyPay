from __future__ import annotations
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt

class KpiCard(QFrame):
    def __init__(self, title: str, value: str, subtitle: str = ""):
        super().__init__()
        self.setStyleSheet("QFrame{background:#0b1220;border:1px solid #1f2937;border-radius:16px;}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        t = QLabel(title)
        t.setStyleSheet("color:#94a3b8;font-weight:700;")
        v = QLabel(value)
        v.setStyleSheet("font-size:22px;font-weight:900;")
        lay.addWidget(t)
        lay.addWidget(v)
        if subtitle:
            s = QLabel(subtitle)
            s.setStyleSheet("color:#94a3b8;")
            lay.addWidget(s)
        lay.addStretch(1)
