from chess.engine import Score
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import QProgressBar


class EvaluationBar(QProgressBar):
    """Vertical bar with animatable chunk showing evaluation score."""

    def __init__(self, settings: SettingsService) -> None:
        super().__init__()

        self._settings: SettingsService = settings

        self._animation: QPropertyAnimation = QPropertyAnimation(self, b"value")
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._animation.valueChanged.connect(self.update)

        self.setFixedWidth(50)
        self.setRange(0, 1000)
        self.setOrientation(Qt.Orientation.Vertical)

        self.invert_fill(self._settings.value("ui", "is_white_at_bottom"))

    def invert_fill(self, invert: bool) -> None:
        """Invert from which end evaluation bar fills."""
        self.setInvertedAppearance(invert)

    def reset_appearance(self) -> None:
        """Rewind chunk and clear evaluation text."""
        self.reset()

    def animate(self, evaluation: Score) -> None:
        """Start animating chunk based on `evaluation`."""
        if evaluation.is_mate():
            moves_to_mate: int = evaluation.mate() or 0
            animation_value: int = 0 if moves_to_mate > 0 else 1000
            evaluation_text: str = f"M{abs(moves_to_mate)}"
        else:
            evaluation_score: int = evaluation.score() or 0
            animation_value = 500 - evaluation_score
            evaluation_text = f"{evaluation_score / 100 :.2f}"

        if animation_value < 0:
            animation_value = 0
        elif animation_value > 1000:
            animation_value = 1000

        self.setFormat(evaluation_text)
        self._animation.setEndValue(animation_value)
        self._animation.start()
