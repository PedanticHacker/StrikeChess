import re
from datetime import datetime
from io import StringIO

from chess.pgn import Game as PgnGame, read_game
from PySide6.QtWidgets import QApplication


class PgnService:
    """Portable Game Notation (PGN) parsing and exporting."""

    def parse_pgn(self, pgn_text: str) -> tuple[list[str], str | None, str]:
        """Parse `pgn_text` into moves, optional FEN, and result."""
        pgn_data: StringIO = StringIO(pgn_text)
        game: PgnGame | None = read_game(pgn_data)

        if game is None:
            raise ValueError(
                QApplication.translate(
                    "PgnService",
                    "Cannot load game.\n\n"
                    "No valid PGN game found.\n"
                    "Try selecting a different PGN.",
                )
            )

        if game.errors:
            raise ValueError(
                QApplication.translate(
                    "PgnService",
                    "Cannot load game.\n\n"
                    "PGN content might be invalid.\n"
                    "Check whether your PGN is corrupted or incomplete.",
                )
            )

        moves: list[str] = []
        board: Board = game.board()
        fen: str | None = game.headers.get("FEN")
        result: str = game.headers.get("Result", "*")

        for move in game.mainline_moves():
            san_move: str = board.san(move)
            moves.append(san_move)
            board.push(move)

        return moves, fen, result

    def export_to_pgn(
        self,
        game: GameService,
        human_name: str,
        engine_name: str,
        is_engine_white: bool,
    ) -> str:
        """Export game to PGN format."""
        headers: dict[str, str] = {
            "Event": "StrikeChess Game",
            "Site": "Computer",
            "Date": datetime.now().strftime("%Y.%m.%d"),
            "Round": "1",
            "White": engine_name if is_engine_white else human_name,
            "Black": human_name if is_engine_white else engine_name,
            "Result": game.result("pgn"),
        }

        pgn_game: PgnGame = PgnGame(headers)

        board: Board = pgn_game.board()
        board.set_fen(game.root_fen)
        pgn_game.setup(board)

        pgn_game.add_line(game.move_stack)

        return str(pgn_game)

    def suggest_file_name(
        self,
        human_name: str,
        engine_name: str,
        is_engine_white: bool,
    ) -> str:
        """Suggest PGN file name based on player names and timestamp."""
        white: str = self._sanitize(engine_name if is_engine_white else human_name)
        black: str = self._sanitize(human_name if is_engine_white else engine_name)
        timestamp: str = datetime.now().strftime("%Y.%m.%d %H-%M-%S")
        return f"{white} versus {black} ({timestamp}).pgn"

    def _sanitize(self, name: str) -> str:
        """Replace unsafe characters in `name` with underscores."""
        return re.sub(r'[<>:"/\\|?*]', "_", name)
