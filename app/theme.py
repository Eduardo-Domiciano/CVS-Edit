from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory

from app.constants import BLACK, DARK_GRAY, LIGHT_GRAY, ORANGE


def apply_theme(app: QApplication) -> None:
    """Aplica só as cores. Fusion é necessário no Linux para o Qt respeitar a paleta."""
    style = QStyleFactory.create("Fusion")
    if style is not None:
        app.setStyle(style)
    app.setPalette(_build_palette())


def _build_palette() -> QPalette:
    orange = QColor(ORANGE)
    black = QColor(BLACK)
    dark = QColor(DARK_GRAY)
    light = QColor(LIGHT_GRAY)
    muted = QColor("#8a8a8a")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, black)
    palette.setColor(QPalette.ColorRole.WindowText, light)
    palette.setColor(QPalette.ColorRole.Base, dark)
    palette.setColor(QPalette.ColorRole.AlternateBase, black)
    palette.setColor(QPalette.ColorRole.ToolTipBase, dark)
    palette.setColor(QPalette.ColorRole.ToolTipText, light)
    palette.setColor(QPalette.ColorRole.Text, light)
    palette.setColor(QPalette.ColorRole.Button, dark)
    palette.setColor(QPalette.ColorRole.ButtonText, light)
    palette.setColor(QPalette.ColorRole.BrightText, orange)
    palette.setColor(QPalette.ColorRole.Highlight, orange)
    palette.setColor(QPalette.ColorRole.HighlightedText, black)
    palette.setColor(QPalette.ColorRole.Link, orange)
    palette.setColor(QPalette.ColorRole.PlaceholderText, muted)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, muted)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, muted)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, muted)
    return palette
