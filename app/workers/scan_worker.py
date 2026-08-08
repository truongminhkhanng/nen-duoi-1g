from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from app.core.scanner import scan_files


class ScanWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)
    log = Signal(str)

    def __init__(self, source: Path, output: Path, recursive: bool,
                 skip_hidden: bool, skip_system: bool) -> None:
        super().__init__()
        self.source = source
        self.output = output
        self.recursive = recursive
        self.skip_hidden = skip_hidden
        self.skip_system = skip_system
        self._cancelled = False

    @Slot()
    def run(self) -> None:
        try:
            result = scan_files(self.source, self.output, self.recursive,
                                self.skip_hidden, self.skip_system,
                                lambda: self._cancelled, self.log.emit)
            self.finished.emit(result)
        except (ValueError, OSError, InterruptedError) as error:
            self.failed.emit(str(error))

    @Slot()
    def cancel(self) -> None:
        self._cancelled = True
