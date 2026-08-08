from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED

from PySide6.QtCore import QSettings, QThread, Qt, QUrl
from PySide6.QtGui import QCloseEvent, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
                               QFrame, QGridLayout, QGroupBox, QHBoxLayout,
                               QLabel, QLineEdit, QMainWindow, QMessageBox,
                               QPlainTextEdit, QProgressBar, QPushButton,
                               QHeaderView, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from app.core.models import CompressionOptions, ConflictAction, OversizeAction, ScanResult
from app.core.engines import resolve_engine
from app.core.models import CompressionEngine
from app.core.planner import plan_archives
from app.ui.dialogs import JoinDialog, choose_conflict_action, choose_oversize_action
from app.ui.styles import LIGHT_STYLE
from app.utils.paths import open_folder, validate_prefix
from app.utils.sizes import format_size, parse_size
from app.workers.compress_worker import CompressWorker
from app.workers.scan_worker import ScanWorker
from app.version import __version__


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Zip Part Maker")
        self.resize(1280, 820)
        self.setMinimumSize(1080, 720)
        self.setAcceptDrops(True)
        self.settings = QSettings("ZipPartMaker", "ZipPartMaker")
        self.scan_result = ScanResult()
        self.groups = []
        self.oversized = []
        self.thread: QThread | None = None
        self.worker: ScanWorker | CompressWorker | None = None
        self.paused = False
        self.active_engine = CompressionEngine.PYTHON
        self._build_ui()
        self._restore_settings()
        self.setStyleSheet(LIGHT_STYLE)

    def _build_ui(self) -> None:
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setCentralWidget(central)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(232)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 26, 20, 22)
        sidebar_layout.setSpacing(10)
        brand = QLabel("ZIP\nPART MAKER")
        brand.setObjectName("brand")
        sidebar_layout.addWidget(brand)
        tagline = QLabel("Đóng gói thông minh\nChia sẻ dễ dàng")
        tagline.setObjectName("tagline")
        sidebar_layout.addWidget(tagline)
        sidebar_layout.addSpacing(28)
        nav_title = QLabel("QUY TRÌNH")
        nav_title.setObjectName("navTitle")
        sidebar_layout.addWidget(nav_title)
        for text, active in (("01   Chọn thư mục", True),
                             ("02   Thiết lập ZIP", False),
                             ("03   Quét và đóng gói", False)):
            item = QLabel(text)
            item.setObjectName("navActive" if active else "navItem")
            sidebar_layout.addWidget(item)
        sidebar_layout.addStretch()
        open_button = QPushButton("Mở thư mục kết quả")
        open_button.setObjectName("sidebarButton")
        join_button = QPushButton("Ghép file đã chia…")
        join_button.setObjectName("sidebarButton")
        open_button.clicked.connect(self._open_output)
        join_button.clicked.connect(lambda: JoinDialog(self).exec())
        sidebar_layout.addWidget(open_button)
        sidebar_layout.addWidget(join_button)
        version_label = QLabel(f"Phiên bản {__version__}")
        version_label.setObjectName("versionLabel")
        sidebar_layout.addWidget(version_label)
        root.addWidget(sidebar)

        content = QWidget()
        content.setObjectName("content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 24, 28, 24)
        content_layout.setSpacing(14)
        root.addWidget(content, 1)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Tạo các gói ZIP độc lập theo đúng dung lượng bạn cần")
        subtitle.setObjectName("pageSubtitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading)
        header.addStretch()
        self.scan_button = QPushButton("Quét file")
        self.scan_button.setObjectName("secondary")
        self.start_button = QPushButton("Bắt đầu nén")
        self.start_button.setObjectName("primary")
        self.start_button.setEnabled(False)
        self.scan_button.clicked.connect(self.scan)
        self.start_button.clicked.connect(self.compress)
        header.addWidget(self.scan_button)
        header.addWidget(self.start_button)
        content_layout.addLayout(header)

        location = QGroupBox("Nguồn và kết quả")
        location_grid = QGridLayout(location)
        location_grid.setContentsMargins(18, 22, 18, 16)
        self.source_edit = QLineEdit()
        self.output_edit = QLineEdit()
        source_pick = QPushButton("Chọn thư mục")
        output_pick = QPushButton("Chọn đầu ra")
        source_pick.clicked.connect(self._choose_source)
        output_pick.clicked.connect(self._choose_output)
        location_grid.addWidget(QLabel("Thư mục nguồn"), 0, 0)
        location_grid.addWidget(self.source_edit, 0, 1)
        location_grid.addWidget(source_pick, 0, 2)
        location_grid.addWidget(QLabel("Thư mục đầu ra"), 1, 0)
        location_grid.addWidget(self.output_edit, 1, 1)
        location_grid.addWidget(output_pick, 1, 2)
        content_layout.addWidget(location)

        options = QGroupBox("Thiết lập đóng gói")
        option_grid = QGridLayout(options)
        option_grid.setContentsMargins(18, 22, 18, 16)
        self.limit_spin = QDoubleSpinBox()
        self.limit_spin.setRange(0.01, 99999)
        self.limit_spin.setDecimals(2)
        self.limit_spin.setValue(950)
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["MB", "GB"])
        self.level_combo = QComboBox()
        self.level_combo.addItems(["Không nén", "Nhanh", "Cân bằng", "Tối đa"])
        self.level_combo.setCurrentIndex(2)
        self.engine_combo = QComboBox()
        self.engine_combo.addItem("Tự động (khuyên dùng)", CompressionEngine.AUTO)
        self.engine_combo.addItem("7-Zip", CompressionEngine.SEVEN_ZIP)
        self.engine_combo.addItem("Python tích hợp", CompressionEngine.PYTHON)
        self.engine_status = QLabel()
        self.engine_status.setObjectName("engineStatus")
        self.prefix_edit = QLineEdit("part")
        option_grid.addWidget(QLabel("Giới hạn"), 0, 0)
        option_grid.addWidget(self.limit_spin, 0, 1)
        option_grid.addWidget(self.unit_combo, 0, 2)
        option_grid.addWidget(QLabel("Mức nén"), 0, 3)
        option_grid.addWidget(self.level_combo, 0, 4)
        option_grid.addWidget(QLabel("Prefix"), 0, 5)
        option_grid.addWidget(self.prefix_edit, 0, 6)
        self.recursive_check = QCheckBox("Quét thư mục con")
        self.structure_check = QCheckBox("Giữ cấu trúc thư mục")
        self.hidden_check = QCheckBox("Bỏ qua file ẩn")
        self.system_check = QCheckBox("Bỏ qua file hệ thống")
        self.open_check = QCheckBox("Mở thư mục kết quả khi xong")
        for checkbox in (self.recursive_check, self.structure_check, self.hidden_check,
                         self.system_check, self.open_check):
            checkbox.setChecked(True)
        checks = QHBoxLayout()
        for checkbox in (self.recursive_check, self.structure_check, self.hidden_check,
                         self.system_check, self.open_check):
            checks.addWidget(checkbox)
        checks.addStretch()
        option_grid.addLayout(checks, 1, 0, 1, 7)
        engine_row = QHBoxLayout()
        engine_row.addWidget(QLabel("Công cụ nén"))
        engine_row.addWidget(self.engine_combo)
        engine_row.addWidget(self.engine_status)
        engine_row.addStretch()
        option_grid.addLayout(engine_row, 2, 0, 1, 7)
        self.engine_combo.currentIndexChanged.connect(self._refresh_engine_status)
        self.structure_check.toggled.connect(self._refresh_engine_status)
        content_layout.addWidget(options)

        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.total_files = QLabel("Tổng file\n0")
        self.total_size = QLabel("Tổng dung lượng\n0 B")
        self.estimated = QLabel("ZIP dự kiến\n0")
        self.current_file = QLabel("File: —")
        self.current_zip = QLabel("ZIP: —")
        for label in (self.total_files, self.total_size, self.estimated):
            card = QFrame()
            card.setObjectName("statCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 12, 18, 12)
            label.setObjectName("statValue")
            card_layout.addWidget(label)
            stats.addWidget(card, 1)
        content_layout.addLayout(stats)

        self.table = QTableWidget(0, 4)
        self.table.setObjectName("fileTable")
        self.table.setHorizontalHeaderLabels(["Tên file", "Đường dẫn tương đối", "Dung lượng", "Trạng thái"])
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        content_layout.addWidget(self.table, 2)

        bottom = QHBoxLayout()
        bottom.setSpacing(12)
        progress_card = QFrame()
        progress_card.setObjectName("panel")
        progress_layout = QVBoxLayout(progress_card)
        progress_layout.setContentsMargins(18, 14, 18, 14)
        progress_title = QLabel("Tiến trình")
        progress_title.setObjectName("panelTitle")
        progress_layout.addWidget(progress_title)
        progress_layout.addWidget(self.current_file)
        progress_layout.addWidget(self.current_zip)
        self.total_progress = QProgressBar()
        self.zip_progress = QProgressBar()
        progress_layout.addWidget(QLabel("Tổng tiến trình"))
        progress_layout.addWidget(self.total_progress)
        progress_layout.addWidget(QLabel("ZIP hiện tại"))
        progress_layout.addWidget(self.zip_progress)

        actions = QHBoxLayout()
        self.pause_button = QPushButton("Tạm dừng")
        self.cancel_button = QPushButton("Hủy")
        self.pause_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.pause_button.clicked.connect(self._toggle_pause)
        self.cancel_button.clicked.connect(self._cancel)
        for button in (self.pause_button, self.cancel_button):
            actions.addWidget(button)
        actions.addStretch()
        progress_layout.addLayout(actions)
        bottom.addWidget(progress_card, 1)

        log_card = QFrame()
        log_card.setObjectName("panel")
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(18, 14, 18, 14)
        log_title = QLabel("Nhật ký hoạt động")
        log_title.setObjectName("panelTitle")
        log_layout.addWidget(log_title)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(2000)
        self.log.setPlaceholderText("Nhật ký hoạt động…")
        log_layout.addWidget(self.log)
        bottom.addWidget(log_card, 1)
        content_layout.addLayout(bottom, 1)

    def _choose_source(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục nguồn", self.source_edit.text())
        if path:
            self._set_source(Path(path))

    def _set_source(self, path: Path) -> None:
        self.source_edit.setText(str(path))
        self.output_edit.setText(str(path / "ZIP_PARTS"))

    def _choose_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục đầu ra", self.output_edit.text())
        if path:
            self.output_edit.setText(path)

    def _paths(self) -> tuple[Path, Path]:
        source, output = Path(self.source_edit.text()), Path(self.output_edit.text())
        if not source.is_dir():
            raise ValueError("Hãy chọn thư mục nguồn hợp lệ")
        if not self.output_edit.text().strip():
            raise ValueError("Hãy chọn thư mục đầu ra")
        return source, output

    def scan(self) -> None:
        try:
            source, output = self._paths()
            parse_size(self.limit_spin.value(), self.unit_combo.currentText())
        except ValueError as error:
            QMessageBox.warning(self, "Thiết lập chưa hợp lệ", str(error))
            return
        self._set_busy(True, scanning=True)
        self.log.appendPlainText(f"Bắt đầu quét: {source}")
        worker = ScanWorker(source, output, self.recursive_check.isChecked(),
                            self.hidden_check.isChecked(), self.system_check.isChecked())
        self._start_worker(worker, self._scan_finished)

    def _start_worker(self, worker: ScanWorker | CompressWorker, finished: object) -> None:
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(finished)  # type: ignore[arg-type]
        worker.finished.connect(thread.quit)
        worker.failed.connect(self._failed)
        worker.failed.connect(thread.quit)
        worker.log.connect(self.log.appendPlainText)
        if isinstance(worker, CompressWorker):
            worker.cancelled.connect(self._cancelled)
            worker.cancelled.connect(thread.quit)
            worker.progress.connect(self._progress)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._thread_done)
        self.thread, self.worker = thread, worker
        thread.start()

    def _scan_finished(self, result: object) -> None:
        self.scan_result = result  # type: ignore[assignment]
        limit = parse_size(self.limit_spin.value(), self.unit_combo.currentText())
        self.groups, self.oversized = plan_archives(self.scan_result.files, limit)
        self.table.setRowCount(len(self.scan_result.files))
        for row, entry in enumerate(self.scan_result.files):
            values = (entry.path.name, entry.relative_path.as_posix(), format_size(entry.size), entry.status.value)
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()
        self.total_files.setText(f"Tổng file\n{len(self.scan_result.files)}")
        self.total_size.setText(f"Tổng dung lượng\n{format_size(self.scan_result.total_size)}")
        self.estimated.setText(f"ZIP dự kiến\n{len(self.groups)} (+{len(self.oversized)} quá lớn)")
        self.log.appendPlainText(f"Quét xong: {len(self.scan_result.files)} file, {len(self.scan_result.errors)} lỗi")
        self.start_button.setEnabled(bool(self.scan_result.files))

    def _compression_settings(self) -> tuple[int, int | None]:
        return [(ZIP_STORED, None), (ZIP_DEFLATED, 1), (ZIP_DEFLATED, 6),
                (ZIP_DEFLATED, 9)][self.level_combo.currentIndex()]

    def _selected_engine(self) -> CompressionEngine:
        return self.engine_combo.currentData()

    def _engine_info(self):
        return resolve_engine(self._selected_engine(), self.structure_check.isChecked())

    def _refresh_engine_status(self) -> None:
        info = self._engine_info()
        detail = f" — {info.fallback_reason}" if info.fallback_reason else ""
        self.engine_status.setText(f"Đang dùng: {info.label}{detail}")

    def compress(self) -> None:
        try:
            source, output = self._paths()
            limit = parse_size(self.limit_spin.value(), self.unit_combo.currentText())
            prefix = validate_prefix(self.prefix_edit.text())
        except ValueError as error:
            QMessageBox.warning(self, "Thiết lập chưa hợp lệ", str(error))
            return
        self.groups, self.oversized = plan_archives(self.scan_result.files, limit)
        oversize_action = OversizeAction.SKIP
        if self.oversized:
            selected = choose_oversize_action(self, len(self.oversized))
            if selected is None:
                return
            oversize_action = selected
        output.mkdir(parents=True, exist_ok=True)
        conflict = choose_conflict_action(self, output, prefix)
        if conflict is None:
            return
        compression, level = self._compression_settings()
        engine = self._engine_info()
        self.active_engine = engine.engine
        self.log.appendPlainText(f"Công cụ nén: {engine.label}")
        if engine.fallback_reason:
            self.log.appendPlainText(f"Lưu ý: {engine.fallback_reason}")
        options = CompressionOptions(source, output, limit, prefix, compression, level,
                                     self.structure_check.isChecked(), conflict, oversize_action,
                                     engine.engine, engine.executable)
        self._save_settings()
        self._set_busy(True, scanning=False)
        worker = CompressWorker(options, self.groups, self.oversized, self.scan_result.errors)
        self._start_worker(worker, self._compression_finished)

    def _progress(self, done: int, total: int, filename: str, archive: str, current: int) -> None:
        self.total_progress.setValue(min(100, int(done * 100 / max(total, 1))))
        self.zip_progress.setValue(current)
        self.current_file.setText(f"File: {filename or '—'}")
        self.current_zip.setText(f"ZIP: {archive or '—'}")

    def _compression_finished(self, report: object) -> None:
        data = report  # type: ignore[assignment]
        self.total_progress.setValue(100)
        self.zip_progress.setValue(100)
        self._refresh_statuses()
        archives = len(data.get("archives", []))
        errors = len(data.get("errors", []))
        QMessageBox.information(self, "Hoàn thành", f"Đã tạo {archives} ZIP. Lỗi: {errors}.\nĐã ghi zip_report.json.")
        if self.open_check.isChecked():
            self._open_output()

    def _refresh_statuses(self) -> None:
        for row, entry in enumerate(self.scan_result.files):
            item = self.table.item(row, 3)
            if item:
                item.setText(entry.status.value)

    def _failed(self, message: str) -> None:
        self.log.appendPlainText(f"Lỗi: {message}")
        QMessageBox.critical(self, "Có lỗi", message)

    def _cancelled(self) -> None:
        self.log.appendPlainText("Đã hủy. File tạm chưa hoàn chỉnh đã được xóa.")
        self._refresh_statuses()

    def _thread_done(self) -> None:
        self.thread = None
        self.worker = None
        self._set_busy(False)

    def _set_busy(self, busy: bool, scanning: bool = False) -> None:
        self.scan_button.setEnabled(not busy)
        self.start_button.setEnabled(not busy and bool(self.scan_result.files))
        can_pause = self.active_engine == CompressionEngine.PYTHON
        self.pause_button.setEnabled(busy and not scanning and can_pause)
        self.pause_button.setToolTip("" if can_pause else "7-Zip không hỗ trợ tạm dừng an toàn")
        self.cancel_button.setEnabled(busy)

    def _toggle_pause(self) -> None:
        if isinstance(self.worker, CompressWorker):
            self.paused = not self.paused
            self.worker.pause(self.paused)
            self.pause_button.setText("Tiếp tục" if self.paused else "Tạm dừng")

    def _cancel(self) -> None:
        if isinstance(self.worker, (ScanWorker, CompressWorker)):
            self.worker.cancel()
            self.cancel_button.setEnabled(False)
            self.log.appendPlainText("Đang hủy an toàn sau file hiện tại…")

    def _open_output(self) -> None:
        path = Path(self.output_edit.text())
        if not path.is_dir():
            QMessageBox.warning(self, "Không tìm thấy", "Thư mục kết quả chưa tồn tại")
            return
        try:
            open_folder(path)
        except OSError as error:
            QMessageBox.critical(self, "Không thể mở thư mục", str(error))

    def _restore_settings(self) -> None:
        self.source_edit.setText(self.settings.value("source", "", str))
        self.output_edit.setText(self.settings.value("output", "", str))
        self.limit_spin.setValue(self.settings.value("limit", 950.0, float))
        self.unit_combo.setCurrentText(self.settings.value("unit", "MB", str))
        self.level_combo.setCurrentIndex(self.settings.value("level", 2, int))
        saved_engine = self.settings.value("engine", CompressionEngine.AUTO.value, str)
        engine_index = self.engine_combo.findData(CompressionEngine(saved_engine))
        self.engine_combo.setCurrentIndex(max(engine_index, 0))
        self.prefix_edit.setText(self.settings.value("prefix", "part", str))
        for key, widget in (("recursive", self.recursive_check), ("structure", self.structure_check),
                            ("hidden", self.hidden_check), ("system", self.system_check),
                            ("open", self.open_check)):
            widget.setChecked(self.settings.value(key, True, bool))
        self._refresh_engine_status()

    def _save_settings(self) -> None:
        for key, value in (("source", self.source_edit.text()), ("output", self.output_edit.text()),
                           ("limit", self.limit_spin.value()), ("unit", self.unit_combo.currentText()),
                           ("level", self.level_combo.currentIndex()), ("prefix", self.prefix_edit.text()),
                           ("engine", self._selected_engine().value),
                           ("recursive", self.recursive_check.isChecked()),
                           ("structure", self.structure_check.isChecked()),
                           ("hidden", self.hidden_check.isChecked()),
                           ("system", self.system_check.isChecked()), ("open", self.open_check.isChecked())):
            self.settings.setValue(key, value)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        urls = event.mimeData().urls()
        if len(urls) == 1 and urls[0].isLocalFile() and Path(urls[0].toLocalFile()).is_dir():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        self._set_source(Path(event.mimeData().urls()[0].toLocalFile()))
        event.acceptProposedAction()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.thread and self.thread.isRunning():
            QMessageBox.warning(self, "Đang xử lý", "Hãy hủy tác vụ và đợi hoàn tất trước khi đóng.")
            event.ignore()
            return
        self._save_settings()
        event.accept()
