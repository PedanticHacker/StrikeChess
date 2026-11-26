from enum import StrEnum

from chess import Color, WHITE
from PySide6.QtWidgets import QLCDNumber
from PySide6.QtCore import QElapsedTimer, QSize, Qt, QTimer, Signal, Slot


TenthsThresholdInSeconds: Final[float] = 10.0
CountdownIntervalInMilliseconds: Final[int] = 30
NanosecondsPerSecond: Final[int] = 1_000_000_000


class ClockStyleSheet(StrEnum):
    """Qt Style Sheets (QSS) for clock widgets."""

    Black = "color: white; background-color: black;"
    White = "color: black; background-color: white;"


class ChessClock(QLCDNumber):
    """Player's clock, counting down while player is on turn."""

    expired: ClassVar[Signal] = Signal(Color)

    def __init__(self, player_color: Color, game: GameService, settings: SettingsService) -> None:
        super().__init__()

        self._game: GameService = game
        self._player_color: Color = player_color
        self._settings: SettingsService = settings

        self.setStyleSheet(
            ClockStyleSheet.White if player_color == WHITE else ClockStyleSheet.Black
        )
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
        """Stop countdown and set time and increment from settings."""
        self._countdown_timer.stop()

        self.time: float = self._settings.value("clock", "time")
        self.increment: float = self._settings.value("clock", "increment")
        self._show_time()

    def update_countdown(self) -> None:
        """Start/stop countdown based on current turn."""
        if not self._game.move_stack:
            return

        if self._game.is_over_by_result() or self._game.is_viewing_history:
            return

        if self._game.turn == self._player_color:
            self.start_timer()
        else:
            self.stop_timer()

    def start_timer(self) -> None:
        """Start countdown unless already active."""
        if self._countdown_timer.isActive():
            return

        self._elapsed_timer.start()
        self._countdown_timer.start()

    def stop_timer(self) -> None:
        """Stop countdown and update clock to remaining time."""
        if not self._countdown_timer.isActive():
            return

        elapsed_time: float = self._elapsed_timer.nsecsElapsed() / NanosecondsPerSecond
        self.time = max(0.0, self.time - elapsed_time)
        self._show_time()

        self._countdown_timer.stop()

    def add_increment(self) -> None:
        """Add increment to time on clock if player just moved."""
        if len(self._game.move_stack) == 1 or self._game.turn == self._player_color:
            return

        self.time += self.increment
        self._show_time()

    @Slot()
    def update_time(self) -> None:
        """Update clock to remaining time and check for expiration."""
        elapsed_time: float = self._elapsed_timer.nsecsElapsed() / NanosecondsPerSecond
        self.time -= elapsed_time
        self._elapsed_timer.start()

        if self.time <= 0.0:
            self.time = 0.0
            self._countdown_timer.stop()
            self.expired.emit(self._player_color)

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
