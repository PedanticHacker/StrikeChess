import os
import platform
import stat
import subprocess
from contextlib import suppress
from pathlib import Path

from chess import Move
from chess.engine import EngineError, Limit, Score, SimpleEngine
from cpuinfo import get_cpu_info
from psutil import cpu_count, virtual_memory
from PySide6.QtCore import QObject, Signal

from strikechess.utils import root_path


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

        self.is_thinking: bool = False
        self.is_analyzing: bool = False

        self.load_default_engine()

    @property
    def name(self) -> str:
        """Engine name, or "(no engine)" if none is loaded."""
        return self.tr("(no engine)") if self._engine is None else self._engine.id["name"]

    def is_loaded(self) -> bool:
        """Return True if engine is loaded."""
        return self._engine is not None

    def load_default_engine(self) -> None:
        """Load executable file of Stockfish engine."""
        with suppress(EngineError):
            self.load_file(_stockfish_executable())

    def load_file(self, file_path: str) -> None:
        """Load UCI-compliant engine from `file_path`."""
        try:
            _delete_quarantine_attribute(file_path)
            _make_executable(file_path)

            new_engine: SimpleEngine = SimpleEngine.popen_uci(file_path)
            new_engine.configure(_engine_options())

            self.terminate()
            self._engine = new_engine

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
        if self._engine is None:
            return

        with self._engine.analysis(self._game.board) as analysis:
            for info in analysis:
                if not self.is_analyzing:
                    break

                if "pv" in info:
                    pv: list[Move] = info["pv"][0:50]

                    best_move: Move = pv[0]
                    score: Score = info["score"].white()
                    variation: str = self._game.board.variation_san(pv)

                    self.best_move_analyzed.emit(best_move)
                    self.score_analyzed.emit(score)
                    self.variation_analyzed.emit(variation)

    def stop_analysis(self) -> None:
        """Stop analyzing current position."""
        self.is_analyzing = False


def _delete_quarantine_attribute(file_path: str) -> None:
    """Delete quarantine attribute from `file_path`."""
    if platform.system() == "Darwin":
        subprocess.run(
            ["xattr", "-d", "com.apple.quarantine", file_path],
            stderr=subprocess.DEVNULL,
        )


def _engine_options() -> dict[str, int]:
    """Get UCI engine Hash and Threads options based on OS resources."""
    bytes_per_megabyte: int = 2**20
    engine_hash_size_percentage: float = 0.25
    maximum_hash_size_in_megabytes: int = 4096

    logical_cpu_cores: int | None = cpu_count()
    allowed_cpu_threads: int = 1 if logical_cpu_cores is None else max(1, logical_cpu_cores // 2)

    available_ram_in_megabytes: int = virtual_memory().available // bytes_per_megabyte
    allowed_hash_size_in_megabytes: int = int(available_ram_in_megabytes * engine_hash_size_percentage)

    return {
        "Hash": min(allowed_hash_size_in_megabytes, maximum_hash_size_in_megabytes),
        "Threads": allowed_cpu_threads,
    }


def _make_executable(file_path: str) -> None:
    """Make `file_path` have executable permission."""
    os.chmod(file_path, os.stat(file_path).st_mode | stat.S_IXUSR)


def _stockfish_executable() -> str:
    """Get path to executable file of default Stockfish engine."""
    system: str = platform.system()
    extension: str = ".exe" if system == "Windows" else ""

    stockfish_directory: Path = root_path() / "assets" / "engines" / "stockfish-18" / system
    build_path: Path = stockfish_directory / _stockfish_build() / f"stockfish{extension}"

    return str(build_path)


def _stockfish_build() -> str:
    """Detect best Stockfish build for current CPU."""
    if platform.machine() == "arm64":
        return "apple-silicon"

    cpu_info: dict[str, Any] = get_cpu_info()
    supported_instructions: set[str] = set(cpu_info.get("flags", []))

    if platform.system() == "Darwin":
        builds: list[tuple[str, set[str]]] = [
            ("bmi2", {"bmi2", "popcnt"}),
            ("avx2", {"avx2", "popcnt"}),
            ("sse41-popcnt", {"sse4_1", "popcnt"}),
        ]
    else:
        builds = [
            ("avx512icl", {"avx512f", "avx512_vnni", "avx512_vbmi", "popcnt"}),
            ("vnni512", {"avx512_vnni", "avx512f", "popcnt"}),
            ("avx512", {"avx512f", "popcnt"}),
            ("avxvnni", {"avx_vnni", "popcnt"}),
            ("bmi2", {"bmi2", "popcnt"}),
            ("avx2", {"avx2", "popcnt"}),
            ("sse41-popcnt", {"sse4_1", "popcnt"}),
        ]

    for build, required_instructions in builds:
        if required_instructions <= supported_instructions:
            return build

    return "x86-64"
