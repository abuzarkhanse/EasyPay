from __future__ import annotations

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
)

from easypay.services.backup import (
    create_manual_backup_to_folder,
    restore_from_backup_zip,
)

from easypay.config import BACKUP_DIR


class BackupPage(QWidget):
    def __init__(self, on_restored=None):
        super().__init__()
        self.on_restored = on_restored

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)

        # Title
        title = QLabel("Backup & Restore (Offline - Local Only)")
        title.setStyleSheet("font-size:16px; font-weight:bold;")
        root.addWidget(title)

        # Buttons Row
        row = QHBoxLayout()

        self.btn_backup = QPushButton("Create Backup")
        self.btn_restore = QPushButton("Restore Backup")
        self.btn_restore.setStyleSheet("background:#334155;")

        row.addWidget(self.btn_backup)
        row.addWidget(self.btn_restore)
        row.addStretch(1)

        root.addLayout(row)

        # Info Label
        info = QLabel(
            "Manual backups can be saved to any location (USB, D Drive, Desktop, etc).\n"
            f"Emergency auto-backups are stored in ProgramData.\n"
            f"System backup folder: {BACKUP_DIR}"
        )
        info.setWordWrap(True)
        root.addWidget(info)

        # Connect Buttons
        self.btn_backup.clicked.connect(self.backup)
        self.btn_restore.clicked.connect(self.restore)

    # -------------------------
    # MANUAL BACKUP
    # -------------------------
    def backup(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Backup Folder",
        )

        if not folder:
            return

        try:
            out_path = create_manual_backup_to_folder(Path(folder))
            QMessageBox.information(
                self,
                "Backup Created",
                f"Backup successfully saved:\n\n{out_path}",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Backup Failed",
                str(e),
            )

    # -------------------------
    # RESTORE BACKUP
    # -------------------------
    def restore(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup File",
            str(BACKUP_DIR),
            "ZIP Backup Files (*.zip)",
        )

        if not file_path:
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Restore",
            "Restoring will replace current database and receipts.\n\nAre you sure you want to continue?",
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            restore_from_backup_zip(Path(file_path))

            QMessageBox.information(
                self,
                "Restore Complete",
                "Backup restored successfully.\nPlease restart the application.",
            )

            if self.on_restored:
                self.on_restored()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Restore Failed",
                str(e),
            )