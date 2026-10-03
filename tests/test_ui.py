import os
import time
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QMessageBox

from app.core.models import CompressionOptions, FileEntry, ScanResult
from app.core.splitter import split_file
from app.ui import main_window
from app.ui.dialogs import JoinDialog
from app.workers.compress_worker import CompressWorker
from app.workers.join_worker import JoinWorker
from app.workers.scan_worker import ScanWorker


@pytest.fixture(scope="module")
def qt_app():
    application = QApplication.instance() or QApplication([])
    yield application


@pytest.fixture
def window(qt_app, tmp_path, monkeypatch):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    monkeypatch.setattr(main_window, "QSettings", lambda *_: settings)
    result = main_window.MainWindow()
    yield result
    result.close()


def wait_for(qt_app, predicate, timeout=5):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        qt_app.processEvents()
        time.sleep(0.005)
    assert predicate(), "Qt worker did not finish within the test deadline"


def test_blank_source_and_source_as_output_are_rejected(window, tmp_path):
    with pytest.raises(ValueError, match="nguồn"):
        window._paths()
    window.source_edit.setText(str(tmp_path))
    window.output_edit.setText(str(tmp_path))
    with pytest.raises(ValueError, match="khác"):
        window._paths()


@pytest.mark.parametrize("setting", ["source", "output", "recursive", "hidden", "system"])
def test_scan_inputs_invalidate_old_file_list(window, tmp_path, setting):
    item = FileEntry(tmp_path / "data.bin", Path("data.bin"), 1)
    window._scan_finished(ScanResult([item]))
    window._set_busy(False)
    assert window.start_button.isEnabled()
    if setting in {"source", "output"}:
        getattr(window, f"{setting}_edit").setText(str(tmp_path / "changed"))
    else:
        getattr(window, f"{setting}_check").setChecked(False)
    assert not window.scan_result.files
    assert window.file_model.rowCount() == 0
    assert not window.start_button.isEnabled()


def test_busy_state_locks_settings_and_resets_pause(window):
    window._set_busy(True)
    assert not window.source_edit.isEnabled()
    assert not window.limit_spin.isEnabled()
    assert not window.join_button.isEnabled()
    assert not window.acceptDrops()
    window.paused = True
    window.pause_button.setText("Tiếp tục")
    window._set_busy(False)
    assert window.source_edit.isEnabled()
    assert window.acceptDrops()
    assert not window.paused
    assert window.pause_button.text() == "Tạm dừng"


def test_scan_can_finish_and_enable_compression(qt_app, window, tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "data.bin").write_bytes(b"abc")
    window._set_source(source)
    window.scan()
    wait_for(qt_app, lambda: window.thread is None)
    assert window.file_model.rowCount() == 1
    assert window.start_button.isEnabled()


def test_scan_worker_emits_cancelled_without_failure(tmp_path):
    worker = ScanWorker(tmp_path, tmp_path / "out", True, True, True)
    results, errors, cancelled = [], [], []
    worker.finished.connect(results.append)
    worker.failed.connect(errors.append)
    worker.cancelled.connect(lambda: cancelled.append(True))
    worker.cancel()
    worker.run()
    assert cancelled == [True]
    assert not results and not errors


def test_progress_signals_preserve_sizes_above_two_gib(tmp_path):
    size = 5 * 1024**3
    join = JoinWorker(tmp_path / "manifest.json", tmp_path)
    compressor = CompressWorker(CompressionOptions(tmp_path, tmp_path / "out", size), [], [], [])
    received = []
    join.progress.connect(lambda done, total: received.append((done, total)))
    compressor.progress.connect(lambda done, total, *_: received.append((done, total)))
    join.progress.emit(size, size + 1)
    compressor.progress.emit(size, size + 1, "data", "part", 50)
    assert received == [(size, size + 1), (size, size + 1)]


def test_join_success_is_announced_after_thread_stops(qt_app, tmp_path, monkeypatch):
    source = tmp_path / "data.bin"
    source.write_bytes(b"abc")
    manifest = split_file(source, tmp_path / "parts", 2)
    dialog = JoinDialog()
    dialog.manifest.setText(str(manifest))
    dialog.output.setText(str(tmp_path / "joined"))
    notices = []
    monkeypatch.setattr(QMessageBox, "information", lambda *_: notices.append(dialog.thread))
    dialog._join()
    try:
        wait_for(qt_app, lambda: dialog.thread is None)
        assert notices == [None]
        assert (tmp_path / "joined" / "data.bin").read_bytes() == b"abc"
    finally:
        if dialog.worker:
            dialog.worker.cancel()
            wait_for(qt_app, lambda: dialog.thread is None)
        dialog.close()


def test_reject_during_join_keeps_dialog_alive_until_worker_stops(qt_app, tmp_path, monkeypatch):
    source = tmp_path / "data.bin"
    source.write_bytes(b"abc")
    manifest = split_file(source, tmp_path / "parts", 2)
    dialog = JoinDialog()
    dialog.show()
    dialog.manifest.setText(str(manifest))
    dialog.output.setText(str(tmp_path / "joined"))
    monkeypatch.setattr(QMessageBox, "information", lambda *_: None)
    dialog._join()
    dialog.reject()
    assert dialog.isVisible()
    try:
        wait_for(qt_app, lambda: dialog.thread is None)
        assert dialog.pick_manifest.isEnabled()
        assert dialog.buttons.button(QDialogButtonBox.StandardButton.Cancel).isEnabled()
    finally:
        if dialog.worker:
            dialog.worker.cancel()
            wait_for(qt_app, lambda: dialog.thread is None)
        dialog.close()
