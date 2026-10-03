from __future__ import annotations

from pathlib import Path
from glob import escape

from PySide6.QtCore import QThread
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
                               QLineEdit, QMessageBox, QProgressBar, QPushButton)

from app.core.models import ConflictAction, OversizeAction
from app.workers.join_worker import JoinWorker


def choose_oversize_action(parent: object, count: int) -> OversizeAction | None:
    box = QMessageBox(parent)  # type: ignore[arg-type]
    box.setWindowTitle("Tệp vượt dung lượng dự kiến")
    box.setText(f"Có {count} tệp vượt dung lượng dự kiến cho một ZIP, đã tính phần dự phòng 2%.\n\n"
                "Bạn có thể bỏ qua, nén thử từng tệp hoặc chia thành các phần nhỏ. "
                "Nén thử chỉ tạo ZIP khi kết quả nhỏ hơn giới hạn. Các phần đã chia cần "
                "được tải đủ và ghép lại trước khi sử dụng.")
    skip = box.addButton("Bỏ qua", QMessageBox.ButtonRole.AcceptRole)
    attempt = box.addButton("Nén thử riêng", QMessageBox.ButtonRole.ActionRole)
    split = box.addButton("Chia tệp để ghép lại", QMessageBox.ButtonRole.ActionRole)
    box.addButton("Hủy", QMessageBox.ButtonRole.RejectRole)
    box.setDefaultButton(skip)
    box.exec()
    return {skip: OversizeAction.SKIP, attempt: OversizeAction.TRY_COMPRESS,
            split: OversizeAction.SPLIT}.get(box.clickedButton())


def choose_conflict_action(parent: object, output: Path, prefix: str) -> ConflictAction | None:
    if not list(output.glob(f"{escape(prefix)}_[0-9][0-9][0-9]*.zip")):
        return ConflictAction.RENAME
    box = QMessageBox(parent)  # type: ignore[arg-type]
    box.setWindowTitle("ZIP đã tồn tại")
    box.setText(f"Thư mục kết quả đã có ZIP với tiền tố “{prefix}”. Chọn cách xử lý:")
    overwrite = box.addButton("Ghi đè", QMessageBox.ButtonRole.AcceptRole)
    rename = box.addButton("Tạo tên mới", QMessageBox.ButtonRole.ActionRole)
    clean = box.addButton("Xóa ZIP cũ", QMessageBox.ButtonRole.DestructiveRole)
    box.addButton("Hủy", QMessageBox.ButtonRole.RejectRole)
    box.setDefaultButton(rename)
    box.exec()
    clicked = box.clickedButton()
    if clicked == clean:
        confirm = QMessageBox(parent)  # type: ignore[arg-type]
        confirm.setWindowTitle("Xác nhận xóa ZIP cũ")
        confirm.setText(f"Các ZIP khớp mẫu {prefix}_NNN*.zip trong thư mục sau sẽ bị xóa:\n"
                        f"{output}\n\nCác tệp này không được đưa vào thùng rác.")
        delete = confirm.addButton("Xóa ZIP cũ", QMessageBox.ButtonRole.DestructiveRole)
        cancel = confirm.addButton("Hủy", QMessageBox.ButtonRole.RejectRole)
        confirm.setDefaultButton(cancel)
        confirm.exec()
        if confirm.clickedButton() != delete:
            return None
    return {overwrite: ConflictAction.OVERWRITE, rename: ConflictAction.RENAME,
            clean: ConflictAction.CLEAN}.get(clicked)


class JoinDialog(QDialog):
    def __init__(self, parent: object = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self.setWindowTitle("Ghép tệp đã chia")
        self.setMinimumWidth(620)
        self.thread: QThread | None = None
        self.worker: JoinWorker | None = None
        self._outcome: tuple[str, str] | None = None
        layout = QFormLayout(self)
        self.manifest = QLineEdit()
        self.output = QLineEdit()
        self.manifest.setPlaceholderText("Chọn tệp .manifest.json được tạo khi chia tệp")
        self.manifest.setToolTip("Giữ tệp .manifest.json và đầy đủ các phần .001, .002… trong cùng thư mục.")
        self.output.setPlaceholderText("Chọn thư mục lưu tệp sau khi ghép")
        self.output.setToolTip("Nếu tên tệp đã tồn tại, ứng dụng tạo tên mới để giữ nguyên tệp cũ.")
        self.pick_manifest = QPushButton("Chọn danh sách ghép…")
        self.pick_output = QPushButton("Chọn nơi lưu…")
        self.pick_manifest.clicked.connect(self._pick_manifest)
        self.pick_output.clicked.connect(self._pick_output)
        layout.addRow("Danh sách ghép", self.manifest)
        layout.addRow("Thư mục lưu kết quả", self.output)
        layout.addRow(self.pick_manifest, self.pick_output)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addRow("Tiến trình", self.progress)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                        QDialogButtonBox.StandardButton.Cancel)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Ghép tệp")
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Đóng")
        self.buttons.accepted.connect(self._join)
        self.buttons.rejected.connect(self._cancel_or_reject)
        layout.addRow(self.buttons)

    def _pick_manifest(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Chọn danh sách ghép", filter="Danh sách ghép (*.manifest.json);;Tệp JSON (*.json)")
        if path:
            self.manifest.setText(path)
            self.output.setText(str(Path(path).parent))

    def _pick_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu kết quả")
        if path:
            self.output.setText(path)

    def _join(self) -> None:
        if self.thread is not None:
            return
        try:
            manifest = Path(self.manifest.text())
            output = Path(self.output.text())
            if not manifest.is_file():
                raise ValueError("Hãy chọn tệp danh sách ghép hợp lệ")
            if not self.output.text().strip():
                raise ValueError("Hãy chọn thư mục lưu kết quả")
        except ValueError as error:
            QMessageBox.warning(self, "Thiết lập chưa hợp lệ", str(error))
            return
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.manifest.setEnabled(False)
        self.output.setEnabled(False)
        self.pick_manifest.setEnabled(False)
        self.pick_output.setEnabled(False)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Hủy ghép")
        self._outcome = None
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
        self._outcome = ("finished", result)

    def _join_failed(self, message: str) -> None:
        self._outcome = ("failed", message)

    def _join_cancelled(self) -> None:
        self._outcome = ("cancelled", "")

    def _cancel_or_reject(self) -> None:
        if self.worker:
            self.worker.cancel()
            self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setEnabled(False)
        else:
            super().reject()

    def reject(self) -> None:
        self._cancel_or_reject()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.thread is not None:
            self._cancel_or_reject()
            event.ignore()
        else:
            super().closeEvent(event)

    def _join_thread_done(self) -> None:
        self.thread = None
        self.worker = None
        if self.isVisible():
            self.manifest.setEnabled(True)
            self.output.setEnabled(True)
            self.pick_manifest.setEnabled(True)
            self.pick_output.setEnabled(True)
            self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
            cancel = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
            cancel.setEnabled(True)
            cancel.setText("Đóng")
        outcome, self._outcome = self._outcome, None
        if outcome:
            state, message = outcome
            if state == "finished":
                QMessageBox.information(self, "Đã ghép tệp", f"Tệp kết quả được lưu tại:\n{message}")
                self.accept()
            elif state == "failed":
                QMessageBox.critical(self, "Không thể ghép tệp", message)
            else:
                QMessageBox.information(self, "Đã hủy ghép", "Đã hủy ghép tệp và dọn tệp tạm của tác vụ.")
