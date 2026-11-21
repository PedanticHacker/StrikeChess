from enum import StrEnum
from functools import partial

from chess import BLACK, Color, WHITE
from PySide6.QtWidgets import QLCDNumber
from PySide6.QtCore import QElapsedTimer, QObject, QSize, Qt, QTimer, Signal, Slot


TenthsThresholdInSeconds: Final[float] = 10.0
CountdownIntervalInMilliseconds: Final[int] = 30
NanosecondsPerSecond: Final[int] = 1_000_000_000


class ClockStyleSheet(StrEnum):
    """QSS style sheets for clock widgets."""

    Black = "color: white; background-color: black;"
    White = "color: black; background-color: white;"


class DigitalClock(QLCDNumber):
    """Player's clock with countdown and elapsed timers."""

    expired: ClassVar[Signal] = Signal()

    def __init__(self, style_sheet: ClockStyleSheet, settings: SettingsService) -> None:
        super().__init__()

        self._settings: SettingsService = settings

        self.setStyleSheet(style_sheet)
        self.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        self._countdown_timer: QTimer = QTimer(self)
        self._countdown_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._countdown_timer.setInterval(CountdownIntervalInMilliseconds)
        self._countdown_timer.timeout.connect(self.update_time)

        self._elapsed_timer: QElapsedTimer = QElapsedTimer()

        self.reset()

    def sizeHint(self) -> QSize:
        """Get preferred clock size."""
        return QSize(200, 50)

    def minimumSizeHint(self) -> QSize:
        """Get minimum clock size."""
        return QSize(100, 50)

    def reset(self) -> None:
        """Stop countdown and set time to values from settings."""
        self._countdown_timer.stop()
        self.time: float = self._settings.value("clock", "time")
        self.increment: float = self._settings.value("clock", "increment")
        self._show_time()

    def start_timer(self) -> None:
        """Start tracking elapsed time, then start timer countdown."""
        if self._countdown_timer.isActive():
            return

        self._elapsed_timer.start()
        self._countdown_timer.start()

    def stop_timer(self) -> None:
        """Subtract elapsed time, then stop timer countdown."""
        if self._countdown_timer.isActive():
            elapsed_time: float = self._elapsed_timer.nsecsElapsed() / NanosecondsPerSecond
            self.time = max(0.0, self.time - elapsed_time)
            self._show_time()

        self._countdown_timer.stop()

    def add_increment(self) -> None:
        """Add increment to time on clock."""
        self.time += self.increment
        self._show_time()

    @Slot()
    def update_time(self) -> None:
        """Update remaining time and check for timer expiration."""
        elapsed_time: float = self._elapsed_timer.nsecsElapsed() / NanosecondsPerSecond
        self.time -= elapsed_time
        self._elapsed_timer.start()

        if self.time <= 0.0:
            self.time = 0.0
            self._countdown_timer.stop()
            self.expired.emit()

        self._show_time()

    def _show_time(self) -> None:
        """Show time on clock in hh:mm:ss, mm:ss, or mm:ss.s format."""
        time_as_text: str = self._format_time()
        self.setDigitCount(len(time_as_text))
        self.display(time_as_text)

    def _format_time(self) -> str:
        """Get time on clock in hh:mm:ss, mm:ss, or mm:ss.s format."""
        time_in_tenths_of_second: int = int(self.time * 10)
        time_in_seconds, tenths_of_second = divmod(time_in_tenths_of_second, 10)
        hours, remaining_time = divmod(time_in_seconds, 3600)
        minutes, seconds = divmod(remaining_time, 60)

        if self.time < TenthsThresholdInSeconds:
            return f"{minutes:02}:{seconds:02}.{tenths_of_second}"

        return f"{hours:02}:{minutes:02}:{seconds:02}" if hours else f"{minutes:02}:{seconds:02}"


class ChessClock(QObject):
    """Clocks of both players, counting down for player on turn."""

    expired: ClassVar[Signal] = Signal(Color)

    def __init__(self, game: GameService, settings: SettingsService) -> None:
        super().__init__()

        self._game: GameService = game

        self.black: DigitalClock = DigitalClock(ClockStyleSheet.Black, settings)
        self.black.expired.connect(partial(self.expired.emit, BLACK))

        self.white: DigitalClock = DigitalClock(ClockStyleSheet.White, settings)
        self.white.expired.connect(partial(self.expired.emit, WHITE))

    def reset(self) -> None:
        """Stop countdowns and set times to values from settings."""
        self.black.reset()
        self.white.reset()

    def update_timers(self) -> None:
        """Start/stop clocks based on current turn."""
        if not self._game.move_stack:
            self.stop_timers()
            return

        if self._game.is_over_by_result() or self._game.is_viewing_history:
            return

        if self._game.is_white_to_move():
            self.black.stop_timer()
            self.white.start_timer()
        else:
            self.white.stop_timer()
            self.black.start_timer()

    def stop_timers(self) -> None:
        """Stop countdowns of both clocks."""
        self.black.stop_timer()
        self.white.stop_timer()

    def add_increment(self) -> None:
        """Add increment to clock of player who just moved."""
        if len(self._game.move_stack) == 1:
            return

        if self._game.is_white_to_move():
            self.black.add_increment()
        else:
            self.white.add_increment()
