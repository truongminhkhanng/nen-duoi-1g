from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from app.utils.logging_utils import configure_logging


def main() -> int:
    configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("Zip Part Maker")
    app.setOrganizationName("ZipPartMaker")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
