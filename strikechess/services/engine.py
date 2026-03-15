from contextlib import suppress

from chess import Move
from chess.engine import EngineError, Limit, Score, SimpleEngine
from PySide6.QtCore import QObject, Signal

from strikechess.utils import (
    delete_quarantine_attribute,
    engine_options,
    make_executable,
    stockfish_executable,
)


class EngineService(QObject):
    """Chess engine operations using Universal Chess Interface (UCI)."""

    move_played: ClassVar[Signal] = Signal(Move)
    score_analyzed: ClassVar[Signal] = Signal(Score)
    variation_analyzed: ClassVar[Signal] = Signal(str)
    best_move_analyzed: ClassVar[Signal] = Signal(Move)

    def __init__(self, game: GameService, settings: SettingsService) -> None:
        super().__init__()

        self._game: GameService = game
        self._settings: SettingsService = settings

        self._engine: SimpleEngine | None = None

        self._thinking: Event = Event()
        self._analyzing: Event = Event()
        self._active_analysis: SimpleEngine.analysis | None = None

        self.load_default_engine()

    @property
    def name(self) -> str:
        """Engine name, or "(no engine)" if none is loaded."""
        return self.tr("(no engine)") if self._engine is None else self._engine.id["name"]

    def is_thinking(self) -> bool:
        """Return True if engine is thinking."""
        return self._thinking.is_set()

    def is_analyzing(self) -> bool:
        """Return True if engine is analyzing."""
        return self._analyzing.is_set()

    def start_thinking(self) -> None:
        """Set engine state to thinking."""
        self._thinking.set()

    def stop_thinking(self) -> None:
        """Clear engine thinking state."""
        self._thinking.clear()

    def is_loaded(self) -> bool:
        """Return True if engine is loaded."""
        return self._engine is not None

    def load_default_engine(self) -> None:
        """Load executable file of Stockfish engine."""
        with suppress(EngineError):
            self.load_file(stockfish_executable())

    def load_file(self, file_path: str) -> None:
        """Load UCI-compliant engine from `file_path`."""
        try:
            delete_quarantine_attribute(file_path)
            make_executable(file_path)

            new_engine: SimpleEngine = SimpleEngine.popen_uci(file_path)

            if "name" not in new_engine.id:
                new_engine.quit()
                raise EngineError("Engine did not provide identification.")

            new_engine.configure(engine_options())

            self.terminate()
            self._engine = new_engine

        except EngineError:
            self._engine = None
            self._settings.set_value("engine", "name", "(no engine)")
            raise

        except Exception:
            self._engine = None
            self._settings.set_value("engine", "name", "(no engine)")

            raise EngineError(
                self.tr(
                    "Cannot load UCI engine.\n\n"
                    "The engine file may be incompatible.\n"
                    "Ensure the engine matches your platform and CPU architecture."
                )
            )

        self._settings.set_value("engine", "name", self._engine.id["name"])

    def unload(self) -> None:
        """Terminate currently loaded engine."""
        self.terminate()
        self._settings.set_value("engine", "name", "(no engine)")

    def terminate(self) -> None:
        """Stop analysis and terminate engine."""
        if self._engine is None:
            return

        self.stop_analysis()

        self._engine.quit()
        self._engine = None

    def play_move(
        self,
        black_time: float,
        black_increment: float,
        white_time: float,
        white_increment: float,
    ) -> None:
        """Invoke engine to play move."""
        if self._engine is None:
            return

        play_result: PlayResult = self._engine.play(
            board=self._game.board,
            limit=Limit(
                black_clock=black_time,
                black_inc=black_increment,
                white_clock=white_time,
                white_inc=white_increment,
            ),
            ponder=self._settings.value("engine", "is_ponder_enabled"),
        )
        self.move_played.emit(play_result.move)

    def start_analysis(self) -> None:
        """Start analyzing current position."""
        self._analyzing.set()

        with self._engine.analysis(self._game.board) as analysis:
            self._active_analysis = analysis

            for info in analysis:
                if not self._analyzing.is_set():
                    break

                if "pv" not in info:
                    continue

                pv: list[Move] = info["pv"]

                best_move: Move = pv[0]
                score: Score = info["score"].white()
                variation: str = self._game.board.variation_san(pv)

                self.best_move_analyzed.emit(best_move)
                self.score_analyzed.emit(score)
                self.variation_analyzed.emit(variation)

            self._active_analysis = None

    def stop_analysis(self) -> None:
        """Stop analyzing current position."""
        self._analyzing.clear()

        if self._active_analysis is not None:
            self._active_analysis.stop()
