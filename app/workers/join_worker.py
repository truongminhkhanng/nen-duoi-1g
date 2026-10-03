from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from app.core.splitter import join_file


class JoinWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)
    cancelled = Signal()
    progress = Signal("qlonglong", "qlonglong")

    def __init__(self, manifest: Path, output: Path) -> None:
        super().__init__()
        self.manifest = manifest
        self.output = output
        self._cancelled = threading.Event()

    @Slot()
    def run(self) -> None:
        try:
            result = join_file(self.manifest, self.output, self._cancelled.is_set,
                               self.progress.emit)
            self.finished.emit(str(result))
        except InterruptedError:
            self.cancelled.emit()
        except Exception as error:
            self.failed.emit(str(error))

    def cancel(self) -> None:
        self._cancelled.set()
