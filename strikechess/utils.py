import json
import sys
from functools import lru_cache
from pathlib import Path

from PySide6.QtGui import QAction, QColor, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from strikechess import __version__


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


def create_colored_icon(color: str) -> QIcon:
    """Create icon in 16 by 16 pixels filled with `color`."""
    pixmap: QPixmap = QPixmap(16, 16)
    pixmap.fill(QColor(color))
    return QIcon(pixmap)


def create_svg_icon(file_name: str) -> QIcon:
    """Create SVG icon from file at `file_name`."""
    return QIcon(f":/icons/{file_name}.svg")


def find_opening(fen: str) -> str | None:
    """Get opening name based on `fen`."""
    return _openings().get(fen)


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
