from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from app.core.models import FileEntry
from app.utils.sizes import format_size


class FileTableModel(QAbstractTableModel):
    HEADERS = ("Tên tệp", "Đường dẫn tương đối", "Dung lượng", "Trạng thái")

    def __init__(self) -> None:
        super().__init__()
        self.files: list[FileEntry] = []

    def rowCount(self, _parent: QModelIndex = QModelIndex()) -> int:
        return len(self.files)

    def columnCount(self, _parent: QModelIndex = QModelIndex()) -> int:
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        entry = self.files[index.row()]
        return (entry.path.name, entry.relative_path.as_posix(), format_size(entry.size),
                entry.status.value)[index.column()]

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]
        return super().headerData(section, orientation, role)

    def set_files(self, files: list[FileEntry]) -> None:
        self.beginResetModel()
        self.files = files
        self.endResetModel()

    def refresh_statuses(self) -> None:
        if self.files:
            first = self.index(0, 3)
            last = self.index(len(self.files) - 1, 3)
            self.dataChanged.emit(first, last, [Qt.ItemDataRole.DisplayRole])
