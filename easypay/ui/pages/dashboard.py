from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..widgets import KpiCard
from ...services.analytics import dashboard_kpis, monthly_collections

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(18)

        # ---------------- TITLE ----------------
        title = QLabel("Dashboard Overview")
        title.setObjectName("Title")
        subtitle = QLabel("Live business performance & financial summary")
        subtitle.setObjectName("Subtitle")

        root.addWidget(title)
        root.addWidget(subtitle)

        # ---------------- KPI GRID ----------------
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        root.addLayout(grid)

        self.cards = {}

        keys = [
            ("Total Customers", "total_customers"),
            ("Total Investors", "total_investors"),
            ("Active Plans", "active_plans"),
            ("Completed Plans", "completed_plans"),
            ("Total Collected", "total_collected"),
            ("Outstanding Balance", "outstanding"),
            ("Overdue Installments", "overdue_count"),
            ("This Month Collection", "this_month"),
        ]

        for idx, (label, key) in enumerate(keys):
            card = KpiCard(label, "—")
            self.cards[key] = card
            grid.addWidget(card, idx // 4, idx % 4)

        # ---------------- CHART FRAME ----------------
        chart_frame = QFrame()
        chart_frame.setStyleSheet("""
            QFrame {
                background:#0b1220;
                border:1px solid #1f2937;
                border-radius:18px;
            }
        """)
        cf = QVBoxLayout(chart_frame)
        cf.setContentsMargins(18, 16, 18, 16)

        chart_title = QLabel("Monthly Collections (Actual Payments)")
        chart_title.setStyleSheet("font-weight:600; font-size:15px;")
        cf.addWidget(chart_title)

        self.fig = Figure(figsize=(6, 3), tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        cf.addWidget(self.canvas)

        root.addWidget(chart_frame)

        self.refresh()

    # -------------------------------------------------
    def money(self, value: float) -> str:
        return f"{value:,.2f}"

    # -------------------------------------------------
    def refresh(self):
        k = dashboard_kpis()

        # BASIC NUMBERS
        self.cards["total_customers"].layout().itemAt(1).widget().setText(str(k["total_customers"]))
        self.cards["total_investors"].layout().itemAt(1).widget().setText(str(k["total_investors"]))
        self.cards["active_plans"].layout().itemAt(1).widget().setText(str(k["active_plans"]))
        self.cards["completed_plans"].layout().itemAt(1).widget().setText(str(k["completed_plans"]))

        # MONEY VALUES (Formatted)
        self.cards["total_collected"].layout().itemAt(1).widget().setText(self.money(k["total_collected"]))
        self.cards["outstanding"].layout().itemAt(1).widget().setText(self.money(k["outstanding"]))
        self.cards["this_month"].layout().itemAt(1).widget().setText(self.money(k["this_month"]))

        # OVERDUE
        self.cards["overdue_count"].layout().itemAt(1).widget().setText(str(k["overdue_count"]))

        # Color coding
        if k["outstanding"] > 0:
            self.cards["outstanding"].setStyleSheet("border:1px solid #ef4444;")
        else:
            self.cards["outstanding"].setStyleSheet("border:1px solid #22c55e;")

        if k["overdue_count"] > 0:
            self.cards["overdue_count"].setStyleSheet("border:1px solid #ef4444;")
        else:
            self.cards["overdue_count"].setStyleSheet("border:1px solid #22c55e;")

        # ---------------- CHART ----------------
        data = monthly_collections(12)
        self.ax.clear()

        if data:
            xs = [d[0] for d in data]
            ys = [d[1] for d in data]

            self.ax.plot(xs, ys, marker="o", linewidth=2)
            self.ax.fill_between(xs, ys, alpha=0.1)

            self.ax.set_ylabel("Amount")
            self.ax.set_xticks(range(len(xs)))
            self.ax.set_xticklabels(xs, rotation=45, ha="right")

            self.ax.yaxis.set_major_formatter(
                ticker.FuncFormatter(lambda x, pos: f"{x:,.0f}")
            )

            self.ax.grid(alpha=0.2)

        else:
            self.ax.text(
                0.5,
                0.5,
                "No payments yet",
                ha="center",
                va="center",
                transform=self.ax.transAxes
            )
            self.ax.set_xticks([])
            self.ax.set_yticks([])

        self.canvas.draw()