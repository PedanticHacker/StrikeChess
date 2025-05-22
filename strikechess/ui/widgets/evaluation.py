from chess.engine import Score
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import QProgressBar

from strikechess.utils import setting_value


class EvaluationBar(QProgressBar):
    """Vertical bar with animatable chunk diplaying evaluation score."""

    def __init__(self) -> None:
        super().__init__()

        self._animation: QPropertyAnimation = QPropertyAnimation(self, b"value")
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._animation.valueChanged.connect(self.update)

        self.hide()
        self.setRange(0, 1000)
        self.setOrientation(Qt.Orientation.Vertical)
        self.update_chunk_appearance(setting_value("board", "orientation"))

    def update_chunk_appearance(self, orientation: bool) -> None:
        """Update fill direction of chunk based on `orientation`."""
        self.setInvertedAppearance(orientation)

    def animate(self, evaluation: Score) -> None:
        """Animate chunk based on `evaluation`."""
        if evaluation.is_mate():
            moves_to_mate: int = evaluation.mate() or 0
            animation_value: int = 0 if moves_to_mate > 0 else 1000
            evaluation_text: str = f"M{moves_to_mate}"
        else:
            evaluation_score: int = evaluation.score() or 0
            animation_value = 500 - evaluation_score
            evaluation_text = f"{evaluation_score / 100 :.2f}"

        self.setFormat(evaluation_text)
        self._animation.setEndValue(animation_value)
        self._animation.start()
