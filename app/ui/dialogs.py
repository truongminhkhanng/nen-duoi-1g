from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
                               QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout)

from app.core.models import ConflictAction, OversizeAction
from app.core.splitter import join_file


def choose_oversize_action(parent: object, count: int) -> OversizeAction | None:
    box = QMessageBox(parent)  # type: ignore[arg-type]
    box.setWindowTitle("File quá lớn")
    box.setText(f"Phát hiện {count} file mà riêng từng file đã lớn hơn giới hạn ZIP.\n\n"
                "App được thiết kế để phân phối nhiều file vào các ZIP độc lập; một file đơn quá "
                "lớn không thể bảo đảm nằm trong ZIP dưới giới hạn. Chọn cách xử lý:")
    skip = box.addButton("Bỏ qua", QMessageBox.ButtonRole.AcceptRole)
    attempt = box.addButton("Nén thử riêng", QMessageBox.ButtonRole.ActionRole)
    split = box.addButton("Chia file (phải ghép lại)", QMessageBox.ButtonRole.ActionRole)
    box.addButton(QMessageBox.StandardButton.Cancel)
    box.exec()
    return {skip: OversizeAction.SKIP, attempt: OversizeAction.TRY_COMPRESS,
            split: OversizeAction.SPLIT}.get(box.clickedButton())


def choose_conflict_action(parent: object, output: Path, prefix: str) -> ConflictAction | None:
    if not list(output.glob(f"{prefix}_[0-9][0-9][0-9]*.zip")):
        return ConflictAction.RENAME
    box = QMessageBox(parent)  # type: ignore[arg-type]
    box.setWindowTitle("File ZIP đã tồn tại")
    box.setText("Thư mục kết quả đã có ZIP cùng prefix. Chọn cách xử lý:")
    overwrite = box.addButton("Ghi đè", QMessageBox.ButtonRole.AcceptRole)
    rename = box.addButton("Tạo tên mới", QMessageBox.ButtonRole.ActionRole)
    clean = box.addButton("Xóa ZIP cũ", QMessageBox.ButtonRole.DestructiveRole)
    box.addButton(QMessageBox.StandardButton.Cancel)
    box.exec()
    clicked = box.clickedButton()
    if clicked == clean:
        confirm = QMessageBox.question(parent, "Xác nhận xóa",
            "Chỉ các ZIP có tên do ứng dụng tạo với prefix này sẽ bị xóa. Tiếp tục?")
        if confirm != QMessageBox.StandardButton.Yes:
            return None
    return {overwrite: ConflictAction.OVERWRITE, rename: ConflictAction.RENAME,
            clean: ConflictAction.CLEAN}.get(clicked)


class JoinDialog(QDialog):
    def __init__(self, parent: object = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self.setWindowTitle("Ghép file từ manifest")
        layout = QFormLayout(self)
        self.manifest = QLineEdit()
        self.output = QLineEdit()
        pick_manifest = QPushButton("Chọn…")
        pick_output = QPushButton("Chọn…")
        pick_manifest.clicked.connect(self._pick_manifest)
        pick_output.clicked.connect(self._pick_output)
        layout.addRow("Manifest JSON", self.manifest)
        layout.addRow("Thư mục đầu ra", self.output)
        layout.addRow(pick_manifest, pick_output)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._join)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _pick_manifest(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Chọn manifest", filter="JSON (*.json)")
        if path:
            self.manifest.setText(path)
            self.output.setText(str(Path(path).parent))

    def _pick_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục đầu ra")
        if path:
            self.output.setText(path)

    def _join(self) -> None:
        try:
            result = join_file(Path(self.manifest.text()), Path(self.output.text()))
            QMessageBox.information(self, "Hoàn thành", f"Đã ghép: {result}")
            self.accept()
        except (OSError, ValueError, KeyError) as error:
            QMessageBox.critical(self, "Không thể ghép", str(error))
