#!/usr/bin/env python3
"""Visualizador de arquivos CSV com interface PySide6."""

import ctypes.util
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.controllers.main_controller import MainController
from app.models.csv_table_model import CsvTableModel
from app.views.main_window import MainWindow

def _check_qt_system_deps() -> str | None:
    """Verifica bibliotecas exigidas pelo plugin xcb do Qt 6.5+."""
    if ctypes.util.find_library("xcb-cursor") is None:
        return (
            "Dependência do sistema ausente: libxcb-cursor0\n\n"
            "O Qt precisa dessa biblioteca para abrir a janela no Linux (X11).\n"
            "Instale com:\n\n"
            "  sudo apt install libxcb-cursor0\n\n"
            "Depois execute o programa novamente."
        )

        
    return None





def main() -> None:
    if err := _check_qt_system_deps():
        print(err, file=sys.stderr)
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("Visualizador CSV")

    model = CsvTableModel()
    view = MainWindow(model)
    controller = MainController(model, view)

    view.setAcceptDrops(True)
    view.show()

    if len(sys.argv) > 1:
        controller.open_from_argv(Path(sys.argv[1]))

    sys.exit(app.exec())





if __name__ == "__main__":
    main()
