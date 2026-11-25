from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap


IconSizesInPixels: Final[tuple[int, ...]] = (16, 24, 32)
IconDevicePixelRatios: Final[tuple[float, ...]] = (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0)


def create_colored_icon(color: str) -> QIcon:
    """Create icon in 16 by 16 pixels filled with `color`."""
    pixmap: QPixmap = QPixmap(16, 16)
    pixmap.fill(QColor(color))
    return QIcon(pixmap)


def create_svg_icon(file_name: str) -> QIcon:
    """Create SVG icon based on `file_name`."""
    return QIcon(f":/icons/{file_name}.svg")


def create_tinted_icon(icon: QIcon, color: QColor, disabled_color: QColor) -> QIcon:
    """Copy `icon` in `color`, or in `disabled_color` if disabled."""
    tinted_icon: QIcon = QIcon()

    for size in IconSizesInPixels:
        for device_pixel_ratio in IconDevicePixelRatios:
            pixmap: QPixmap = icon.pixmap(QSize(size, size), device_pixel_ratio)
            tinted_icon.addPixmap(_tinted_pixmap(pixmap, color), QIcon.Mode.Normal)
            tinted_icon.addPixmap(_tinted_pixmap(pixmap, disabled_color), QIcon.Mode.Disabled)

    return tinted_icon


def _tinted_pixmap(pixmap: QPixmap, color: QColor) -> QPixmap:
    """Get copy of `pixmap` with its shape painted in `color`."""
    tinted_pixmap: QPixmap = QPixmap(pixmap)
    painter: QPainter = QPainter(tinted_pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(tinted_pixmap.rect(), color)
    painter.end()
    return tinted_pixmap
