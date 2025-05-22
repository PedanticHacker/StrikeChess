from __future__ import annotations

from typing import ClassVar

from chess import Move
from chess.engine import Limit, PlayResult, Score, SimpleEngine
from PySide6.QtCore import QObject, Signal

from strikechess.utils import (
    delete_quarantine_attribute,
    engine_configuration,
    make_executable,
    path_to_stockfish,
    setting_value,
)


class Engine(QObject):
    """Communication with UCI-compliant engine."""

    best_move_analyzed: ClassVar[Signal] = Signal(Move)
    load_failed: ClassVar[Signal] = Signal(str)
    move_played: ClassVar[Signal] = Signal(Move)
    score_analyzed: ClassVar[Signal] = Signal(Score)
    variation_analyzed: ClassVar[Signal] = Signal(str)

    def __init__(self, game: Game) -> None:
        super().__init__()

        self._game: Game = game
        self._analyzing: bool = False

        self.load_from_file_at(path_to_stockfish())

    @property
    def name(self) -> str:
        """Get engine name if engine is loaded."""
        if hasattr(self, "_engine"):
            name: str = self._engine.id["name"]
            return f"{name[0:15]}..." if len(name) > 15 else name
        return "(no engine loaded)"

    def load_from_file_at(self, path_to_file: str) -> None:
        """Load engine from file at `path_to_file`."""
        try:
            delete_quarantine_attribute(path_to_file)
            make_executable(path_to_file)

            new_engine: SimpleEngine = SimpleEngine.popen_uci(path_to_file)
            new_engine.configure(engine_configuration())

            self.quit()
            self._engine: SimpleEngine = new_engine

        except Exception as exception:
            self.load_failed.emit(f"UCI engine failed to load.\n\n{exception}")

    def play_move(self) -> None:
        """Invoke engine to play move."""
        play_result: PlayResult = self._engine.play(
            limit=Limit(depth=20),
            board=self._game.board,
            ponder=setting_value("engine", "is_ponder_on"),
        )
        self.move_played.emit(play_result.move)

    def start_analysis(self) -> None:
        """Start analyzing current position."""
        self._analyzing = True

        with self._engine.analysis(self._game.board) as analysis:
            for info in analysis:
                if not self._analyzing:
                    break

                if "pv" in info:
                    pv: list[Move] = info["pv"]

                    best_move: Move = pv[0]
                    score: Score = info["score"].white()
                    variation: str = self._game.board.variation_san(pv)

                    self.best_move_analyzed.emit(best_move)
                    self.score_analyzed.emit(score)
                    self.variation_analyzed.emit(variation)

    def stop_analysis(self) -> None:
        """Stop analyzing current position."""
        self._analyzing = False

    def quit(self) -> None:
        """Stop analysis and terminate engine."""
        self.stop_analysis()

        if hasattr(self, "_engine"):
            self._engine.quit()
