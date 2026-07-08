from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.csv_table_model import CellMatch, CsvTableModel


class SearchHashDialog(QDialog):
    def __init__(
        self,
        model: CsvTableModel,
        on_select: Callable[[int, int], None],
        parent: QWidget | None = None,
        *,
        initial_hash: str = "",
    ):
        super().__init__(parent)
        self.setWindowTitle("Buscar hash no CSV")
        self.setMinimumSize(520, 360)

        self._model = model
        self._on_select = on_select
        self._matches: list[CellMatch] = []

        self._hash_input = QLineEdit()
        self._hash_input.setPlaceholderText("Cole ou digite o hash")
        self._hash_input.setText(initial_hash)

        self._status_label = QLabel("Informe o hash e clique em Buscar.")
        self._status_label.setStyleSheet("color: #666;")

        self._results_list = QListWidget()
        self._results_list.itemDoubleClicked.connect(self._go_to_selected)

        form = QFormLayout()
        form.addRow("Hash:", self._hash_input)

        search_btn = QPushButton("Buscar")
        search_btn.clicked.connect(self._search)

        go_to_btn = QPushButton("Ir para seleção")
        go_to_btn.clicked.connect(self._go_to_selected)

        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.reject)

        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(search_btn)
        footer.addWidget(go_to_btn)
        footer.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addLayout(form)
        layout.addWidget(self._status_label)
        layout.addWidget(self._results_list)
        layout.addLayout(footer)

        self._hash_input.returnPressed.connect(self._search)
        self._hash_input.setFocus()
        if initial_hash:
            self._search()

    def _search(self) -> None:
        target = self._hash_input.text()
        if not target:
            QMessageBox.warning(self, "Buscar hash no CSV", "Informe o hash.")
            self._hash_input.setFocus()
            return

        self._matches = self._model.find_value(target)
        self._results_list.clear()

        if not self._matches:
            self._status_label.setText("Nenhuma ocorrência encontrada.")
            return

        count = len(self._matches)
        label = "ocorrência" if count == 1 else "ocorrências"
        self._status_label.setText(f"{count} {label} encontrada(s).")

        for match in self._matches:
            item = QListWidgetItem(
                f"Linha {match.row + 1}, coluna \"{match.column_name}\""
            )
            self._results_list.addItem(item)

        self._results_list.setCurrentRow(0)

    def _go_to_selected(self) -> None:
        row = self._results_list.currentRow()
        if row < 0 or row >= len(self._matches):
            QMessageBox.information(
                self,
                "Buscar hash no CSV",
                "Selecione uma ocorrência na lista.",
            )
            return

        match = self._matches[row]
        self._on_select(match.row, match.data_col)
        self.accept()
