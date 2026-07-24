from chess import Board
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QLineEdit


class FenEditor(QLineEdit):
    """Editor for Forsyth-Edwards Notation (FEN)."""

    fen_validated: ClassVar[Signal] = Signal(str)

    def __init__(self, game: GameService) -> None:
        super().__init__()

        self._game: GameService = game

        self.setText(game.fen)
        self.textEdited.connect(self.validate_fen)
        self.returnPressed.connect(self.apply_fen)

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

    @Slot()
    def apply_fen(self) -> None:
        """Emit edited FEN when Return key is pressed."""
        position: Board | None = self.validated_position(self.text())

        if position is None:
            return

        if position.fen() != self._game.fen:
            self.fen_validated.emit(self.text())

    @Slot(str)
    def validate_fen(self, fen: str) -> None:
        """Validate whether `fen` represents valid position."""
        if self.validated_position(fen) is None:
            self.show_warning()
        else:
            self.hide_warning()

    def validated_position(self, fen: str) -> Board | None:
        """Get position based on `fen`, or None if `fen` is invalid."""
        try:
            position: Board = Board(fen)
        except (IndexError, ValueError):
            return None

        if not position.is_valid():
            return None

        return position
