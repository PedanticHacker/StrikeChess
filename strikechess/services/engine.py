import os
import stat
import platform
import subprocess
from pathlib import Path
from contextlib import suppress
from concurrent.futures import CancelledError

from chess import Move
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
from psutil import cpu_count, virtual_memory
from chess.engine import EngineError, Limit, Score, SimpleEngine

from strikechess.utils import root_path


class EngineService(QObject):
    """Chess engine operations using Universal Chess Interface (UCI)."""

    error_occurred: ClassVar[Signal] = Signal()
    move_played: ClassVar[Signal] = Signal(Move)
    score_analyzed: ClassVar[Signal] = Signal(Score)
    variation_analyzed: ClassVar[Signal] = Signal(str)
    best_move_analyzed: ClassVar[Signal] = Signal(Move)

    def __init__(self, settings: SettingsService) -> None:
        super().__init__()

        self._settings: SettingsService = settings

        self._engine: SimpleEngine | None = None
        self._analysis: SimpleAnalysisResult | None = None

        self.is_thinking: bool = False
        self.is_analyzing: bool = False

        self.load_default_engine()

        QApplication.instance().aboutToQuit.connect(self.terminate)

    @property
    def name(self) -> str:
        """Engine name, or "(no engine)" if none is loaded."""
        return self.tr("(no engine)") if self._engine is None else self._engine.id["name"]

    def is_loaded(self) -> bool:
        """Return True if engine is loaded."""
        return self._engine is not None

    def load_default_engine(self) -> None:
        """Load executable file of default Stockfish engine."""
        with suppress(EngineError):
            self.load_file(_stockfish_executable())

    def load_file(self, file_path: str) -> None:
        """Load UCI-compliant engine from `file_path`."""
        new_engine: SimpleEngine | None = None

        try:
            _make_executable(file_path)
            _delete_quarantine_attribute(file_path)

            new_engine = SimpleEngine.popen_uci(file_path)
            new_engine.configure(_engine_options(new_engine.options))

            if "name" not in new_engine.id:
                raise EngineError

        except Exception:
            if new_engine is not None:
                new_engine.close()

            raise EngineError(
                self.tr(
                    "Cannot load UCI engine.\n\n"
                    "The engine file may be incompatible.\n"
                    "Ensure the engine matches your platform and CPU architecture."
                )
            )

        self.terminate()
        self._engine = new_engine

    def terminate(self) -> None:
        """Stop analysis and terminate engine."""
        engine: SimpleEngine | None = self._engine

        if engine is None:
            return

        self.stop_analysis()

        self._engine = None
        engine.close()

    def play_move(
        self,
        board: Board,
        black_time: float,
        black_increment: float,
        white_time: float,
        white_increment: float,
    ) -> None:
        """Invoke engine to play move on `board`."""
        engine: SimpleEngine | None = self._engine

        if engine is None:
            return

        try:
            play_result: PlayResult = engine.play(
                board=board,
                ponder=self._settings.value("engine", "is_ponder_enabled"),
                limit=Limit(
                    black_clock=black_time,
                    white_clock=white_time,
                    black_inc=black_increment,
                    white_inc=white_increment,
                ),
            )

        except CancelledError:
            return

        except EngineError:
            self.is_thinking = False

            if engine is self._engine:
                self.error_occurred.emit()

            return

        if play_result.move is None or engine is not self._engine:
            self.is_thinking = False
            return

        self.move_played.emit(play_result.move)

    def start_analysis(self, board: Board) -> None:
        """Start analyzing position on `board`."""
        engine: SimpleEngine | None = self._engine

        if engine is None:
            return

        try:
            with engine.analysis(board) as analysis:
                self._analysis = analysis

                for info in analysis:
                    if not self.is_analyzing:
                        break

                    if "lowerbound" in info or "upperbound" in info:
                        continue

                    if "pv" in info and "score" in info:
                        pv: list[Move] = info["pv"][:50]

                        best_move: Move = pv[0]
                        score: Score = info["score"].white()
                        variation: str = board.variation_san(pv)

                        self.score_analyzed.emit(score)
                        self.best_move_analyzed.emit(best_move)
                        self.variation_analyzed.emit(variation)

        except (CancelledError, EngineError, TimeoutError):
            self.is_analyzing = False

            if engine is self._engine:
                engine.close()
                self.error_occurred.emit()

    def stop_analysis(self) -> None:
        """Stop analyzing current position."""
        self.is_analyzing = False

        if self._analysis is not None:
            with suppress(EngineError):
                self._analysis.stop()

    def stop_ponder(self) -> None:
        """Stop engine from pondering in background."""
        engine: SimpleEngine | None = self._engine

        if engine is None or self.is_thinking or self.is_analyzing:
            return

        try:
            engine.ping()
        except (EngineError, TimeoutError):
            engine.close()
            self.error_occurred.emit()


def _delete_quarantine_attribute(file_path: str) -> None:
    """Delete quarantine attribute from `file_path`."""
    if platform.system() == "Darwin":
        subprocess.run(
            ["xattr", "-d", "com.apple.quarantine", file_path],
            stderr=subprocess.DEVNULL,
        )


def _engine_options(available_options: Mapping[str, Option]) -> dict[str, int]:
    """Get supported Hash and Threads options based on OS resources."""
    bytes_per_megabyte: int = 2**20
    engine_hash_size_percentage: float = 0.25
    maximum_hash_size_in_megabytes: int = 4096

    logical_cpu_cores: int | None = cpu_count()
    allowed_cpu_threads: int = 1 if logical_cpu_cores is None else max(1, logical_cpu_cores // 2)

    available_ram_in_megabytes: int = virtual_memory().available // bytes_per_megabyte
    allowed_hash_size_in_megabytes: int = max(
        16, int(available_ram_in_megabytes * engine_hash_size_percentage)
    )

    options: dict[str, int] = {
        "Threads": allowed_cpu_threads,
        "Hash": min(allowed_hash_size_in_megabytes, maximum_hash_size_in_megabytes),
    }
    return {
        option: min(available_options[option].max or value, value)
        for option, value in options.items()
        if option in available_options
    }


def _make_executable(file_path: str) -> None:
    """Make `file_path` have executable permission."""
    if os.access(file_path, os.X_OK):
        return

    os.chmod(file_path, os.stat(file_path).st_mode | stat.S_IXUSR)


def _stockfish_executable() -> str:
    """Get path to executable file of default Stockfish engine."""
    system: str = platform.system()
    extension: str = ".exe" if system == "Windows" else ""

    stockfish_directory: Path = root_path() / "assets" / "engines" / "stockfish-19" / system
    executable_path: Path = stockfish_directory / f"stockfish{extension}"

    return str(executable_path)
