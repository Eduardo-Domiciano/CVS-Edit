from pathlib import Path

from PySide6.QtCore import QEvent, QItemSelection, QItemSelectionModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableView,
    QToolTip,
    QVBoxLayout,
    QWidget,
)
from app.constants import SELECTION_BG, SELECTION_FG
from app.models.csv_table_model import CsvTableModel
from app.views.create_csv_dialog import CreateCsvColumnsDialog
from app.views.widgets.bold_selection_delegate import BoldSelectionDelegate
from app.views.widgets.column_highlight_header import ColumnHighlightHeader

class MainWindow(QMainWindow):
    open_requested = Signal()
    save_requested = Signal()
    save_as_requested = Signal()
    create_csv_requested = Signal()
    add_column_requested = Signal()
    remove_column_requested = Signal()
    clear_column_data_requested = Signal()
    add_row_requested = Signal()
    remove_checked_rows_requested = Signal()
    column_lower_requested = Signal()
    column_upper_requested = Signal()
    column_capitalize_requested = Signal()
    headers_lower_requested = Signal()
    headers_capitalize_requested = Signal()
    file_dropped = Signal(object)
    header_clicked = Signal(int)
    cell_clicked = Signal(QModelIndex)
    header_double_clicked = Signal(int)
    def __init__(self, model: CsvTableModel):
        super().__init__()
        self._model = model
        self._highlighted_column: int | None = None
        self._close_handler = None

        # Tirei o bagulho de acertar a janela pela resolução pq aquela merda só deu trabalho.
        self.setWindowTitle("Editor CSV by Eduardo Domiciano")
        self.resize(900, 600)

        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setMouseTracking(True)
        self._table.viewport().setMouseTracking(True)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setItemDelegate(
            BoldSelectionDelegate(self._table, lambda: self._highlighted_column)
        )

        self._table.setStyleSheet(
            "QTableView::item:selected {"
            f" background-color: {SELECTION_BG}; color: {SELECTION_FG}; font-weight: bold; }}"
        )





        self._table.setSortingEnabled(False)
        self._table.setEditTriggers(
            QAbstractItemView.DoubleClicked
            | QAbstractItemView.SelectedClicked
            | QAbstractItemView.EditKeyPressed
        )
        header = ColumnHighlightHeader(self._table)
        self._table.setHorizontalHeader(header)
        self.fit_columns_to_window()
        header.column_clicked.connect(self.header_clicked.emit)
        header.sectionClicked.connect(self.header_clicked.emit)
        header.sectionDoubleClicked.connect(self.header_double_clicked.emit)
        self._table.clicked.connect(self.cell_clicked.emit)
        self._table.viewport().installEventFilter(self)
        self._table.verticalHeader().setDefaultSectionSize(24)


        import_btn = QPushButton("Importar CSV")
        import_btn.clicked.connect(self.open_requested.emit)

        self._add_col_btn = QPushButton("Adicionar coluna")
        self._add_col_btn.clicked.connect(self.add_column_requested.emit)
        self._add_col_btn.setEnabled(False)
        self._remove_col_btn = QPushButton("Remover coluna")
        self._remove_col_btn.clicked.connect(self.remove_column_requested.emit)
        self._remove_col_btn.setEnabled(False)
        self._clear_col_btn = QPushButton("Apagar dados da coluna")
        self._clear_col_btn.clicked.connect(self.clear_column_data_requested.emit)
        self._clear_col_btn.setEnabled(False)
        self._add_row_btn = QPushButton("Adicionar linha")
        self._add_row_btn.clicked.connect(self.add_row_requested.emit)
        self._add_row_btn.setEnabled(False)
        self._remove_checked_rows_btn = QPushButton("Remover linhas marcadas")
        self._remove_checked_rows_btn.clicked.connect(self.remove_checked_rows_requested.emit)
        self._remove_checked_rows_btn.setEnabled(False)
        self._save_btn = QPushButton("Salvar")
        self._save_btn.clicked.connect(self.save_requested.emit)
        self._save_btn.setEnabled(False)

   
   
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 8, 8, 0)
        toolbar_layout.addWidget(import_btn)
        toolbar_layout.addWidget(self._save_btn)
        toolbar_layout.addWidget(self._add_col_btn)
        toolbar_layout.addWidget(self._remove_col_btn)
        toolbar_layout.addWidget(self._clear_col_btn)
        toolbar_layout.addWidget(self._add_row_btn)
        toolbar_layout.addWidget(self._remove_checked_rows_btn)
        toolbar_layout.addStretch()

        placeholder = QLabel(
            'Clique em "Importar CSV" ou arraste um arquivo para exibir a tabela.'
        )
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: #666; font-size: 14px;")



        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(toolbar)
        layout.addWidget(placeholder)
        layout.addWidget(self._table)
        self._table.hide()
        self._placeholder = placeholder
        self.setCentralWidget(container)

        self._build_menu()
        self.setStatusBar(QStatusBar())

    @property
    def model(self) -> CsvTableModel:
        return self._model

    @property
    def highlighted_column(self) -> int | None:
        return self._highlighted_column

    @highlighted_column.setter
    def highlighted_column(self, value: int | None) -> None:
        self._highlighted_column = value

    def set_close_handler(self, handler) -> None:
        self._close_handler = handler
    # botões
    def _build_menu(self) -> None:
        self._save_action = QAction("Salvar", self)
        self._save_action.setShortcut("Ctrl+S")
        self._save_action.triggered.connect(self.save_requested.emit)
        self._save_action.setEnabled(False)

        save_as_action = QAction("Salvar como...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_as_requested.emit)

        open_action = QAction("Abrir CSV...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_requested.emit)

        create_action = QAction("Criar CSV...", self)
        create_action.setShortcut("Ctrl+N")
        create_action.triggered.connect(self.create_csv_requested.emit)

        quit_action = QAction("Sair", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)

        file_menu = self.menuBar().addMenu("Arquivo")
        file_menu.addAction(create_action)
        file_menu.addAction(open_action)
        file_menu.addAction(self._save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)

        add_col_action = QAction("Adicionar coluna", self)
        add_col_action.triggered.connect(self.add_column_requested.emit)

        remove_col_action = QAction("Remover coluna", self)
        remove_col_action.triggered.connect(self.remove_column_requested.emit)

        clear_col_action = QAction("Apagar dados da coluna", self)
        clear_col_action.triggered.connect(self.clear_column_data_requested.emit)

        col_lower_action = QAction("Dados em caixa baixa", self)
        col_lower_action.triggered.connect(self.column_lower_requested.emit)

        col_upper_action = QAction("Dados em caixa alta", self)
        col_upper_action.triggered.connect(self.column_upper_requested.emit)

        col_capitalize_action = QAction("Dados com inicial maiúscula", self)
        col_capitalize_action.triggered.connect(self.column_capitalize_requested.emit)

        col_menu = self.menuBar().addMenu("Colunas")
        col_menu.addAction(add_col_action)
        col_menu.addAction(remove_col_action)
        col_menu.addSeparator()
        col_menu.addAction(clear_col_action)
        col_menu.addSeparator()
        col_menu.addAction(col_lower_action)
        col_menu.addAction(col_upper_action)
        col_menu.addAction(col_capitalize_action)

        add_row_action = QAction("Adicionar linha", self)
        add_row_action.triggered.connect(self.add_row_requested.emit)

        remove_checked_rows_action = QAction("Remover linhas marcadas", self)
        remove_checked_rows_action.triggered.connect(self.remove_checked_rows_requested.emit)

        headers_lower_action = QAction("Títulos em caixa baixa", self)
        headers_lower_action.triggered.connect(self.headers_lower_requested.emit)

        headers_capitalize_action = QAction("Títulos com inicial maiúscula", self)
        headers_capitalize_action.triggered.connect(self.headers_capitalize_requested.emit)

        row_menu = self.menuBar().addMenu("Linhas")
        row_menu.addAction(add_row_action)
        row_menu.addAction(remove_checked_rows_action)
        row_menu.addSeparator()
        row_menu.addAction(headers_lower_action)
        row_menu.addAction(headers_capitalize_action)

    def is_table_visible(self) -> bool:
        return self._table.isVisible()

    def show_table(self) -> None:
        self._placeholder.hide()
        self._table.show()



    def set_edit_actions_enabled(self, enabled: bool) -> None:
        self._add_col_btn.setEnabled(enabled)
        self._remove_col_btn.setEnabled(enabled)
        self._clear_col_btn.setEnabled(enabled)
        self._add_row_btn.setEnabled(enabled)
        self._remove_checked_rows_btn.setEnabled(enabled)
        self._save_btn.setEnabled(enabled)
        self._save_action.setEnabled(enabled)

    def fit_columns_to_window(self) -> None:
        header = self._table.horizontalHeader()
        header.setStretchLastSection(False)
        if self._model.columnCount() == 0:
            return
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 42)
        for col in range(1, self._model.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)

    def refresh_viewport(self) -> None:
        self._table.viewport().update()

    def set_sorting_enabled(self, enabled: bool) -> bool:
        was_sorting = self._table.isSortingEnabled()
        self._table.setSortingEnabled(enabled)
        return was_sorting
    def select_column(self, logical_index: int) -> None:
        self._table.setSelectionBehavior(QAbstractItemView.SelectColumns)
        sm = self._table.selectionModel()
        sm.clearSelection()

        rows = self._model.rowCount()
        if rows > 0:
            top = self._model.index(0, logical_index)
            bottom = self._model.index(rows - 1, logical_index)
            sm.select(
                QItemSelection(top, bottom),
                QItemSelectionModel.SelectionFlag.ClearAndSelect
                | QItemSelectionModel.SelectionFlag.Columns,
            )
        else:
            self._table.selectColumn(logical_index)

    def select_row(self, row: int) -> None:
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.selectRow(row)
    def selected_data_column(self) -> int | None:
        index = self._table.currentIndex()
        if index.isValid():
            return CsvTableModel.to_data_column(index.column())

        selected = self._table.selectionModel().selectedIndexes()
        if selected:
            return CsvTableModel.to_data_column(selected[0].column())

        if self._highlighted_column is not None:
            return CsvTableModel.to_data_column(self._highlighted_column)


        return None

    def selected_row(self) -> int | None:
        index = self._table.currentIndex()
        if index.isValid():
            return index.row()

        selected = self._table.selectionModel().selectedIndexes()
        if selected:
            return selected[0].row()

        return None

    def update_title(self, current_path: Path | None, dirty: bool) -> None:
        if current_path:
            prefix = "* " if dirty else ""
            self.setWindowTitle(f"{prefix}Editor CVS - Arquivo: {current_path.name}")
        else:
            self.setWindowTitle("Editor de CSV by: Eduardo Domiciano")


    def update_status(self, current_path: Path | None, dirty: bool) -> None:
        rows = self._model.rowCount()
        cols = self._model.data_column_count()
        name = current_path.name if current_path else "sem arquivo"
        modified = " — modificado" if dirty else ""
        self.statusBar().showMessage(f"{name} — {rows} linhas, {cols} colunas{modified}")

    def show_status_message(self, message: str, timeout_ms: int = 4000) -> None:
        self.statusBar().showMessage(message, timeout_ms)
    def ask_confirm_discard(self) -> bool:
        reply = QMessageBox.question(
            self,
            "Alterações não salvas",
            "Existem alterações não salvas. Deseja descartá-las?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return reply == QMessageBox.Yes

    def ask_yes_no(self, title: str, message: str) -> bool:
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return reply == QMessageBox.Yes

    def show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)
    def show_warning(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
    def show_critical(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)

    def ask_open_file_path(self) -> Path | None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir arquivo CSV",
            "",
            "Arquivos CSV (*.csv);;Todos os arquivos (*)",
        )
        return Path(path) if path else None

    def ask_save_file_path(
        self, title: str, start_name: str, start_dir: str = ""
    ) -> Path | None:
        start = str(Path(start_dir) / start_name) if start_dir else start_name
        path, _ = QFileDialog.getSaveFileName(
            self,
            title,
            start,
            "Arquivos CSV (*.csv);;Todos os arquivos (*)",
        )
        if not path:
            return None
        target = Path(path)
        if target.suffix.lower() != ".csv":
            target = target.with_suffix(".csv")
        return target

    def ask_column_names(self) -> list[str] | None:
        dialog = CreateCsvColumnsDialog(self)
        if dialog.exec() != CreateCsvColumnsDialog.DialogCode.Accepted:
            return None
        return dialog.column_names()

    def ask_header_text(self, current: str) -> str | None:
        text, ok = QInputDialog.getText(
            self,
            "Editar coluna",
            "Nome da coluna:",
            text=current,
        )
        return text if ok else None

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._table.isVisible():
            self.fit_columns_to_window()
    def closeEvent(self, event) -> None:
        if self._close_handler and not self._close_handler():
            event.ignore()
        else:
            event.accept()
    def eventFilter(self, obj, event) -> bool:
        if obj is self._table.viewport() and event.type() == QEvent.Type.Leave:
            QToolTip.hideText()
        return super().eventFilter(obj, event)
    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith(".csv"):
                event.acceptProposedAction()
    def dropEvent(self, event) -> None:
        path = Path(event.mimeData().urls()[0].toLocalFile())
        self.file_dropped.emit(path)
        event.acceptProposedAction()
