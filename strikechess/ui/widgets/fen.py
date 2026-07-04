from chess import Board
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QLineEdit


class FenEditor(QLineEdit):
    """Editor for Forsyth-Edwards Notation (FEN)."""

    fen_validated: ClassVar[Signal] = Signal()

    def __init__(self, game: GameService) -> None:
        super().__init__()

        self._game: GameService = game

        self.setText(game.fen)
        self.textEdited.connect(self.validate_fen)

    def show_warning(self) -> None:
        """Show red background color to indicate invalid FEN."""
        self.setProperty("invalid", True)
        self.style().polish(self)

    def hide_warning(self) -> None:
        """Hide red background color to indicate valid FEN."""
        self.setProperty("invalid", False)
        self.style().polish(self)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Paste FEN from clipboard on mouse double-click."""
        self.selectAll()
        self.paste()

    @Slot(str)
    def validate_fen(self, fen: str) -> None:
        """Validate whether `fen` represents valid position."""
        try:
            position: Board = Board(fen)
        except (IndexError, ValueError):
            self.show_warning()
            return

        if not position.is_valid():
            self.show_warning()
            return

        self.hide_warning()

        if position.fen() != self._game.fen:
            self._game.fen = fen
            self.fen_validated.emit()
