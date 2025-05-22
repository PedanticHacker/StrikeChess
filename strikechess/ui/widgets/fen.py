from __future__ import annotations

from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QLineEdit


class FenEditor(QLineEdit):
    """Editor for Forsyth-Edwards Notation (FEN)."""

    fen_validated: Signal = Signal()

    def __init__(self, game: Game) -> None:
        super().__init__()

        self._game: Game = game

        self.setText(game.fen)
        self.setToolTip(game.fen)

        self.textChanged.connect(self.update_tooltip)
        self.textEdited.connect(self.validate_fen)

    def show_warning(self) -> None:
        """Show red background color to indicate invalid FEN."""
        self.setStyleSheet("background-color: red;")

    def hide_warning(self) -> None:
        """Hide red background color to indicate valid FEN."""
        self.setStyleSheet("")

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Paste FEN from clipboard on mouse double-click."""
        self.selectAll()
        self.paste()

    @Slot(str)
    def update_tooltip(self, fen: str) -> None:
        """Update tooltip whenever `fen` changes."""
        self.setToolTip(fen)

    @Slot(str)
    def validate_fen(self, fen: str) -> None:
        """Validate `fen` to set new board position based on it."""
        try:
            self._game.fen = fen
        except (IndexError, ValueError):
            self.show_warning()
        else:
            if self._game.is_valid():
                self.hide_warning()
                self.fen_validated.emit()
