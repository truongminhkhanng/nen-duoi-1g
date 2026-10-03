from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from app.core.compressor import CompressionController, Compressor
from app.core.models import ArchiveGroup, CompressionOptions, FileEntry


class CompressWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)
    cancelled = Signal()
    log = Signal(str)
    progress = Signal("qlonglong", "qlonglong", str, str, int)

    def __init__(self, options: CompressionOptions, groups: list[ArchiveGroup],
                 oversized: list[FileEntry], scan_errors: list[str]) -> None:
        super().__init__()
        self.options = options
        self.groups = groups
        self.oversized = oversized
        self.scan_errors = scan_errors
        self.controller = CompressionController()

    @Slot()
    def run(self) -> None:
        try:
            compressor = Compressor(self.options, self.controller, self.log.emit,
                                    self.progress.emit)
            self.finished.emit(compressor.run(self.groups, self.oversized, self.scan_errors))
        except InterruptedError:
            self.cancelled.emit()
        except Exception as error:  # worker boundary: surface unexpected failures to UI
            self.failed.emit(f"{type(error).__name__}: {error}")

    def cancel(self) -> None:
        self.controller.cancel()

    def pause(self, paused: bool) -> None:
        self.controller.set_paused(paused)
