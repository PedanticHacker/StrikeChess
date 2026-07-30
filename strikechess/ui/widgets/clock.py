from enum import StrEnum

from PySide6.QtCore import QElapsedTimer, QSize, Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import QLCDNumber


CountdownIntervalMilliseconds: Final[int] = 30
CountdownThresholdSeconds: Final[float] = CountdownIntervalMilliseconds / 1000


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
        self._countdown_timer.setInterval(CountdownIntervalMilliseconds)
        self._countdown_timer.setTimerType(Qt.TimerType.PreciseTimer)
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
        """Set time to values from settings."""
        self.time: float = self._settings.value("clock", "time")
        self.increment: float = self._settings.value("clock", "increment")
        self._show_time()

    def start_timer(self) -> None:
        """Start tracking elapsed time, then start timer countdown."""
        self._elapsed_timer.start()
        self._countdown_timer.start()

    def stop_timer(self) -> None:
        """Stop timer countdown."""
        self._countdown_timer.stop()

    def add_increment(self) -> None:
        """Add increment to time on clock."""
        self.time += self.increment
        self._show_time()

    def zero_time(self) -> None:
        """Set remaining time to zero and stop timer countdown."""
        self.time = 0.0
        self.stop_timer()
        self._show_time()

    @Slot()
    def update_time(self) -> None:
        """Update remaining time and check for timer expiration."""
        if self.time < CountdownThresholdSeconds:
            self.time = 0.0
            self._countdown_timer.stop()
            self.expired.emit()
        else:
            elapsed_time: float = self._elapsed_timer.restart() / 1000.0
            self.time -= elapsed_time

        self._show_time()

    def _show_time(self) -> None:
        """Show time on clock in hh:mm:ss or mm:ss format."""
        time_as_text: str = self._format_time()
        self.setDigitCount(len(time_as_text))
        self.display(time_as_text)

    def _format_time(self) -> str:
        """Get time on clock in hh:mm:ss or mm:ss format."""
        time_in_seconds: int = max(0, round(self.time))
        hours, remaining_time = divmod(time_in_seconds, 3600)
        minutes, seconds = divmod(remaining_time, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}" if hours else f"{minutes:02}:{seconds:02}"
