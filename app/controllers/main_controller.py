import csv
from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt

from app.models.csv_table_model import CsvTableModel
from app.views.main_window import MainWindow

class MainController:
    def __init__(self, model: CsvTableModel, view: MainWindow):
        self._model = model
        self._view = view
        self._current_path: Path | None = None
        self._dirty = False

        self._connect_model_signals()
        self._connect_view_signals()
        self._view.set_close_handler(self.confirm_discard)



    def _connect_model_signals(self) -> None:
        self._model.dataChanged.connect(self._on_model_changed)
        self._model.headerDataChanged.connect(self._on_model_changed)
        self._model.modelReset.connect(self._clear_dirty)
        self._model.columnsInserted.connect(self._mark_dirty)
        self._model.columnsRemoved.connect(self._mark_dirty)
        self._model.rowsInserted.connect(self._mark_dirty)
        self._model.rowsRemoved.connect(self._mark_dirty)
    def _connect_view_signals(self) -> None:
        self._view.open_requested.connect(self.open_dialog)
        self._view.save_requested.connect(self.save)
        self._view.save_as_requested.connect(self.save_as)
        self._view.create_csv_requested.connect(self.create_csv)
        self._view.add_column_requested.connect(self.add_column)
        self._view.remove_column_requested.connect(self.remove_column)
        self._view.clear_column_data_requested.connect(self.clear_column_data)
        self._view.add_row_requested.connect(self.add_row)
        self._view.remove_checked_rows_requested.connect(self.remove_checked_rows)
        self._view.column_lower_requested.connect(self.column_values_to_lower)
        self._view.column_upper_requested.connect(self.column_values_to_upper)
        self._view.column_capitalize_requested.connect(self.column_values_to_capitalize)
        self._view.headers_lower_requested.connect(self.headers_to_lower)
        self._view.headers_capitalize_requested.connect(self.headers_to_capitalize)
        self._view.create_hash_requested.connect(self.create_hash)
        self._view.search_hash_requested.connect(self.search_hash)
        self._view.file_dropped.connect(self.open_file)
        self._view.header_clicked.connect(self.on_header_clicked)
        self._view.cell_clicked.connect(self.on_cell_clicked)
        self._view.header_double_clicked.connect(self.edit_header)



    def open_from_argv(self, path: Path) -> None:
        self.open_file(path)





    def _on_model_changed(
        self, top_left: QModelIndex = QModelIndex(), bottom_right: QModelIndex = QModelIndex(), *_args
    ) -> None:
        if not self._view.is_table_visible():
            return
        if isinstance(top_left, QModelIndex) and top_left.isValid():
            if CsvTableModel.is_checkbox_column(top_left.column()):
                if not bottom_right.isValid() or CsvTableModel.is_checkbox_column(
                    bottom_right.column()
                ):
                    return
        self._mark_dirty()

    def _mark_dirty(self, *_args) -> None:
        self._dirty = True
        self._refresh_ui_state()



    def _clear_dirty(self, *_args) -> None:
        self._dirty = False
        self._refresh_ui_state()


    def _refresh_ui_state(self) -> None:
        self._view.update_title(self._current_path, self._dirty)
        self._view.update_status(self._current_path, self._dirty)
    def confirm_discard(self) -> bool:
        if not self._dirty:
            return True
        return self._view.ask_confirm_discard()



    def on_header_clicked(self, logical_index: int) -> None:
        if CsvTableModel.is_checkbox_column(logical_index):
            self._model.toggle_all_row_checks()
            self._view.highlighted_column = None
            self._view.refresh_viewport()
            return





        self._view.highlighted_column = logical_index
        self._view.select_column(logical_index)
        self._view.refresh_viewport()




    def on_cell_clicked(self, index: QModelIndex) -> None:
        if not index.isValid():
            return
        if CsvTableModel.is_checkbox_column(index.column()):
            return

        self._view.highlighted_column = None
        self._view.select_row(index.row())
        self._view.refresh_viewport()

    def edit_header(self, logical_index: int) -> None:
        if CsvTableModel.is_checkbox_column(logical_index):
            return


        current = self._model.headerData(logical_index, Qt.Horizontal) or ""
        text = self._view.ask_header_text(str(current))
        if text is not None:
            self._model.setHeaderData(logical_index, Qt.Horizontal, text)
    def save(self) -> None:
        if not self._view.is_table_visible():
            return
        if self._current_path is None:
            self.save_as()
            return
        self._write_file(self._current_path)


    def save_as(self) -> None:
        if not self._view.is_table_visible():
            return

        start_dir = str(self._current_path.parent) if self._current_path else ""
        start_name = self._current_path.name if self._current_path else "dados.csv"
        target = self._view.ask_save_file_path(
            "Salvar arquivo CSV", start_name, start_dir
        )
        if target:
            self._write_file(target)
            self._current_path = target

    def _write_file(self, path: Path) -> None:
        try:
            self._model.save(path)
        except OSError as e:
            self._view.show_critical(
                "Erro", f"Não foi possível salvar o arquivo:\n{e}"
            )
            return

        self._clear_dirty()
        self._view.show_status_message(f"Salvo em {path.name}")



    def add_row(self) -> None:
        row = self._view.selected_row()
        position = (row + 1) if row is not None else self._model.rowCount()
        self._model.add_row(position)
        self._refresh_ui_state()


    def remove_checked_rows(self) -> None:
        if self._model.rowCount() == 0:
            return

        checked = self._model.checked_rows()
        if not checked:
            self._view.show_info(
                "Remover linhas marcadas",
                "Marque as linhas que deseja remover usando as caixas de seleção.",
            )
            return

        if not self._view.ask_yes_no(
            "Remover linhas marcadas",
            f"Remover {len(checked)} linha(s) marcada(s)?",
        ):
            return

        self._model.remove_checked_rows()
        self._view.refresh_viewport()
        self._refresh_ui_state()



    def add_column(self) -> None:
        was_sorting = self._view.set_sorting_enabled(False)

        data_col = self._view.selected_data_column()
        position = (
            (data_col + 1) if data_col is not None else self._model.data_column_count()
        )
        self._model.add_column(position)

        self._view.set_sorting_enabled(was_sorting)
        self._view.fit_columns_to_window()
        self._refresh_ui_state()



    def clear_column_data(self) -> None:
        if self._model.data_column_count() == 0:
            return

        col = self._view.selected_data_column()
        if col is None:
            self._view.show_info(
                "Apagar dados da coluna",
                "Selecione uma célula ou clique no cabeçalho da coluna desejada.",
            )
            return

        if self._model.rowCount() == 0:
            return

        header_name = self._model.headerData(
            CsvTableModel.to_view_column(col), Qt.Horizontal
        )
        if not self._view.ask_yes_no(
            "Apagar dados da coluna",
            f'Apagar todos os dados da coluna "{header_name}"?\n'
            "O título da coluna será mantido.",
        ):
            return

        self._model.clear_column_data(col)
        self._view.refresh_viewport()
        self._refresh_ui_state()
    def _transform_column_values(self, transform, action_name: str) -> None:
        if self._model.data_column_count() == 0:
            return

        col = self._view.selected_data_column()
        if col is None:
            self._view.show_info(
                action_name,
                "Selecione uma célula ou clique no cabeçalho da coluna desejada.",
            )
            return

        if self._model.rowCount() == 0:
            return

        if not self._model.transform_column_data(col, transform):
            self._view.show_info(
                action_name,
                "Não há valores de texto para alterar nesta coluna.",
            )
            return

        self._view.refresh_viewport()
        self._refresh_ui_state()



    def column_values_to_lower(self) -> None:
        self._transform_column_values(str.lower, "Dados em caixa baixa")

    def column_values_to_upper(self) -> None:
        self._transform_column_values(str.upper, "Dados em caixa alta")

    def column_values_to_capitalize(self) -> None:
        self._transform_column_values(str.capitalize, "Dados com inicial maiúscula")


    def remove_column(self) -> None:
        if self._model.data_column_count() == 0:
            return

        col = self._view.selected_data_column()
        if col is None:
            self._view.show_info(
                "Remover coluna",
                "Selecione uma célula ou clique no cabeçalho da coluna que deseja remover.",
            )
            return



        header_name = self._model.headerData(
            CsvTableModel.to_view_column(col), Qt.Horizontal
        )
        if not self._view.ask_yes_no(
            "Remover coluna",
            f'Remover a coluna "{header_name}"?',
        ):
            return



        was_sorting = self._view.set_sorting_enabled(False)
        self._model.remove_column(col)
        self._view.set_sorting_enabled(was_sorting)
        self._view.fit_columns_to_window()
        self._refresh_ui_state()
    def headers_to_lower(self) -> None:
        if not self._view.is_table_visible() or self._model.data_column_count() == 0:
            return
        self._model.transform_all_headers(str.lower)
        self._view.refresh_viewport()
    def headers_to_capitalize(self) -> None:
        if not self._view.is_table_visible() or self._model.data_column_count() == 0:
            return
        self._model.transform_all_headers(str.capitalize)
        self._view.refresh_viewport()

    def create_hash(self) -> None:
        self._view.show_create_hash_dialog()

    def search_hash(self, initial_hash: str = "") -> None:
        if not self._view.is_table_visible():
            self._view.show_info(
                "Buscar hash no CSV",
                "Abra um arquivo CSV antes de buscar.",
            )
            return

        self._view.show_search_hash_dialog(
            initial_hash,
            self._go_to_hash_match,
        )

    def _go_to_hash_match(self, row: int, data_col: int) -> None:
        self._view.select_cell(row, data_col)
        header = self._model.headerData(
            CsvTableModel.to_view_column(data_col), Qt.Horizontal
        )
        self._view.show_status_message(
            f"Hash encontrado na linha {row + 1}, coluna \"{header}\""
        )

    def open_dialog(self) -> None:
        path = self._view.ask_open_file_path()
        if path:
            self.open_file(path)
    def create_csv(self) -> None:
        if not self.confirm_discard():
            return

        columns = self._view.ask_column_names()
        if columns is None:
            return

        target = self._view.ask_save_file_path("Criar arquivo CSV", "novo.csv")
        if target is None:
            return

        try:
            with target.open("w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(columns)
        except OSError as e:
            self._view.show_critical(
                "Erro", f"Não foi possível criar o arquivo:\n{e}"
            )
            return

        self.open_file(target, confirm=False)
    def open_file(self, path: Path, *, confirm: bool = True) -> None:
        if confirm and not self.confirm_discard():
            return


        if not path.exists():
            self._view.show_warning("Erro", f"Arquivo não encontrado:\n{path}")
            return

        try:
            self._model.load(path)
        except OSError as e:
            self._view.show_critical(
                "Erro", f"Não foi possível ler o arquivo:\n{e}"
            )
            return
        except csv.Error as e:
            self._view.show_critical("Erro", f"Arquivo CSV inválido:\n{e}")
            return


        self._current_path = path
        self._view.highlighted_column = None
        self._view.show_table()
        self._view.set_edit_actions_enabled(True)
        self._clear_dirty()
        self._view.fit_columns_to_window()
        self._refresh_ui_state()
