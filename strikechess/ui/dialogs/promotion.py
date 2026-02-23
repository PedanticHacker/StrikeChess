from chess import BISHOP, KNIGHT, QUEEN, ROOK, WHITE
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton

from strikechess.utils import create_button, create_svg_icon


class PromotionDialog(QDialog):
    """Dialog with buttons for selecting promotion piece type."""

    def __init__(self, parent: QWidget | None, player_color: Color) -> None:
        super().__init__(parent)

        self._player_color: Color = player_color

        self.piece_type: PieceType | None = None

        self.create_buttons()
        self.set_horizontal_layout()
        self.connect_signals_to_slots()

        self.setWindowTitle(self.tr("Pawn Promotion"))

    def create_buttons(self) -> None:
        """Create buttons based on player's color."""
        if self._player_color == WHITE:
            self.queen_button: QPushButton = create_button(create_svg_icon("white-queen"))
            self.rook_button: QPushButton = create_button(create_svg_icon("white-rook"))
            self.bishop_button: QPushButton = create_button(create_svg_icon("white-bishop"))
            self.knight_button: QPushButton = create_button(create_svg_icon("white-knight"))
        else:
            self.queen_button = create_button(create_svg_icon("black-queen"))
            self.rook_button = create_button(create_svg_icon("black-rook"))
            self.bishop_button = create_button(create_svg_icon("black-bishop"))
            self.knight_button = create_button(create_svg_icon("black-knight"))

    def set_horizontal_layout(self) -> None:
        """Add buttons to horizontal layout."""
        horizontal_layout: QHBoxLayout = QHBoxLayout()
        horizontal_layout.addWidget(self.queen_button)
        horizontal_layout.addWidget(self.rook_button)
        horizontal_layout.addWidget(self.bishop_button)
        horizontal_layout.addWidget(self.knight_button)

        self.setLayout(horizontal_layout)

    def connect_signals_to_slots(self) -> None:
        """Connect button signals to corresponding slot methods."""
        self.queen_button.clicked.connect(self.select_queen)
        self.rook_button.clicked.connect(self.select_rook)
        self.bishop_button.clicked.connect(self.select_bishop)
        self.knight_button.clicked.connect(self.select_knight)

    def select_queen(self) -> None:
        """Set promotion piece type to queen."""
        self.piece_type = QUEEN
        self.accept()

    def select_rook(self) -> None:
        """Set promotion piece type to rook."""
        self.piece_type = ROOK
        self.accept()

    def select_bishop(self) -> None:
        """Set promotion piece type to bishop."""
        self.piece_type = BISHOP
        self.accept()

    def select_knight(self) -> None:
        """Set promotion piece type to knight."""
        self.piece_type = KNIGHT
        self.accept()
