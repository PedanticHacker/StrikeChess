from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplashScreen

from strikechess import __version__
from strikechess.utils import create_svg_icon


class SplashScreen(QSplashScreen):
    """Big logo icon with app name and app version."""

    def __init__(self) -> None:
        super().__init__()

        yellow_color: Qt.GlobalColor = Qt.GlobalColor.yellow
        logo_pixmap: QPixmap = create_svg_icon("logo").pixmap(400, 400)
        center_alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignCenter

        message_font: QFont = self.font()
        message_font.setBold(True)
        message_font.setPixelSize(30)

        self.setFont(message_font)
        self.setPixmap(logo_pixmap)
        self.showMessage(f"StrikeChess\n{__version__}", center_alignment, yellow_color)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Prevent splash screen from closing on mouse press."""
        event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Prevent splash screen from closing on key press."""
        event.accept()

    def show_raised(self) -> Self:
        """Show splash screen and raise it to foreground."""
        self.show()
        self.raise_()

        return self
