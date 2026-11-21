from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QApplication


def elide_name(name: str) -> str:
    """Shorten `name` with ellipsis if too wide for name labels."""
    border_width_in_pixels: int = 1
    label_width_in_pixels: int = 200
    font_metrics: QFontMetrics = QFontMetrics(QApplication.font("QLabel"))
    available_width_in_pixels: int = label_width_in_pixels - 2 * border_width_in_pixels
    return font_metrics.elidedText(name, Qt.TextElideMode.ElideRight, available_width_in_pixels)
