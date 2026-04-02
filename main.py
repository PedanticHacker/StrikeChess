#!/usr/bin/env python3


import sys
from pathlib import Path
from multiprocessing import freeze_support

from PySide6.QtCore import QLockFile, QTimer
from PySide6.QtWidgets import QApplication

from strikechess import __version__
from strikechess.ui import MainWindow, SplashScreen
from strikechess.utils import create_svg_icon, show_warning


SplashScreenDurationMilliseconds: Final[int] = 3000


def _abort_duplicate_launch(splash_screen: SplashScreen, main_window: MainWindow) -> None:
    """Warn user about duplicate launch and quit app."""
    splash_screen.close()

    show_warning(
        main_window,
        QApplication.translate("StrikeChess", "App Error"),
        QApplication.translate("StrikeChess", "StrikeChess has already been launched!"),
    )

    main_window.terminate_engine()
    sys.exit()


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


def _switch(splash_screen: SplashScreen, main_window: MainWindow) -> None:
    """Switch from splash screen to main window."""
    splash_screen.finish(main_window)

    main_window.showMaximized()
    main_window.update_clock_timers()
    main_window.request_engine_move()


def main() -> None:
    """Launch app with splash screen, abort duplicate launch attempt."""
    app: QApplication = _create_app()
    splash_screen: SplashScreen = SplashScreen().show_raised()
    main_window: MainWindow = MainWindow()

    lock_directory: Path = Path.home() / ".StrikeChess"
    lock_directory.mkdir(exist_ok=True)
    lock_file: QLockFile = QLockFile(str(lock_directory / "StrikeChess.lock"))

    if not lock_file.tryLock(1):
        _abort_duplicate_launch(splash_screen, main_window)

    QTimer.singleShot(
        SplashScreenDurationMilliseconds,
        lambda: _switch(splash_screen, main_window),
    )

    app.exec()


if __name__ == "__main__":
    freeze_support()
    main()
