from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame
from PySide6.QtCore import Qt

from ..widgets import KpiCard
from ...services.analytics import dashboard_kpis, monthly_collections

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        title = QLabel("Dashboard")
        title.setObjectName("Title")
        subtitle = QLabel("Overview of customers, plans and collections")
        subtitle.setObjectName("Subtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        root.addLayout(grid)

        self.cards = {}
        keys = [
            ("Total Customers", "total_customers"),
            ("Total Investors", "total_investors"),
            ("Active Plans", "active_plans"),
            ("Outstanding Balance", "outstanding"),
            ("Total Discounts", "total_discounts"),
            ("Overdue Installments", "overdue_count"),
            ("Upcoming Installments", "upcoming_count"),
        ]
        for idx, (label, key) in enumerate(keys):
            card = KpiCard(label, "—")
            self.cards[key] = card
            grid.addWidget(card, idx // 3, idx % 3)

        chart_frame = QFrame()
        chart_frame.setStyleSheet("QFrame{background:#0b1220;border:1px solid #1f2937;border-radius:16px;}")
        cf = QVBoxLayout(chart_frame)
        cf.setContentsMargins(14, 12, 14, 12)
        cf.addWidget(QLabel("Monthly Collections (by payment date)"))

        self.fig = Figure(figsize=(6, 2.5), tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        cf.addWidget(self.canvas)
        root.addWidget(chart_frame)

        self.refresh()

    def refresh(self):
        k = dashboard_kpis()
        self.cards["total_customers"].layout().itemAt(1).widget().setText(str(k["total_customers"]))
        self.cards["total_investors"].layout().itemAt(1).widget().setText(str(k["total_investors"]))
        self.cards["active_plans"].layout().itemAt(1).widget().setText(str(k["active_plans"]))
        self.cards["outstanding"].layout().itemAt(1).widget().setText(f"{k['outstanding']:.2f}")
        self.cards["total_discounts"].layout().itemAt(1).widget().setText(f"{k['total_discounts']:.2f}")
        self.cards["overdue_count"].layout().itemAt(1).widget().setText(str(k["overdue_count"]))
        self.cards["upcoming_count"].layout().itemAt(1).widget().setText(str(k["upcoming_count"]))

        data = monthly_collections(12)
        self.ax.clear()
        if data:
            xs = [d[0] for d in data]
            ys = [d[1] for d in data]
            self.ax.plot(xs, ys, marker="o")
            self.ax.set_xticklabels(xs, rotation=45, ha="right")
            self.ax.set_ylabel("Amount")
        else:
            self.ax.text(0.5, 0.5, "No payments yet", ha="center", va="center", transform=self.ax.transAxes)
            self.ax.set_xticks([])
            self.ax.set_yticks([])
        self.canvas.draw()
