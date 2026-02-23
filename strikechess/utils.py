import json
import os
import platform
import stat
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from cpuinfo import get_cpu_info
from psutil import cpu_count, virtual_memory
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction, QColor, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QPushButton

from strikechess import __version__


def abort_duplicate_launch(splash_screen: SplashScreen, main_window: MainWindow) -> None:
    """Warn user about duplicate launch and quit app."""
    splash_screen.close()

    show_warning(
        main_window,
        QApplication.translate("StrikeChess", "App Error"),
        QApplication.translate("StrikeChess", "StrikeChess has already been launched!"),
    )

    main_window.terminate_engine()
    sys.exit()


def ask_question(parent: QWidget | None, title: str, question: str) -> bool:
    """Ask yes/no question based on `title` and `question`."""
    answer: QMessageBox.StandardButton = QMessageBox.question(parent, title, question)
    return answer == QMessageBox.StandardButton.Yes


def create_action(
    icon: QIcon,
    name: str,
    handler: Callable[[], None],
    shortcut: str,
    status_tip: str,
) -> QAction:
    """Create action for menu item or tool bar button."""
    action: QAction = QAction(icon, name)
    action.setShortcut(shortcut)
    action.setStatusTip(status_tip)
    action.triggered.connect(handler)
    return action


def create_app() -> QApplication:
    """Create QApplication object initialized with basic settings."""
    app: QApplication = QApplication()
    app.setStyle("fusion")
    app.setApplicationName("StrikeChess")
    app.setDesktopFileName("StrikeChess")
    app.setApplicationVersion(__version__)
    app.setWindowIcon(create_svg_icon("logo"))
    app.setApplicationDisplayName("StrikeChess")
    return app


def create_button(icon: QIcon) -> QPushButton:
    """Create button with `icon`."""
    button: QPushButton = QPushButton()
    button.setIcon(icon)
    button.setIconSize(QSize(50, 50))
    return button


def create_colored_icon(color: str) -> QIcon:
    """Create icon in 16 by 16 pixels filled with `color`."""
    pixmap: QPixmap = QPixmap(16, 16)
    pixmap.fill(QColor(color))
    return QIcon(pixmap)


def create_svg_icon(file_name: str) -> QIcon:
    """Create SVG icon from file at `file_name`."""
    return QIcon(f":/icons/{file_name}.svg")


def delete_quarantine_attribute(file_path: str) -> None:
    """Delete quarantine attribute from `file_path`."""
    if platform.system() == "Darwin":
        subprocess.run(
            ["xattr", "-d", "com.apple.quarantine", file_path],
            stderr=subprocess.DEVNULL,
        )


def engine_options() -> dict[str, int]:
    """Get UCI engine Hash and Threads options based on OS resources."""
    bytes_per_megabyte: int = 2**20
    engine_hash_size_percentage: float = 0.25

    logical_cpu_cores: int | None = cpu_count()
    allowed_cpu_threads: int = 1 if logical_cpu_cores is None else max(1, logical_cpu_cores // 2)

    available_ram_in_megabytes: int = virtual_memory().available // bytes_per_megabyte
    allowed_hash_size_in_megabytes: int = int(
        available_ram_in_megabytes * engine_hash_size_percentage
    )

    return {"Hash": allowed_hash_size_in_megabytes, "Threads": allowed_cpu_threads}


def find_opening(fen: str) -> str | None:
    """Get opening name based on `fen`."""
    return _openings().get(fen)


def make_executable(file_path: str) -> None:
    """Make `file_path` have executable permission."""
    os.chmod(file_path, os.stat(file_path).st_mode | stat.S_IXUSR)


def read_pgn_file(file_path: str) -> str:
    """Read and return PGN text from `file_path`."""
    with open(file_path, encoding="utf-8") as file:
        return file.read()


def root_path() -> Path:
    """Get path to app's root directory."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def save_with_file_manager(
    parent: QWidget | None, caption: str, file_filter: str, suggested_name: str = ""
) -> str | None:
    """Show file manager to save file and return selected path."""
    file_path, _ = QFileDialog.getSaveFileName(
        parent=parent,
        caption=caption,
        dir=suggested_name,
        filter=file_filter,
    )
    return file_path if file_path else None


def show_about(parent: QWidget | None) -> None:
    """Show About dialog."""
    QMessageBox.about(
        parent,
        QApplication.translate("StrikeChess", "About StrikeChess %1").replace(
            "%1", __version__
        ),
        QApplication.translate(
            "StrikeChess",
            "Play chess and analyze games across\n"
            "Windows, Linux, and macOS platforms.\n\n"
            "Copyright © 2026 Boštjan Mejak\n"
            "MIT License",
        ),
    )


def show_file_manager(parent: QWidget | None, caption: str, file_filter: str = "") -> str | None:
    """Show file manager to open file and return selected path."""
    file_path, _ = QFileDialog.getOpenFileName(
        parent=parent,
        caption=caption,
        dir=str(Path.home()),
        filter=file_filter,
    )
    return file_path if file_path else None


def show_info(parent: QWidget | None, message: str) -> None:
    """Show information dialog based on `message`."""
    QMessageBox.information(parent, QApplication.translate("StrikeChess", "Info"), message)


def show_warning(parent: QWidget | None, title: str, warning: str) -> None:
    """Show warning dialog based on `title` and `warning`."""
    QMessageBox.warning(parent, title, warning)


def stockfish_executable() -> str:
    """Get path to executable file of default Stockfish engine."""
    system: str = platform.system()
    extension: str = ".exe" if system == "Windows" else ""

    stockfish_directory: Path = root_path() / "assets" / "engines" / "stockfish-18" / system
    build_path: Path = stockfish_directory / _stockfish_build() / f"stockfish{extension}"

    return str(build_path)


def write_pgn_file(file_path: str, pgn_text: str) -> None:
    """Write `pgn_text` as PGN to `file_path`."""
    with open(file_path, mode="w", encoding="utf-8", newline="\n") as file:
        file.write(pgn_text)


@lru_cache(maxsize=1)
def _openings() -> dict[str, str]:
    """Load openings from openings.json file."""
    file_path: Path = root_path() / "assets" / "openings.json"

    with open(file_path, encoding="utf-8") as file:
        return json.load(file)


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
