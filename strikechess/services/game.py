from contextlib import suppress

from chess import (
    BB_SQUARES,
    BLACK,
    Board,
    IllegalMoveError,
    Move,
    STARTING_FEN,
    WHITE,
)
from PySide6.QtCore import QObject, Signal


class GameService(QObject):
    """Chess game logic and state."""

    move_played: ClassVar[Signal] = Signal(Move)

    def __init__(self, settings: SettingsService) -> None:
        super().__init__()

        self._settings: SettingsService = settings
        self._board: Board = Board()

        self.moves: list[str] = []
        self.positions: list[Board] = []
        self.arrow: list[tuple[Square, Square]] = []

        self.move_index: int = -1
        self.is_viewing_history: bool = False
        self.player_with_expired_clock: Color | None = None

    @property
    def board(self) -> Board:
        """Current state of Board object."""
        return self._board

    @property
    def check(self) -> Square | None:
        """Square of king in check."""
        if self._board.is_check():
            return self._board.king(self._board.turn)
        return None

    @property
    def fen(self) -> str:
        """Current position in FEN format."""
        return self._board.fen()

    @fen.setter
    def fen(self, value: str) -> None:
        """New position from `value` in FEN format."""
        self._board.set_fen(value)
        self.reset_game_state()

    @property
    def move_stack(self) -> list[Move]:
        """Stack of moves in game, unaffected by viewing history."""
        return self.positions[-1].move_stack if self.positions else self._board.move_stack

    @property
    def root_fen(self) -> str:
        """Initial position in FEN format before any moves."""
        return self._board.root().fen()

    @property
    def turn(self) -> Color:
        """Color of player on current turn."""
        return self._board.turn

    def result(self, format_type: Literal["message", "pgn"] = "message") -> str:
        """Get game result in `format_type` as message or PGN format."""
        if self.player_with_expired_clock == BLACK:
            return "1-0" if format_type == "pgn" else self.tr("White wins on time")
        elif self.player_with_expired_clock == WHITE:
            return "0-1" if format_type == "pgn" else self.tr("Black wins on time")

        pgn_result: str = self._board.result(claim_draw=True)

        if format_type == "pgn":
            return pgn_result

        messages: dict[str, str] = {
            "1/2-1/2": self.tr("Draw"),
            "0-1": self.tr("Black wins"),
            "1-0": self.tr("White wins"),
            "*": self.tr("Undetermined game"),
        }
        return messages[pgn_result]

    def reset(self) -> None:
        """Reset board to initial position and game to default state."""
        self._board.reset()
        self.reset_game_state()

    def reset_game_state(self) -> None:
        """Reset game to default state."""
        self.move_index = -1
        self.is_viewing_history = False
        self.player_with_expired_clock = None

        self.moves.clear()
        self.positions.clear()

        self.clear_arrow()
        self.add_ellipsis_as_first_move()

    def load_moves(self, moves: list[str]) -> None:
        """Load `moves` into current game."""
        for san_move in moves:
            move: Move = self._board.parse_san(san_move)
            new_san_move: str = self._board.san_and_push(move)
            self.moves.append(new_san_move)
            self.positions.append(self._board.copy())

        self.move_index = len(self.moves) - 1

    def expire_clock_for(self, player_color: Color) -> None:
        """Set `player_color` as player whose clock expired."""
        self.player_with_expired_clock = player_color

    def push(self, move: Move) -> None:
        """Update game state due to `move` being played."""
        if not self._board.is_legal(move):
            return

        self.delete_game_data_after_index()

        san_move: str = self._board.san_and_push(move)
        self.moves.append(san_move)

        position: Board = self._board.copy()
        self.positions.append(position)

        self.move_index = len(self.moves) - 1

    def find_legal_move(self, origin_square: Square, target_square: Square) -> None:
        """Detect legal move by `origin_square` and `target_square`."""
        if origin_square is None or target_square is None:
            return

        with suppress(IllegalMoveError):
            move: Move = self._board.find_move(origin_square, target_square)
            self.move_played.emit(move)

    def legal_target_squares(self, square: Square | None = None) -> list[Square]:
        """Get legal target squares for piece at `square`."""
        if square is None:
            return []

        square_mask: int = BB_SQUARES[square]
        moves: Iterator[Move] = self._board.generate_legal_moves(square_mask)
        return [move.to_square for move in moves]

    def set_root_position(self) -> None:
        """Reset pieces to initial position and clear arrow marker."""
        self.move_index = -1
        self._board = self._board.root()

        self.clear_arrow()

    def update_state(self, move_index: int) -> None:
        """Update game state by `move_index`."""
        self.move_index = move_index
        self._board = self.positions[move_index].copy()

        if self.moves[move_index] == "...":
            self.clear_arrow()
        else:
            self.set_arrow(self._board.move_stack[-1])

    def delete_game_data_after_index(self) -> None:
        """Delete moves and positions after internal move index."""
        last_move_index: int = len(self.moves) - 1

        if self.move_index < last_move_index:
            after_move_index: slice = slice(self.move_index + 1, len(self.moves))
            del self.moves[after_move_index]
            del self.positions[after_move_index]

    def set_arrow(self, move: Move) -> None:
        """Set arrow marker for `move`."""
        self.arrow = [(move.from_square, move.to_square)]

    def clear_arrow(self) -> None:
        """Clear current arrow marker from board."""
        self.arrow.clear()

    def add_ellipsis_as_first_move(self) -> None:
        """Add ellipsis as White's missing move if Black starts."""
        if self.move_index < 0 and not self.is_white_to_move():
            self.moves.append("...")
            self.positions.append(self._board.copy())
            self.move_index = 0

    def piece_at(self, square: Square) -> Piece | None:
        """Get piece at `square`, if any."""
        return self._board.piece_at(square)

    def gives_check(self, move: Move) -> bool:
        """Return True if `move` puts opponent's king in check."""
        return self._board.gives_check(move)

    def is_capture(self, move: Move) -> bool:
        """Return True if `move` is capture."""
        return self._board.is_capture(move)

    def is_castling(self, move: Move) -> bool:
        """Return True if `move` is castling."""
        return self._board.is_castling(move)

    def is_engine_to_move(self) -> bool:
        """Return True if engine is to move."""
        return self._board.turn == self._settings.value("engine", "is_white")

    def is_in_progress(self) -> bool:
        """Return True if game is in progress."""
        return bool(self.moves) or self.fen != STARTING_FEN

    def is_legal(self, move: Move) -> bool:
        """Return True if `move` is legal."""
        return self._board.is_legal(move)

    def is_over_by_result(self) -> bool:
        """Return True if game is over by rules or by expired clock."""
        return (
            self._board.is_game_over(claim_draw=True)
            or self.player_with_expired_clock is not None
        )

    def is_over_by_rules(self) -> bool:
        """Return True if game is over only by rules."""
        position: Board = self.positions[-1] if self.positions else self._board
        return position.is_game_over(claim_draw=True)

    def is_over_by_rules_after(self, move: Move) -> bool:
        """Return True if game is over by rules after `move`."""
        board: Board = self._board.copy()
        board.push(move)
        return board.is_game_over(claim_draw=True)

    def is_position_valid(self) -> bool:
        """Return True if current position is valid by chess rules."""
        return self._board.is_valid()

    def is_white_to_move(self) -> bool:
        """Return True if White is to move."""
        return self._board.turn == WHITE
