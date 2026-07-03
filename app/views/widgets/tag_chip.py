from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from app.constants import SELECTION_BG, SELECTION_FG


class TagChip(QWidget):
    def __init__(self, text: str, on_remove, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"background-color: {SELECTION_BG}; border: 1px solid {SELECTION_BG};"
            " border-radius: 14px;"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 6, 4)
        layout.setSpacing(4)

        label = QLabel(text)
        label.setStyleSheet(
            f"border: none; background: transparent; color: {SELECTION_FG};"
            " font-weight: bold;"
        )

        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(20, 20)
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.setStyleSheet(
            f"QPushButton {{ border: none; color: {SELECTION_FG}; font-weight: bold; }}"
            "QPushButton:hover { color: #ffcccc; }"
        )
        remove_btn.clicked.connect(lambda *_args: on_remove())

        layout.addWidget(label)
        layout.addWidget(remove_btn)
