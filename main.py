#!/usr/bin/env python3


from multiprocessing import freeze_support

from PySide6.QtCore import QLockFile, QTimer

from strikechess.ui import MainWindow, SplashScreen
from strikechess.utils import abort_duplicate_launch, create_app, lock_file_path


SplashScreenDurationMilliseconds: Final[int] = 3000


def _switch(splash_screen: SplashScreen, main_window: MainWindow) -> None:
    """Switch from splash screen to main window."""
    splash_screen.finish(main_window)

    main_window.showMaximized()
    main_window.update_clock_timers()
    main_window.request_engine_move()


def main() -> None:
    """Launch app with splash screen, abort duplicate launch attempt."""
    app: QApplication = create_app()
    splash_screen: SplashScreen = SplashScreen().show_raised()

    main_window: MainWindow = MainWindow()
    lock_file: QLockFile = QLockFile(lock_file_path())

    if not lock_file.tryLock(1):
        abort_duplicate_launch(splash_screen, main_window)

    QTimer.singleShot(
        SplashScreenDurationMilliseconds,
        lambda: _switch(splash_screen, main_window),
    )

    app.exec()


if __name__ == "__main__":
    freeze_support()
    main()
