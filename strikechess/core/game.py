from __future__ import annotations

from contextlib import suppress
from typing import ClassVar, Iterator

from chess import BB_SQUARES, BLACK, WHITE, Board, IllegalMoveError, Move
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog

from strikechess.ui.dialogs import PromotionDialog
from strikechess.utils import setting_value


class Game(QObject):
    """Management of game state, logic, and events."""

    move_played: ClassVar[Signal] = Signal(Move)
    sound_effect_played: ClassVar[Signal] = Signal(Move)

    def __init__(self) -> None:
        super().__init__()

        self.board: Board = Board()

        self.moves: list[str] = []
        self.positions: list[Board] = []
        self.arrow: list[tuple[Square, Square]] = []

        self.move_index: int = -1
        self.origin_square: Square | None = None
        self.target_square: Square | None = None
        self.player_lost_on_time: Color | None = None

        self.is_history: bool = False
        self.has_time_expired: bool = False

        self.reset_selected_squares()

    @property
    def fen(self) -> str:
        """Get current position in FEN format."""
        return self.board.fen()

    @fen.setter
    def fen(self, value) -> None:
        """Set new position in FEN format based on `value`."""
        self.board.set_fen(value)
        self._initialize_state()

    @property
    def check(self) -> Square | None:
        """Get square of king in check."""
        if self.board.is_check():
            return self.board.king(self.board.turn)
        return None

    @property
    def result(self) -> str:
        """Get result of current game."""
        result: str = "*"

        if self.has_time_expired:
            if self.player_lost_on_time == BLACK:
                return "White wins on time"
            elif self.player_lost_on_time == WHITE:
                return "Black wins on time"
        else:
            result = self.board.result(claim_draw=True)

        result_descriptions: dict[str, str] = {
            "1/2-1/2": "Draw",
            "0-1": "Black wins",
            "1-0": "White wins",
            "*": "Undetermined game",
        }
        return result_descriptions[result]

    @property
    def turn(self) -> bool:
        """Return True if White is on turn."""
        return self.board.turn

    def _initialize_state(self) -> None:
        """Clear game history and set squares to initial value."""
        self.move_index = -1

        self.has_time_expired = False
        self.player_lost_on_time = None

        self.moves.clear()
        self.positions.clear()

        self.clear_arrow()
        self.reset_selected_squares()

    def reset_selected_squares(self) -> None:
        """Reset origin and target squares."""
        self.origin_square = None
        self.target_square = None

    def set_selected_square(self, square_index: Square) -> None:
        """Set selected square to be `square_index`."""
        if self.origin_square is None:
            self.origin_square = square_index
        else:
            self.target_square = square_index
            self.find_legal_move(self.origin_square, self.target_square)
            self.reset_selected_squares()

    def prepare_new_game(self) -> None:
        """Initialize state and reset board for new game."""
        self._initialize_state()
        self.board.reset()

    def declare_time_loss_for(self, player_color: Color) -> None:
        """Declare that `player_color` has lost on time."""
        self.player_lost_on_time = player_color
        self.has_time_expired = True

    def maybe_append_ellipsis(self) -> None:
        """If Black moves first, append ellipsis for White's move."""
        if self.move_index < 0 and not self.is_white_on_turn():
            self.moves.append("...")
            self.positions.append(self.board.copy())

    def push(self, move: Move) -> None:
        """Update game state by pushing `move`."""
        if not self.board.is_legal(move):
            return

        self.delete_data_after_index()
        self.maybe_append_ellipsis()

        self.sound_effect_played.emit(move)

        new_move: str = self.board.san_and_push(move)
        self.moves.append(new_move)

        position: Board = self.board.copy()
        self.positions.append(position)

    def set_arrow(self, move: Move) -> None:
        """Set arrow based on `move`."""
        self.arrow = [(move.from_square, move.to_square)]

    def clear_arrow(self) -> None:
        """Clear arrow from board."""
        self.arrow.clear()

    def set_root_position(self) -> None:
        """Reset pieces on board to initial position and clear arrow."""
        self.move_index = -1
        self.board = self.board.root()

        self.clear_arrow()

    def legal_targets(self, square: Square | None = None) -> list[Square]:
        """Get target squares as legal moves for piece at `square`."""
        if square is None:
            return []

        square_bit: int = BB_SQUARES[square]
        targets: Iterator[Move] = self.board.generate_legal_moves(square_bit)
        return [move.to_square for move in targets]

    def find_legal_move(self, origin_square: Square, target_square: Square) -> None:
        """Find legal move for `origin_square` and `target_square`."""
        if origin_square is None or target_square is None:
            return

        with suppress(IllegalMoveError):
            move: Move = self.board.find_move(origin_square, target_square)

            if move.promotion:
                move.promotion = self.promotion_piece_type()

            self.move_played.emit(move)

    def promotion_piece_type(self) -> PieceType | None:
        """Get promotion piece type from promotion dialog."""
        promotion_dialog: PromotionDialog = PromotionDialog(self.board.turn)

        if promotion_dialog.exec() == QDialog.DialogCode.Accepted:
            return promotion_dialog.piece_type

        return None

    def piece_at(self, square: Square) -> Piece | None:
        """Get piece at `square`."""
        return self.board.piece_at(square)

    def update_state(self, item_index: int) -> None:
        """Update game state based on `item_index`."""
        self.move_index = item_index
        self.board = self.positions[item_index].copy()

        if self.moves[item_index] != "...":
            self.set_arrow(self.board.move_stack[-1])
        else:
            self.clear_arrow()

    def delete_data_after_index(self) -> None:
        """Delete moves and positions after internal move index."""
        last_move_index: int = len(self.moves) - 1

        if self.move_index < last_move_index:
            after_move_index: slice = slice(self.move_index + 1, len(self.moves))
            del self.moves[after_move_index]
            del self.positions[after_move_index]

    def gives_check(self, move: Move) -> bool:
        """Return True if `move` puts opponent's king in check."""
        return self.board.gives_check(move)

    def is_engine_on_turn(self) -> bool:
        """Return True if engine is on turn."""
        return self.board.turn == setting_value("engine", "is_white")

    def is_in_progress(self) -> bool:
        """Return True if game is in progress."""
        return bool(self.moves)

    def is_legal(self, move: Move) -> bool:
        """Return True if `move` would be considered as legal."""
        return self.board.is_legal(move)

    def is_over(self) -> bool:
        """Return True if game is over or time has expired."""
        return self.board.is_game_over(claim_draw=True) or self.has_time_expired

    def is_over_after(self, move: Move) -> bool:
        """Return True if game is over after `move`."""
        board: Board = self.board.copy()
        board.push(move)
        return board.is_game_over(claim_draw=True)

    def is_valid(self) -> bool:
        """Return True if board setup is valid."""
        return self.board.is_valid()

    def is_white_on_turn(self) -> bool:
        """Return True if White is on turn."""
        return self.board.turn == WHITE
