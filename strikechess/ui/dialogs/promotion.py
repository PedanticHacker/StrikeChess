from functools import partial

from chess import BISHOP, KNIGHT, QUEEN, ROOK, WHITE
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton

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

        self._player_color: Color = player_color

        self.piece_type: PieceType | None = None

        self.create_buttons()

        self.setWindowTitle(self.tr("Pawn Promotion"))

    def create_buttons(self) -> None:
        """Create one piece-selecting button per promotable piece type."""
        color_prefix: str = "white" if self._player_color == WHITE else "black"

        piece_specs: list[tuple[PieceType, str]] = [
            (QUEEN, "queen"),
            (ROOK, "rook"),
            (BISHOP, "bishop"),
            (KNIGHT, "knight"),
        ]

        horizontal_layout: QHBoxLayout = QHBoxLayout()

        for piece_type, piece_name in piece_specs:
            icon: QIcon = create_svg_icon(f"{color_prefix}-{piece_name}")
            button: QPushButton = _create_button(icon)
            button.clicked.connect(partial(self.select_piece, piece_type))
            horizontal_layout.addWidget(button)

        self.setLayout(horizontal_layout)

    def select_piece(self, piece_type: PieceType) -> None:
        """Set promotion to `piece_type` and accept dialog."""
        self.piece_type = piece_type
        self.accept()
