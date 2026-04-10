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
    get_backup_root,
    set_backup_root,
    ensure_backup_root,
)


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
        self.btn_change_backup_location = QPushButton("Change Emergency Backup Location")

        self.btn_restore.setStyleSheet("background:#334155;")
        self.btn_change_backup_location.setStyleSheet("background:#0f766e; color:white;")

        row.addWidget(self.btn_backup)
        row.addWidget(self.btn_restore)
        row.addWidget(self.btn_change_backup_location)
        row.addStretch(1)

        root.addLayout(row)

        # Current backup path label
        self.lbl_backup_location_title = QLabel("Current Emergency / Auto Backup Location:")
        self.lbl_backup_location_title.setStyleSheet("font-weight:bold;")

        self.lbl_backup_location = QLabel(str(ensure_backup_root()))
        self.lbl_backup_location.setWordWrap(True)
        self.lbl_backup_location.setStyleSheet("color:#94a3b8;")

        root.addWidget(self.lbl_backup_location_title)
        root.addWidget(self.lbl_backup_location)

        # Info Label
        self.info = QLabel()
        self.info.setWordWrap(True)
        root.addWidget(self.info)

        self._refresh_info_text()

        # Connect Buttons
        self.btn_backup.clicked.connect(self.backup)
        self.btn_restore.clicked.connect(self.restore)
        self.btn_change_backup_location.clicked.connect(self.change_backup_location)

    def _refresh_info_text(self):
        current_backup_root = ensure_backup_root()
        self.lbl_backup_location.setText(str(current_backup_root))

        self.info.setText(
            "Manual backups can be saved to any location (USB, D Drive, Desktop, etc).\n"
            "Emergency and auto backups are stored in the selected permanent backup folder.\n"
            f"System backup folder: {current_backup_root}"
        )

    # -------------------------
    # CHANGE PERMANENT BACKUP LOCATION
    # -------------------------
    def change_backup_location(self):
        current_path = str(get_backup_root())

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Permanent Backup Folder",
            current_path,
        )

        if not folder:
            return

        try:
            new_path = set_backup_root(folder)
            self._refresh_info_text()

            QMessageBox.information(
                self,
                "Backup Location Updated",
                "Emergency and auto backups will now be saved to:\n\n"
                f"{new_path}",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Update Failed",
                str(e),
            )

    # -------------------------
    # MANUAL BACKUP
    # -------------------------
    def backup(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Backup Folder",
            str(get_backup_root()),
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
            str(get_backup_root()),
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
            