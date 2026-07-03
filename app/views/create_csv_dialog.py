from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from app.views.widgets.tag_chip import TagChip






class CreateCsvColumnsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Quais os nomes das colunas")
        self.setMinimumWidth(480)
        self._tags: list[str] = []

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        hint = QLabel("Digite um nome e pressione Enter para adicionar.")
        hint.setStyleSheet("color: #666;")
        layout.addWidget(hint)
        self._input = QLineEdit()
        self._input.setPlaceholderText("Nome da coluna")
        self._input.returnPressed.connect(self._add_tag)
        layout.addWidget(self._input)
        self._tags_area = QWidget()
        self._tags_layout = QVBoxLayout(self._tags_area)
        self._tags_layout.setContentsMargins(0, 0, 0, 0)
        self._tags_layout.setSpacing(6)
        self._tags_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll = QScrollArea()
        scroll.setWidget(self._tags_area)
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(100)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        layout.addWidget(scroll)
        footer = QHBoxLayout()
        footer.addStretch()
        self._create_btn = QPushButton("Criar")
        self._create_btn.setDefault(False)
        self._create_btn.setAutoDefault(False)
        self._create_btn.clicked.connect(self._on_create)
        footer.addWidget(self._create_btn)
        layout.addLayout(footer)


        self._input.setFocus()
    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._input.hasFocus():
                self._add_tag()
                event.accept()
                return
        super().keyPressEvent(event)


    def _add_tag(self) -> None:
        name = self._input.text().strip()
        if not name:
            return
        if name in self._tags:
            self._input.clear()
            return
        self._tags.append(name)
        self._input.clear()
        self._rebuild_tags()
    def _remove_tag(self, name: str) -> None:
        if name in self._tags:
            self._tags.remove(name)
            self._rebuild_tags()
    def _rebuild_tags(self) -> None:
        while self._tags_layout.count():
            item = self._tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._tags:
            return

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        per_row = 3
        for i, tag in enumerate(self._tags):
            if i > 0 and i % per_row == 0:
                self._tags_layout.addWidget(row_widget)
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(6)
                row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            row_layout.addWidget(TagChip(tag, lambda t=tag: self._remove_tag(t)))
        row_layout.addStretch()
        self._tags_layout.addWidget(row_widget)
    def _on_create(self) -> None:
        pending = self._input.text().strip()
        if pending and pending not in self._tags:
            self._tags.append(pending)
            self._input.clear()
            self._rebuild_tags()
        if not self._tags:
            QMessageBox.warning(self, "Criar CSV", "Adicione pelo menos uma coluna.")
            return
        self.accept()

    def column_names(self) -> list[str]:
        return list(self._tags)
