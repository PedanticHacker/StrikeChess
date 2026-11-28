from chess.pgn import FileExporter
from PySide6.QtCore import QObject, Signal

from strikechess.services import PgnService
from strikechess.utils import (
    show_info,
    ask_question,
    show_warning,
    show_open_file_manager,
    show_save_file_manager,
)


class PgnFiles(QObject):
    """Loading and saving games as PGN files."""

    game_loaded: ClassVar[Signal] = Signal()

    def __init__(
        self,
        parent: QWidget,
        game: GameService,
        engine: EngineService,
        settings: SettingsService,
    ) -> None:
        super().__init__(parent)

        self._game: GameService = game
        self._engine: EngineService = engine
        self._pgn: PgnService = PgnService()
        self._settings: SettingsService = settings

    def load_from_pgn(self) -> None:
        """Load game from PGN, prompt if game is in progress."""
        if self._game.is_in_progress():
            if not ask_question(
                self.parent(),
                self.tr("Load Game"),
                self.tr(
                    "You will lose the current game.\n"
                    "Load from PGN anyway?"
                ),
            ):
                return

        file_path: str | None = show_open_file_manager(
            self.parent(),
            self.tr("Load Game"),
            self.tr("PGN file (*.pgn)"),
        )

        if file_path is None:
            return

        try:
            pgn_text: str = _read_pgn_file(file_path)
            moves, fen, result = self._pgn.parse_game(pgn_text)

            if fen is None:
                self._game.reset()
            else:
                self._game.fen = fen

            self._game.load_moves(moves)

            if result in ("1-0", "0-1", "1/2-1/2") and not self._game.is_over_by_rules():
                self._game.loaded_result = result

            self.game_loaded.emit()

            show_info(self.parent(), self.tr("Game loaded from PGN."))

        except (OSError, UnicodeDecodeError):
            show_warning(
                self.parent(),
                self.tr("File Error"),
                self.tr(
                    "Cannot read PGN.\n\n"
                    "The file may be locked or corrupted.\n"
                    "Check file permissions and try again."
                ),
            )

        except ValueError as error:
            show_warning(self.parent(), self.tr("Load Error"), str(error))

    def save_as_pgn(self) -> None:
        """Save current game as PGN."""
        is_engine_white: bool = self._settings.value("engine", "is_white")
        human_name: str = self._settings.value("human", "name") or "Player"
        engine_name: str = self._engine.name if self._engine.is_loaded() else "Unknown"

        suggested_file_name: str = self._pgn.suggest_file_name(
            human_name,
            engine_name,
            is_engine_white,
        )

        file_path: str | None = show_save_file_manager(
            self.parent(),
            self.tr("Save Game"),
            self.tr("PGN file (*.pgn)"),
            suggested_file_name,
        )

        if file_path is None:
            return

        try:
            pgn_game: PgnGame = self._pgn.create_game(
                self._game,
                human_name,
                engine_name,
                is_engine_white,
            )

            _write_pgn_file(file_path, pgn_game)

            show_info(self.parent(), self.tr("Game saved successfully."))

        except ValueError as error:
            show_warning(self.parent(), self.tr("Save Error"), str(error))

        except OSError:
            show_warning(
                self.parent(),
                self.tr("Save Error"),
                self.tr(
                    "Cannot save game as PGN.\n\n"
                    "The folder may be read-only or the disk may be full.\n"
                    "Try saving to a different folder."
                ),
            )


def _read_pgn_file(file_path: str) -> str:
    """Read PGN text from file at `file_path`."""
    with open(file_path, encoding="utf-8") as game_file:
        return game_file.read()


def _write_pgn_file(file_path: str, pgn_game: PgnGame) -> None:
    """Write `pgn_game` to file at `file_path`."""
    with open(file_path, mode="w", encoding="utf-8", newline="\n") as game_file:
        pgn_game.accept(FileExporter(game_file))
