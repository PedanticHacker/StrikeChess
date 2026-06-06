#!/usr/bin/env python3


import sys
from pathlib import Path
from multiprocessing import freeze_support

from PySide6.QtCore import QLockFile, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from strikechess import __version__
from strikechess.services import SettingsService
from strikechess.ui import MainWindow, SplashScreen
from strikechess.utils import create_svg_icon, install_translators, read_theme_stylesheet


SplashScreenDurationMilliseconds: Final[int] = 3000


def _create_app() -> QApplication:
    """Create QApplication object initialized with basic settings."""
    app: QApplication = QApplication()
    app.setStyle("fusion")
    app.setApplicationName("StrikeChess")
    app.setDesktopFileName("StrikeChess")
    app.setApplicationVersion(__version__)
    app.setWindowIcon(create_svg_icon("logo"))
    app.setApplicationDisplayName("StrikeChess")
    return app


def _show_duplicate_launch_warning() -> None:
    """Show warning that StrikeChess has already been launched."""
    settings: SettingsService = SettingsService()
    install_translators(settings.value("ui", "language"))

    theme_name: str = settings.value("ui", "theme")

    message_box: QMessageBox = QMessageBox(
        QMessageBox.Icon.Warning,
        QApplication.translate("StrikeChess", "App Error"),
        QApplication.translate("StrikeChess", "StrikeChess has already been launched!"),
    )

    message_box.setStyleSheet(read_theme_stylesheet(theme_name))

    message_box.exec()


def _switch(splash_screen: SplashScreen, main_window: MainWindow) -> None:
    """Switch from splash screen to main window."""
    splash_screen.finish(main_window)

    main_window.showMaximized()
    main_window.update_clock_timers()
    main_window.request_engine_move()


def main() -> None:
    """Launch app with splash screen, abort duplicate launch attempt."""
    app: QApplication = _create_app()

    lock_directory: Path = Path.home() / ".StrikeChess"
    lock_directory.mkdir(exist_ok=True)
    lock_file: QLockFile = QLockFile(str(lock_directory / "StrikeChess.lock"))

    if not lock_file.tryLock(1):
        _show_duplicate_launch_warning()
        sys.exit()

    splash_screen: SplashScreen = SplashScreen().show_raised()
    main_window: MainWindow = MainWindow()

    QTimer.singleShot(
        SplashScreenDurationMilliseconds,
        lambda: _switch(splash_screen, main_window),
    )

    app.exec()


if __name__ == "__main__":
    freeze_support()
    main()
