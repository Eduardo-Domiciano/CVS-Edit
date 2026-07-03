from collections.abc import Callable

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QColor, QCursor, QFont, QFontMetrics, QPalette
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QTableView, QToolTip

from app.constants import SELECTION_BG, SELECTION_FG
from app.models.csv_table_model import CsvTableModel


class BoldSelectionDelegate(QStyledItemDelegate):
    def __init__(self, table: QTableView, highlighted_column: Callable[[], int | None]):
        super().__init__(table)
        self._highlighted_column = highlighted_column

    def _apply_selection_style(self, opt) -> None:
        opt.backgroundBrush = QColor(SELECTION_BG)
        opt.palette.setColor(QPalette.ColorRole.Text, QColor(SELECTION_FG))
        opt.palette.setColor(QPalette.ColorRole.HighlightedText, QColor(SELECTION_FG))
        font = QFont(opt.font)
        font.setBold(True)
        opt.font = font

    def paint(self, painter, option, index) -> None:
        opt = option
        if CsvTableModel.is_checkbox_column(index.column()):
            super().paint(painter, opt, index)
            return

        col = self._highlighted_column()
        is_column = col is not None and index.column() == col
        is_selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        if is_column or is_selected:
            self._apply_selection_style(opt)
        super().paint(painter, opt, index)

    def helpEvent(self, event, view, option, index) -> bool:
        if not index.isValid() or CsvTableModel.is_checkbox_column(index.column()):
            return False
        if event.type() != QEvent.Type.ToolTip:
            return super().helpEvent(event, view, option, index)

        text = str(index.data(Qt.DisplayRole) or "")
        if not text:
            return False

        metrics = QFontMetrics(option.font)
        available = max(option.rect.width() - 10, 0)
        if metrics.horizontalAdvance(text) <= available:
            return False

        QToolTip.showText(QCursor.pos(), text, view)
        return True

    def editorEvent(self, event, model, option, index) -> bool:
        if not index.isValid() or not CsvTableModel.is_checkbox_column(index.column()):
            return super().editorEvent(event, model, option, index)

        if (
            event.type() == QEvent.Type.MouseButtonRelease
            and event.button() == Qt.MouseButton.LeftButton
        ):
            current = model.data(index, Qt.ItemDataRole.CheckStateRole)
            new_state = (
                Qt.CheckState.Unchecked
                if CsvTableModel._is_checked(current)
                else Qt.CheckState.Checked
            )
            return model.setData(index, new_state, Qt.ItemDataRole.CheckStateRole)

        return super().editorEvent(event, model, option, index)
