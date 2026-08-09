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

    def __init__(self, settings: SettingsService) -> None:
        super().__init__()

        self._settings: SettingsService = settings

        self._engine: SimpleEngine | None = None

        self.is_thinking: bool = False
        self.is_analyzing: bool = False

        self._load_default_engine()

    @property
    def name(self) -> str:
        """Engine name, or "(no engine)" if none is loaded."""
        return self.tr("(no engine)") if self._engine is None else self._engine.id["name"]

    def is_loaded(self) -> bool:
        """Return True if engine is loaded."""
        return self._engine is not None

    def load_file(self, file_path: str) -> None:
        """Load UCI-compliant engine from `file_path`."""
        new_engine: SimpleEngine | None = None

        try:
            _delete_quarantine_attribute(file_path)
            _make_executable(file_path)

            new_engine = SimpleEngine.popen_uci(file_path)
            new_engine.configure(_engine_options(new_engine.options))

        except Exception:
            if new_engine is not None:
                with suppress(Exception):
                    new_engine.quit()

            raise EngineError(
                self.tr(
                    "Cannot load UCI engine.\n\n"
                    "The engine file may be incompatible.\n"
                    "Ensure the engine matches your platform and CPU architecture."
                )
            )

        self.terminate()
        self._engine = new_engine

        self._settings.set_value("engine", "name", new_engine.id["name"])

    def unload(self) -> None:
        """Terminate currently loaded engine."""
        self.terminate()
        self._settings.set_value("engine", "name", "(no engine)")

    def terminate(self) -> None:
        """Stop analysis and terminate engine."""
        engine: SimpleEngine | None = self._engine

        if engine is None:
            return

        self.stop_analysis()

        self._engine = None
        engine.quit()

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
                limit=Limit(
                    black_clock=black_time,
                    black_inc=black_increment,
                    white_clock=white_time,
                    white_inc=white_increment,
                ),
                ponder=self._settings.value("engine", "is_ponder_enabled"),
            )
        except EngineError:
            self.is_thinking = False
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
                for info in analysis:
                    if not self.is_analyzing:
                        break

                    if "pv" in info and "score" in info:
                        pv: list[Move] = info["pv"][:50]

                        best_move: Move = pv[0]
                        score: Score = info["score"].white()
                        variation: str = board.variation_san(pv)

                        self.best_move_analyzed.emit(best_move)
                        self.score_analyzed.emit(score)
                        self.variation_analyzed.emit(variation)
        except (EngineError, TimeoutError):
            self.is_analyzing = False

    def stop_analysis(self) -> None:
        """Stop analyzing current position."""
        self.is_analyzing = False

    def _load_default_engine(self) -> None:
        """Load executable file of default Stockfish engine."""
        try:
            self.load_file(_stockfish_executable())
        except EngineError:
            self._settings.set_value("engine", "name", "(no engine)")


def _delete_quarantine_attribute(file_path: str) -> None:
    """Delete quarantine attribute from `file_path`."""
    if platform.system() == "Darwin":
        subprocess.run(
            ["xattr", "-d", "com.apple.quarantine", file_path],
            stderr=subprocess.DEVNULL,
        )


def _engine_options(available_options: Mapping[str, Option]) -> dict[str, int]:
    """Get Hash and Threads options based on OS resources, if engine supports them."""
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
        "Hash": min(allowed_hash_size_in_megabytes, maximum_hash_size_in_megabytes),
        "Threads": allowed_cpu_threads,
    }
    return {name: value for name, value in options.items() if name in available_options}


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
    """Get best Stockfish build for current CPU."""
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        return "apple-silicon"

    cpu_info: dict[str, Any] = get_cpu_info()
    supported_instructions: set[str] | None = _supported_instructions(cpu_info)

    if supported_instructions is None:
        return "x86-64"

    if platform.system() == "Darwin":
        builds: dict[str, set[str]] = {
            "bmi2": {"bmi2"},
            "avx2": {"avx2"},
            "sse41-popcnt": {"sse41", "popcnt"},
        }
    else:
        builds = {
            "avx512icl": {
                "avx512bitalg", "avx512bw", "avx512cd", "avx512dq", "avx512f",
                "avx512ifma", "avx512vbmi", "avx512vbmi2", "avx512vl",
                "avx512vnni", "avx512vpopcntdq", "gfni", "vaes", "vpclmulqdq",
            },
            "vnni512": {"avx512bw", "avx512dq", "avx512f", "avx512vl", "avx512vnni"},
            "avx512": {"avx512bw", "avx512f"},
            "avxvnni": {"avxvnni"},
            "bmi2": {"bmi2"},
            "avx2": {"avx2"},
            "sse41-popcnt": {"sse41", "popcnt"},
        }

    if _is_bmi2_slow(cpu_info):
        supported_instructions.discard("bmi2")

    for build, required_instructions in builds.items():
        if required_instructions <= supported_instructions:
            return build

    return "x86-64"


def _is_bmi2_slow(cpu_info: dict[str, Any]) -> bool:
    """Return True if CPU runs BMI2 instructions in slow microcode."""
    zen_1_and_zen_2_family: int = 23

    if cpu_info.get("vendor_id_raw") != "AuthenticAMD":
        return False

    return cpu_info.get("family") == zen_1_and_zen_2_family


def _supported_instructions(cpu_info: dict[str, Any]) -> set[str] | None:
    """Get CPU instructions, if any."""
    instruction_names: list[str] | None = cpu_info.get("flags")

    if instruction_names is None:
        return None

    return {instruction_name.replace("_", "") for instruction_name in instruction_names}
