from functools import partial

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton
from chess import BISHOP, COLOR_NAMES, KNIGHT, piece_name, QUEEN, ROOK

from strikechess.utils import create_svg_icon


def _create_button(icon: QIcon) -> QPushButton:
    """Create button with `icon`."""
    button: QPushButton = QPushButton()
    button.setIcon(icon)
    button.setIconSize(QSize(50, 50))
    return button


class PromotionDialog(QDialog):
    """Dialog with buttons for selecting promotion piece type."""

    def __init__(self, parent: QWidget | None, player_color: Color) -> None:
        super().__init__(parent)

        self.piece_type: PieceType | None = None

        self._create_buttons(player_color)

        self.setWindowTitle(self.tr("Pawn Promotion"))

    def select_piece_type(self, piece_type: PieceType) -> None:
        """Set promotion piece type to `piece_type`."""
        self.piece_type = piece_type
        self.accept()

    def _create_buttons(self, player_color: Color) -> None:
        """Create buttons for `player_color` in horizontal layout."""
        color_name: str = COLOR_NAMES[player_color]
        horizontal_layout: QHBoxLayout = QHBoxLayout()

        for piece_type in (QUEEN, ROOK, BISHOP, KNIGHT):
            icon: QIcon = create_svg_icon(f"{color_name}-{piece_name(piece_type)}")
            button: QPushButton = _create_button(icon)
            horizontal_layout.addWidget(button)
            button.clicked.connect(partial(self.select_piece_type, piece_type))

        self.setLayout(horizontal_layout)
