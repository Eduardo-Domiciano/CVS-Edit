from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHeaderView, QTableView


class ColumnHighlightHeader(QHeaderView):
    column_clicked = Signal(int)

    def __init__(self, table: QTableView):
        super().__init__(Qt.Horizontal, table)
        self._table = table
        self.setSectionsClickable(True)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            logical = self.logicalIndexAt(pos)
            if logical >= 0:
                self.column_clicked.emit(logical)
        super().mousePressEvent(event)
