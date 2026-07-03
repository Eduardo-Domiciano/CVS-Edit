import csv
from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt







class CsvTableModel(QAbstractTableModel):
    CHECKBOX_COLUMN = 0

    @staticmethod
    def _is_checked(value) -> bool:
        try:
            return Qt.CheckState(value) == Qt.CheckState.Checked
        except (ValueError, TypeError):
            return value == Qt.CheckState.Checked

    def __init__(self, headers: list[str] | None = None, rows: list[list[str]] | None = None):
        super().__init__()
        self._headers = headers or []
        self._rows = rows or []
        self._row_checks: list[bool] = []
        self._delimiter = ","
        self._sync_row_checks()

    def data_column_count(self) -> int:
        if self._headers:
            return len(self._headers)
        if self._rows:
            return max(len(row) for row in self._rows)
        return 0



    @classmethod
    def is_checkbox_column(cls, col: int) -> bool:
        return col == cls.CHECKBOX_COLUMN

    @classmethod
    def to_data_column(cls, view_col: int) -> int | None:
        if cls.is_checkbox_column(view_col):
            return None
        return view_col - 1

    @classmethod
    def to_view_column(cls, data_col: int) -> int:
        return data_col + 1
    def _sync_row_checks(self) -> None:
        while len(self._row_checks) < len(self._rows):
            self._row_checks.append(False)
        del self._row_checks[len(self._rows) :]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._rows)


    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return 1 + self.data_column_count()

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.NoItemFlags
        if self.is_checkbox_column(index.column()):
            return (
                Qt.ItemIsEnabled
                | Qt.ItemIsSelectable
                | Qt.ItemIsUserCheckable
            )
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None


        row, col = index.row(), index.column()
        if self.is_checkbox_column(col):
            if role == Qt.ItemDataRole.CheckStateRole:
                self._sync_row_checks()
                if row < len(self._row_checks) and self._row_checks[row]:
                    return Qt.CheckState.Checked
                return Qt.CheckState.Unchecked
            return None

        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None

        data_col = self.to_data_column(col)
        if data_col is None:
            return ""
        if row >= len(self._rows) or data_col >= len(self._rows[row]):
            return ""
        return self._rows[row][data_col]








    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if not index.isValid():
            return False

        row, col = index.row(), index.column()
        if self.is_checkbox_column(col):
            if role != Qt.ItemDataRole.CheckStateRole:
                return False
            self._sync_row_checks()
            checked = self._is_checked(value)
            if row < len(self._row_checks) and self._row_checks[row] == checked:
                return True
            while len(self._row_checks) <= row:
                self._row_checks.append(False)
            self._row_checks[row] = checked
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])
            return True

        if role != Qt.EditRole:
            return False

        data_col = self.to_data_column(col)
        if data_col is None:
            return False

        text = "" if value is None else str(value)
        while len(self._rows) <= row:
            self._rows.append([""] * len(self._headers))
        row_data = self._rows[row]
        while len(row_data) <= data_col:
            row_data.append("")
        if row_data[data_col] == text:
            return True


        row_data[data_col] = text
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation != Qt.Horizontal or role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        if self.is_checkbox_column(section):
            return ""
        data_col = self.to_data_column(section)
        if data_col is not None and data_col < len(self._headers):
            return self._headers[data_col]
        return f"Coluna {section}"

    def setHeaderData(
        self, section: int, orientation: Qt.Orientation, value, role: int = Qt.EditRole
    ) -> bool:
        if (
            orientation != Qt.Horizontal
            or role != Qt.EditRole
            or self.is_checkbox_column(section)
        ):
            return False



        data_col = self.to_data_column(section)
        if data_col is None or data_col >= len(self._headers):
            return False

        text = "" if value is None else str(value)
        if self._headers[data_col] == text:
            return True

        self._headers[data_col] = text
        self.headerDataChanged.emit(Qt.Horizontal, section, section)
        return True


    def load(self, path: Path) -> None:
        self.beginResetModel()
        self._headers = []
        self._rows = []
        with path.open(newline="", encoding="utf-8-sig") as f:
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except csv.Error:
                dialect = csv.excel
            self._delimiter = dialect.delimiter

            reader = csv.reader(f, dialect)
            for i, row in enumerate(reader):
                if i == 0:
                    self._headers = row
                else:
                    self._rows.append(row)



        if self._rows and len(self._headers) < self.data_column_count():
            while len(self._headers) < self.data_column_count():
                self._headers.append(f"Coluna {len(self._headers) + 1}")

        self._normalize_rows()
        self._sync_row_checks()
        self.endResetModel()

 
 
 
    def _normalize_rows(self) -> None:
        width = len(self._headers)
        for row in self._rows:
            if len(row) < width:
                row.extend([""] * (width - len(row)))
            elif len(row) > width:
                del row[width:]

    def _next_column_name(self) -> str:
        n = 1
        existing = set(self._headers)
        while f"Coluna {n}" in existing:
            n += 1
        return f"Coluna {n}"
    def add_column(self, data_position: int | None = None) -> None:
        col_count = self.data_column_count()
        pos = col_count if data_position is None else max(0, min(data_position, col_count))
        view_pos = self.to_view_column(pos)

        self.beginInsertColumns(QModelIndex(), view_pos, view_pos)
        self._headers.insert(pos, self._next_column_name())
        for row in self._rows:
            row.insert(pos, "")
        self.endInsertColumns()

    def remove_column(self, data_col: int) -> bool:
        if data_col < 0 or data_col >= self.data_column_count():
            return False

        view_col = self.to_view_column(data_col)
        self.beginRemoveColumns(QModelIndex(), view_col, view_col)
        self._headers.pop(data_col)
        for row in self._rows:
            if data_col < len(row):
                row.pop(data_col)
        self.endRemoveColumns()
        return True
    def clear_column_data(self, data_col: int) -> bool:
        if data_col < 0 or data_col >= self.data_column_count() or self.rowCount() == 0:
            return False

        view_col = self.to_view_column(data_col)
        changed = False
        for row in range(self.rowCount()):
            while len(self._rows[row]) <= data_col:
                self._rows[row].append("")
            if self._rows[row][data_col]:
                self._rows[row][data_col] = ""
                changed = True

        # Emitir sinal d
        if changed:
            top = self.index(0, view_col)
            bottom = self.index(self.rowCount() - 1, view_col)
            self.dataChanged.emit(top, bottom, [Qt.DisplayRole, Qt.EditRole])
        return True

    @staticmethod
    def _is_string_value(value: str) -> bool:
        return bool(value) and any(char.isalpha() for char in value)

    def transform_column_data(self, data_col: int, transform) -> bool:
        if data_col < 0 or data_col >= self.data_column_count() or self.rowCount() == 0:
            return False

        view_col = self.to_view_column(data_col)
        changed = False
        for row in range(self.rowCount()):
            while len(self._rows[row]) <= data_col:
                self._rows[row].append("")
            value = self._rows[row][data_col]
            if not self._is_string_value(value):
                continue
            new_value = transform(value)
            if new_value != value:
                self._rows[row][data_col] = new_value
                changed = True

 
 
        if changed:
            top_left = self.index(0, view_col)
            bottom_right = self.index(self.rowCount() - 1, view_col)
            self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole, Qt.EditRole])
        return True

    def checked_rows(self) -> list[int]:
        self._sync_row_checks()
        return [i for i, checked in enumerate(self._row_checks) if checked]

 
 
    def toggle_all_row_checks(self) -> None:
        self._sync_row_checks()
        if not self._rows:
            return
        select_all = not all(self._row_checks)
        self._row_checks = [select_all] * len(self._rows)
        top = self.index(0, self.CHECKBOX_COLUMN)
        bottom = self.index(self.rowCount() - 1, self.CHECKBOX_COLUMN)
        self.dataChanged.emit(top, bottom, [Qt.ItemDataRole.CheckStateRole])

    def add_row(self, position: int | None = None) -> None:
        row_count = self.rowCount()
        pos = row_count if position is None else max(0, min(position, row_count))
        width = self.data_column_count()

        self.beginInsertRows(QModelIndex(), pos, pos)
        self._rows.insert(pos, [""] * width)
        self._row_checks.insert(pos, False)
        self.endInsertRows()

    def remove_row(self, row: int) -> bool:
        if row < 0 or row >= self.rowCount():
            return False

        self.beginRemoveRows(QModelIndex(), row, row)
        self._rows.pop(row)
        if row < len(self._row_checks):
            self._row_checks.pop(row)
        self.endRemoveRows()
        return True

    def remove_checked_rows(self) -> int:
        rows = sorted(self.checked_rows(), reverse=True)
        for row in rows:
            self.remove_row(row)
        return len(rows)
    def save(self, path: Path) -> None:
        self._normalize_rows()
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=self._delimiter)
            if self._headers:
                writer.writerow(self._headers)
            writer.writerows(self._rows)

    def transform_all_headers(self, transform) -> None:
        if self.data_column_count() == 0:
            return
        for view_col in range(1, self.columnCount()):
            current = self.headerData(view_col, Qt.Horizontal) or ""
            self.setHeaderData(view_col, Qt.Horizontal, transform(str(current)))
