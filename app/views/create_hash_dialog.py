import bcrypt
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

_BCRYPT_SALT_CHARS = "./ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def _to_bcrypt_salt_component(text: str) -> str:
    chars = []
    for char in text:
        if char in _BCRYPT_SALT_CHARS:
            chars.append(char)
        else:
            chars.append(_BCRYPT_SALT_CHARS[ord(char) % len(_BCRYPT_SALT_CHARS)])
        if len(chars) == 22:
            break
    while len(chars) < 22:
        chars.append(".")
    return "".join(chars)


def create_password_hash(password: str, cost: int, custom_salt: str | None = None) -> str:
    if custom_salt:
        salt_component = _to_bcrypt_salt_component(custom_salt)
        salt = f"$2b${cost:02d}${salt_component}".encode()
    else:
        salt = bcrypt.gensalt(rounds=cost)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


class CreateHashDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Criar Hash")
        self.setMinimumWidth(520)

        self._password_input = QLineEdit()
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_input.setPlaceholderText("Digite a senha")

        self._cost_input = QSpinBox()
        self._cost_input.setRange(4, 31)
        self._cost_input.setValue(12)
        self._cost_input.valueChanged.connect(self._update_cost_hint)

        self._cost_hint = QLabel("2^12")
        self._cost_hint.setStyleSheet("color: #666;")

        cost_row = QWidget()
        cost_layout = QHBoxLayout(cost_row)
        cost_layout.setContentsMargins(0, 0, 0, 0)
        cost_layout.addWidget(self._cost_input)
        cost_layout.addWidget(self._cost_hint)
        cost_layout.addStretch()

        self._salt_input = QLineEdit()
        self._salt_input.setPlaceholderText("Opcional — deixe vazio para gerar automaticamente")

        self._hash_output = QLineEdit()
        self._hash_output.setReadOnly(True)
        self._hash_output.setPlaceholderText("O hash aparecerá aqui")

        form = QFormLayout()
        form.setSpacing(12)
        form.addRow("Senha:", self._password_input)
        form.addRow("Custo de fatoração:", cost_row)
        form.addRow("Salt:", self._salt_input)
        form.addRow("Hash final:", self._hash_output)

        generate_btn = QPushButton("Gerar hash")
        generate_btn.clicked.connect(self._generate_hash)

        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.reject)

        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(generate_btn)
        footer.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.addLayout(form)
        layout.addLayout(footer)

        self._password_input.setFocus()

    def _update_cost_hint(self, value: int) -> None:
        self._cost_hint.setText(f"2^{value}")

    def _generate_hash(self) -> None:
        password = self._password_input.text()
        if not password:
            QMessageBox.warning(self, "Criar Hash", "Informe a senha.")
            self._password_input.setFocus()
            return

        salt_text = self._salt_input.text().strip()
        try:
            hashed = create_password_hash(
                password,
                self._cost_input.value(),
                salt_text or None,
            )
        except ValueError as error:
            QMessageBox.warning(self, "Criar Hash", str(error))
            return

        self._hash_output.setText(hashed)
