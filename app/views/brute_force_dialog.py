from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from app.services.hash_service import (
    extract_bcrypt_cost,
    is_bcrypt_hash,
    load_wordlist,
    verify_password,
)


class BruteForceWorker(QThread):
    progress = Signal(int, int)
    match_found = Signal(str)
    finished_ok = Signal(list)
    failed = Signal(str)

    def __init__(
        self,
        target_hash: str,
        passwords: list[str],
        *,
        pepper: str,
        pepper_enabled: bool,
        pepper_position: str,
        cost: int,
        custom_salt: str | None,
        auto_generate_salt: bool,
        use_embedded_salt: bool,
    ):
        super().__init__()
        self._target_hash = target_hash
        self._passwords = passwords
        self._pepper = pepper
        self._pepper_enabled = pepper_enabled
        self._pepper_position = pepper_position
        self._cost = cost
        self._custom_salt = custom_salt
        self._auto_generate_salt = auto_generate_salt
        self._use_embedded_salt = use_embedded_salt
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        matches: list[str] = []
        total = len(self._passwords)
        pepper = self._pepper if self._pepper_enabled else ""

        try:
            for index, password in enumerate(self._passwords, start=1):
                if self._cancelled:
                    self.finished_ok.emit(matches)
                    return

                if verify_password(
                    password,
                    self._target_hash,
                    pepper=pepper,
                    pepper_position=self._pepper_position,
                    cost=self._cost,
                    custom_salt=self._custom_salt,
                    auto_generate_salt=self._auto_generate_salt,
                    use_embedded_salt=self._use_embedded_salt,
                ):
                    matches.append(password)
                    self.match_found.emit(password)

                if index % 25 == 0 or index == total:
                    self.progress.emit(index, total)
        except Exception as error:
            self.failed.emit(str(error))
            return

        self.finished_ok.emit(matches)


class BruteForceDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Brute-force")
        self.setMinimumSize(560, 520)

        self._wordlist_path: Path | None = None
        self._worker: BruteForceWorker | None = None

        self._hash_input = QLineEdit()
        self._hash_input.setPlaceholderText("Cole o hash bcrypt alvo")

        self._wordlist_input = QLineEdit()
        self._wordlist_input.setReadOnly(True)
        self._wordlist_input.setPlaceholderText("Nenhuma wordlist selecionada")

        browse_btn = QPushButton("Selecionar...")
        browse_btn.clicked.connect(self._browse_wordlist)

        wordlist_row = QWidget()
        wordlist_layout = QHBoxLayout(wordlist_row)
        wordlist_layout.setContentsMargins(0, 0, 0, 0)
        wordlist_layout.addWidget(self._wordlist_input)
        wordlist_layout.addWidget(browse_btn)

        self._wordlist_info = QLabel("0 senhas carregadas")
        self._wordlist_info.setStyleSheet("color: #666;")

        salt_group = QGroupBox("Salt")
        salt_layout = QFormLayout(salt_group)

        self._use_embedded_salt = QCheckBox("Usar salt embutido no hash (automático)")
        self._use_embedded_salt.setChecked(True)
        self._use_embedded_salt.setToolTip(
            "Recomendado para hashes bcrypt. O salt é lido do próprio hash alvo."
        )
        self._use_embedded_salt.toggled.connect(self._on_salt_mode_changed)

        self._salt_input = QLineEdit()
        self._salt_input.setPlaceholderText("Salt personalizado")
        self._salt_input.setEnabled(False)

        self._no_auto_salt = QCheckBox("Não gerar salt automaticamente")
        self._no_auto_salt.setEnabled(False)

        self._cost_input = QSpinBox()
        self._cost_input.setRange(4, 31)
        self._cost_input.setValue(12)
        self._cost_input.setEnabled(False)

        salt_layout.addRow("", self._use_embedded_salt)
        salt_layout.addRow("Salt:", self._salt_input)
        salt_layout.addRow("", self._no_auto_salt)
        salt_layout.addRow("Custo:", self._cost_input)

        pepper_group = QGroupBox("Pepper")
        pepper_layout = QFormLayout(pepper_group)

        self._use_pepper = QCheckBox("Aplicar pepper nas senhas da wordlist")
        self._use_pepper.toggled.connect(self._on_pepper_toggled)

        self._pepper_input = QLineEdit()
        self._pepper_input.setPlaceholderText("Valor do pepper")
        self._pepper_input.setEnabled(False)

        self._pepper_position = QComboBox()
        self._pepper_position.addItems(["Depois da senha", "Antes da senha", "Antes e depois"])
        self._pepper_position.setEnabled(False)

        pepper_layout.addRow("", self._use_pepper)
        pepper_layout.addRow("Pepper:", self._pepper_input)
        pepper_layout.addRow("Posição:", self._pepper_position)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)

        self._status_label = QLabel("Configure o hash alvo e a wordlist para iniciar.")
        self._status_label.setStyleSheet("color: #666;")

        self._results_list = QListWidget()

        form = QFormLayout()
        form.addRow("Hash alvo:", self._hash_input)
        form.addRow("Wordlist:", wordlist_row)

        self._start_btn = QPushButton("Iniciar")
        self._start_btn.clicked.connect(self._start)

        self._cancel_btn = QPushButton("Cancelar")
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel)

        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.reject)

        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(self._start_btn)
        footer.addWidget(self._cancel_btn)
        footer.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addLayout(form)
        layout.addWidget(self._wordlist_info)
        layout.addWidget(salt_group)
        layout.addWidget(pepper_group)
        layout.addWidget(self._status_label)
        layout.addWidget(self._progress)
        layout.addWidget(QLabel("Senhas encontradas:"))
        layout.addWidget(self._results_list)
        layout.addLayout(footer)

        self._hash_input.textChanged.connect(self._on_hash_changed)
        self._hash_input.setFocus()

    def _on_hash_changed(self, text: str) -> None:
        cost = extract_bcrypt_cost(text)
        if cost is not None:
            self._cost_input.setValue(cost)
            self._use_embedded_salt.setChecked(True)

    def _on_salt_mode_changed(self, use_embedded: bool) -> None:
        manual = not use_embedded
        self._salt_input.setEnabled(manual)
        self._no_auto_salt.setEnabled(manual)
        self._cost_input.setEnabled(manual)

    def _on_pepper_toggled(self, enabled: bool) -> None:
        self._pepper_input.setEnabled(enabled)
        self._pepper_position.setEnabled(enabled)

    def _browse_wordlist(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar wordlist",
            "",
            "Arquivos de texto (*.txt);;Todos os arquivos (*)",
        )
        if not path:
            return

        self._wordlist_path = Path(path)
        self._wordlist_input.setText(path)
        try:
            count = len(load_wordlist(self._wordlist_path))
        except OSError as error:
            QMessageBox.critical(self, "Brute-force", f"Não foi possível ler a wordlist:\n{error}")
            self._wordlist_path = None
            self._wordlist_input.clear()
            self._wordlist_info.setText("0 senhas carregadas")
            return

        self._wordlist_info.setText(f"{count} senha(s) carregada(s)")

    def _pepper_position_key(self) -> str:
        index = self._pepper_position.currentIndex()
        if index == 1:
            return "before"
        if index == 2:
            return "both"
        return "after"

    def _set_running(self, running: bool) -> None:
        self._start_btn.setEnabled(not running)
        self._cancel_btn.setEnabled(running)
        self._hash_input.setEnabled(not running)
        self._use_embedded_salt.setEnabled(not running)
        self._salt_input.setEnabled(not running and not self._use_embedded_salt.isChecked())
        self._no_auto_salt.setEnabled(not running and not self._use_embedded_salt.isChecked())
        self._cost_input.setEnabled(not running and not self._use_embedded_salt.isChecked())
        self._use_pepper.setEnabled(not running)
        self._pepper_input.setEnabled(not running and self._use_pepper.isChecked())
        self._pepper_position.setEnabled(not running and self._use_pepper.isChecked())

    def _start(self) -> None:
        target_hash = self._hash_input.text().strip()
        if not target_hash:
            QMessageBox.warning(self, "Brute-force", "Informe o hash alvo.")
            self._hash_input.setFocus()
            return

        if self._wordlist_path is None:
            QMessageBox.warning(self, "Brute-force", "Selecione uma wordlist.")
            return

        try:
            passwords = load_wordlist(self._wordlist_path)
        except OSError as error:
            QMessageBox.critical(self, "Brute-force", f"Não foi possível ler a wordlist:\n{error}")
            return

        if not passwords:
            QMessageBox.warning(self, "Brute-force", "A wordlist não contém senhas válidas.")
            return

        use_embedded = self._use_embedded_salt.isChecked()
        if use_embedded and not is_bcrypt_hash(target_hash):
            QMessageBox.warning(
                self,
                "Brute-force",
                "O hash alvo não parece ser bcrypt. "
                "Desmarque \"Usar salt embutido no hash\" para comparar com salt manual.",
            )
            return

        self._results_list.clear()
        self._progress.setValue(0)
        self._status_label.setText("Testando senhas...")
        self._set_running(True)

        self._worker = BruteForceWorker(
            target_hash,
            passwords,
            pepper=self._pepper_input.text(),
            pepper_enabled=self._use_pepper.isChecked(),
            pepper_position=self._pepper_position_key(),
            cost=self._cost_input.value(),
            custom_salt=self._salt_input.text().strip() or None,
            auto_generate_salt=not self._no_auto_salt.isChecked(),
            use_embedded_salt=use_embedded,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.match_found.connect(self._on_match_found)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _cancel(self) -> None:
        if self._worker is not None:
            self._worker.cancel()

    def _on_progress(self, current: int, total: int) -> None:
        if total > 0:
            self._progress.setValue(int((current / total) * 100))
        self._status_label.setText(f"Testando {current} de {total} senhas...")

    def _on_match_found(self, password: str) -> None:
        self._results_list.addItem(password)

    def _on_finished(self, matches: list[str]) -> None:
        self._set_running(False)
        self._progress.setValue(100)
        if matches:
            self._status_label.setText(
                f"Concluído — {len(matches)} senha(s) encontrada(s)."
            )
        else:
            self._status_label.setText("Concluído — nenhuma senha correspondeu ao hash.")
        self._worker = None

    def _on_failed(self, message: str) -> None:
        self._set_running(False)
        self._worker = None
        QMessageBox.critical(self, "Brute-force", message)
        self._status_label.setText("Falha ao executar o brute-force.")

    def closeEvent(self, event) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(3000)
        super().closeEvent(event)
