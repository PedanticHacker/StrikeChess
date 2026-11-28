from PySide6.QtWidgets import QApplication, QMessageBox

from strikechess import __version__


def ask_question(parent: QWidget | None, title: str, question: str) -> bool:
    """Ask yes/no question with `title` and `question`."""
    answer: QMessageBox.StandardButton = QMessageBox.question(parent, title, question)
    return answer == QMessageBox.StandardButton.Yes


def show_about(parent: QWidget | None) -> None:
    """Show About dialog with version, copyright, and license."""
    title: str = QApplication.translate("StrikeChess", "About StrikeChess")

    message: str = QApplication.translate(
        "StrikeChess",
        "A chess app for Windows, Linux, and macOS,\n"
        "powered by the Stockfish engine.\n\n"
        "Copyright (C) 2026 Boštjan Mejak\n"
        "MIT License",
    )

    QMessageBox.about(parent, f"{title} {__version__}", message)


def show_info(parent: QWidget | None, message: str) -> None:
    """Show information dialog with `message`."""
    QMessageBox.information(parent, QApplication.translate("StrikeChess", "Info"), message)


def show_warning(parent: QWidget | None, title: str, warning: str) -> None:
    """Show warning dialog with `title` and `warning`."""
    QMessageBox.warning(parent, title, warning)
