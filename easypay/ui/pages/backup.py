from __future__ import annotations
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox
from ...services.backup import make_backup, restore_backup
from ...config import BACKUP_DIR

class BackupPage(QWidget):
    def __init__(self, on_restored=None):
        super().__init__()
        self.on_restored = on_restored
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)

        root.addWidget(QLabel("Backup & Restore (offline, local only)"))

        row = QHBoxLayout()
        self.btn_backup = QPushButton("Create Backup")
        self.btn_restore = QPushButton("Restore Backup")
        self.btn_restore.setStyleSheet("background:#334155;")
        row.addWidget(self.btn_backup)
        row.addWidget(self.btn_restore)
        row.addStretch(1)
        root.addLayout(row)

        root.addWidget(QLabel(f"Default backup folder: {BACKUP_DIR}"))

        self.btn_backup.clicked.connect(self.backup)
        self.btn_restore.clicked.connect(self.restore)

    def backup(self):
        try:
            p = make_backup()
            QMessageBox.information(self, "Backup Created", f"Backup saved:\n{p}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def restore(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Backup File", str(BACKUP_DIR), "Backup Files (*.backup);;All Files (*)")
        if not path:
            return
        if QMessageBox.question(self, "Confirm", "Restore will replace current data. Continue?") != QMessageBox.Yes:
            return
        try:
            restore_backup(Path(path))
            QMessageBox.information(self, "Restored", "Backup restored. The app will reload data now.")
            if self.on_restored:
                self.on_restored()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
