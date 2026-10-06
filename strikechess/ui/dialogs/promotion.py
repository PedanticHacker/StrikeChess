from PySide6.QtCore import QSize
from chess import BISHOP, KNIGHT, QUEEN, ROOK, WHITE
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

        self._create_buttons()
        self._set_horizontal_layout()
        self._connect_signals_to_slots()

        self.setWindowTitle(self.tr("Pawn Promotion"))

    def select_queen(self) -> None:
        """Set promotion piece type to queen."""
        self.accept()
        self.piece_type = QUEEN

    def select_rook(self) -> None:
        """Set promotion piece type to rook."""
        self.accept()
        self.piece_type = ROOK

    def select_bishop(self) -> None:
        """Set promotion piece type to bishop."""
        self.accept()
        self.piece_type = BISHOP

    def select_knight(self) -> None:
        """Set promotion piece type to knight."""
        self.accept()
        self.piece_type = KNIGHT

    def _create_buttons(self) -> None:
        """Create buttons based on player's color."""
        if self._player_color == WHITE:
            self.rook_button: QPushButton = _create_button(create_svg_icon("white-rook"))
            self.queen_button: QPushButton = _create_button(create_svg_icon("white-queen"))
            self.bishop_button: QPushButton = _create_button(create_svg_icon("white-bishop"))
            self.knight_button: QPushButton = _create_button(create_svg_icon("white-knight"))
        else:
            self.rook_button = _create_button(create_svg_icon("black-rook"))
            self.queen_button = _create_button(create_svg_icon("black-queen"))
            self.bishop_button = _create_button(create_svg_icon("black-bishop"))
            self.knight_button = _create_button(create_svg_icon("black-knight"))

    def _set_horizontal_layout(self) -> None:
        """Add buttons to horizontal layout."""
        horizontal_layout: QHBoxLayout = QHBoxLayout()
        horizontal_layout.addWidget(self.queen_button)
        horizontal_layout.addWidget(self.rook_button)
        horizontal_layout.addWidget(self.bishop_button)
        horizontal_layout.addWidget(self.knight_button)

        self.setLayout(horizontal_layout)

    def _connect_signals_to_slots(self) -> None:
        """Connect button signals to corresponding slot methods."""
        self.rook_button.clicked.connect(self.select_rook)
        self.queen_button.clicked.connect(self.select_queen)
        self.bishop_button.clicked.connect(self.select_bishop)
        self.knight_button.clicked.connect(self.select_knight)
