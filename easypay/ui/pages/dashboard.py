from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame
from PySide6.QtCore import Qt

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
        return f"{float(value):,.2f}"

    # -------------------------------------------------
    def _set_card_value(self, key: str, value: str):
        self.cards[key].layout().itemAt(1).widget().setText(value)

    # -------------------------------------------------
    def _set_card_border(self, key: str, border_color: str):
        self.cards[key].setStyleSheet(f"""
            QFrame {{
                background:#0b1220;
                border:1px solid {border_color};
                border-radius:18px;
            }}
        """)

    # -------------------------------------------------
    def refresh(self):
        k = dashboard_kpis()

        # BASIC NUMBERS
        self._set_card_value("total_customers", str(max(int(k["total_customers"]), 0)))
        self._set_card_value("total_investors", str(max(int(k["total_investors"]), 0)))
        self._set_card_value("active_plans", str(max(int(k["active_plans"]), 0)))
        self._set_card_value("completed_plans", str(max(int(k["completed_plans"]), 0)))

        # MONEY VALUES
        self._set_card_value("total_collected", self.money(max(float(k["total_collected"]), 0.0)))
        self._set_card_value("outstanding", self.money(max(float(k["outstanding"]), 0.0)))
        self._set_card_value("this_month", self.money(max(float(k["this_month"]), 0.0)))

        # OVERDUE
        self._set_card_value("overdue_count", str(max(int(k["overdue_count"]), 0)))

        # UI COLOR POLISH
        self._set_card_border("outstanding", "#ef4444" if k["outstanding"] > 0 else "#22c55e")
        self._set_card_border("overdue_count", "#ef4444" if k["overdue_count"] > 0 else "#22c55e")
        self._set_card_border("completed_plans", "#22c55e")
        self._set_card_border("active_plans", "#1f2937")

        # ---------------- CHART ----------------
        data = monthly_collections(12)
        self.ax.clear()

        self.ax.set_facecolor("#f8fafc")

        if any(v > 0 for _, v in data):
            labels = [d[0] for d in data]
            values = [d[1] for d in data]
            positions = list(range(len(labels)))

            self.ax.bar(positions, values)
            self.ax.set_ylabel("Amount")
            self.ax.set_xticks(positions)
            self.ax.set_xticklabels(labels, rotation=45, ha="right")

            self.ax.yaxis.set_major_formatter(
                ticker.FuncFormatter(lambda x, pos: f"{x:,.0f}")
            )

            self.ax.grid(axis="y", alpha=0.2)

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
        