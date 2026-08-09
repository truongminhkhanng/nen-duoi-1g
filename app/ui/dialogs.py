from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
                               QLineEdit, QMessageBox, QProgressBar, QPushButton)

from app.core.models import ConflictAction, OversizeAction
from app.workers.join_worker import JoinWorker


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
        self.thread: QThread | None = None
        self.worker: JoinWorker | None = None
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
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addRow("Tiến trình", self.progress)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                        QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self._join)
        self.buttons.rejected.connect(self._cancel_or_reject)
        layout.addRow(self.buttons)

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
            manifest = Path(self.manifest.text())
            output = Path(self.output.text())
            if not manifest.is_file():
                raise ValueError("Hãy chọn manifest hợp lệ")
            if not self.output.text().strip():
                raise ValueError("Hãy chọn thư mục đầu ra")
        except ValueError as error:
            QMessageBox.warning(self, "Thiết lập chưa hợp lệ", str(error))
            return
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.manifest.setEnabled(False)
        self.output.setEnabled(False)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Hủy ghép")
        thread = QThread(self)
        worker = JoinWorker(manifest, output)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._update_progress)
        worker.finished.connect(self._joined)
        worker.failed.connect(self._join_failed)
        worker.cancelled.connect(self._join_cancelled)
        for signal in (worker.finished, worker.failed, worker.cancelled):
            signal.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._join_thread_done)
        self.thread, self.worker = thread, worker
        thread.start()

    def _update_progress(self, completed: int, total: int) -> None:
        self.progress.setValue(int(completed * 100 / max(total, 1)))

    def _joined(self, result: str) -> None:
        self.progress.setValue(100)
        QMessageBox.information(self, "Hoàn thành", f"Đã ghép: {result}")
        self.accept()

    def _join_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Không thể ghép", message)

    def _join_cancelled(self) -> None:
        QMessageBox.information(self, "Đã hủy", "Đã hủy ghép và xóa file tạm")

    def _cancel_or_reject(self) -> None:
        if self.worker:
            self.worker.cancel()
            self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setEnabled(False)
        else:
            self.reject()

    def _join_thread_done(self) -> None:
        self.thread = None
        self.worker = None
        if self.isVisible():
            self.manifest.setEnabled(True)
            self.output.setEnabled(True)
            self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
            cancel = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
            cancel.setEnabled(True)
            cancel.setText("Hủy")
