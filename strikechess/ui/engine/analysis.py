from re import sub
from functools import partial

from chess import Move
from chess.engine import Score
from PySide6.QtCore import QObject, QThreadPool, Signal, Slot


class EngineAnalysis(QObject):
    """Engine analysis of current position."""

    started: ClassVar[Signal] = Signal()
    stopped: ClassVar[Signal] = Signal()

    def __init__(
        self,
        game: GameService,
        engine: EngineService,
        board: SvgBoard,
        black_clock: ChessClock,
        white_clock: ChessClock,
        evaluation_bar: EvaluationBar,
        notifications_label: QLabel,
        engine_analysis_label: QLabel,
    ) -> None:
        super().__init__()

        self._board: SvgBoard = board
        self._game: GameService = game
        self._engine: EngineService = engine
        self._black_clock: ChessClock = black_clock
        self._white_clock: ChessClock = white_clock
        self._evaluation_bar: EvaluationBar = evaluation_bar
        self._notifications_label: QLabel = notifications_label
        self._engine_analysis_label: QLabel = engine_analysis_label

        self._engine.score_analyzed.connect(self.animate_evaluation)
        self._engine.best_move_analyzed.connect(self.show_best_move_arrow)
        self._engine.variation_analyzed.connect(self.show_engine_variation)

    def start(self) -> None:
        """Start analyzing current position."""
        self._black_clock.stop_timer()
        self._white_clock.stop_timer()

        self._evaluation_bar.show()
        self._engine_analysis_label.show()

        self._request_analysis()
        self.started.emit()

    def stop(self) -> None:
        """Stop analyzing current position."""
        self._engine.stop_analysis()

        self._engine_analysis_label.clear()
        self._evaluation_bar.reset_appearance()

        self._evaluation_bar.hide()
        self._engine_analysis_label.hide()

        if self._game.is_over_by_result():
            self._notifications_label.setText(self._game.result())
        else:
            self._notifications_label.clear()

        self.stopped.emit()

        self._black_clock.update_countdown()
        self._white_clock.update_countdown()

    @Slot(Score)
    def animate_evaluation(self, score: Score) -> None:
        """Show position evaluation based on `score`."""
        if not self._engine.is_analyzing:
            return

        self._evaluation_bar.animate(score)

    @Slot(Move)
    def show_best_move_arrow(self, best_move: Move) -> None:
        """Show `best_move` as arrow marker on board."""
        if not self._engine.is_analyzing:
            return

        self._board.set_arrow(best_move)

    @Slot(str)
    def show_engine_variation(self, variation: str) -> None:
        """Show formatted variation based on engine analysis."""
        if not self._engine.is_analyzing:
            return

        formatted_variation: str = sub(r"(?=(\b\d+\.+))", "\n", variation).strip()
        self._engine_analysis_label.setText(formatted_variation)

    def _request_analysis(self) -> None:
        """Request engine to analyze current position."""
        self._engine.is_analyzing = True
        self._notifications_label.setText(self.tr("Analyzing..."))

        QThreadPool.globalInstance().start(
            partial(self._engine.start_analysis, self._game.board_copy())
        )
