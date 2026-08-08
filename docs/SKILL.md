---
name: zip-part-maker
description: Develop and verify the Zip Part Maker PySide6 desktop application.
---

# Zip Part Maker development

1. Preserve the separation between Qt UI/workers and `app/core`.
2. Keep source files immutable and archive writes transactional (`.tmp`, verify, rename).
3. Run `python -m pytest` after core changes.
4. Run `QT_QPA_PLATFORM=offscreen python -c "from PySide6.QtWidgets import QApplication; from app.ui.main_window import MainWindow; a=QApplication([]); w=MainWindow(); w.close()"` after UI changes.
5. Build on the native target OS only.
