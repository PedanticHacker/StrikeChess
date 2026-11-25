from platform import system

from chess.engine import EngineError
from PySide6.QtCore import QObject, Signal, Slot

from strikechess.utils import ask_question, show_open_file_manager, show_warning


class EngineLoader(QObject):
    """Loading and unloading UCI engines."""

    engine_loaded: ClassVar[Signal] = Signal()
    engine_changed: ClassVar[Signal] = Signal()

    def __init__(
        self,
        parent: QWidget,
        engine: EngineService,
        engine_analysis: EngineAnalysis,
    ) -> None:
        super().__init__(parent)

        self._engine: EngineService = engine
        self._engine_analysis: EngineAnalysis = engine_analysis

        self._engine.error_occurred.connect(self.load_default_engine_on_error)

    def load_engine(self) -> None:
        """Show file manager to select and load engine."""
        engine_filter: str = self.tr("UCI engine (*.exe)") if system() == "Windows" else ""
        file_path: str | None = show_open_file_manager(
            self.parent(),
            self.tr("Load Engine"),
            engine_filter,
        )

        if file_path is None:
            return

        try:
            self._engine_analysis.stop()

            self._engine.load_file(file_path)

            self.engine_loaded.emit()
            self.engine_changed.emit()

        except EngineError as error:
            show_warning(self.parent(), self.tr("Engine Error"), str(error))

    def unload_engine(self) -> None:
        """Prompt whether to unload currently loaded engine."""
        if not ask_question(
            self.parent(),
            self.tr("Unload Engine"),
            self.tr("Are you sure you want to unload the engine?"),
        ):
            return

        self._unload_engine()

    @Slot()
    def load_default_engine_on_error(self) -> None:
        """Load default engine if possible and warn about failed one."""
        if not self._engine.is_loaded():
            return

        self._unload_engine()

        self._engine.load_default_engine()

        if not self._engine.is_loaded():
            show_warning(
                self.parent(),
                self.tr("Engine Error"),
                self.tr(
                    "Cannot communicate with UCI engine.\n\n"
                    "The engine may have crashed.\n"
                    "Relaunch StrikeChess or load an engine."
                ),
            )
            return

        self.engine_changed.emit()

        show_warning(
            self.parent(),
            self.tr("Engine Error"),
            self.tr(
                "Cannot communicate with UCI engine.\n\n"
                "The engine may have crashed.\n"
                "Stockfish has been loaded."
            ),
        )

        self.engine_loaded.emit()

    def _unload_engine(self) -> None:
        """Stop analysis, terminate engine, and send engine change."""
        self._engine_analysis.stop()

        self._engine.terminate()
        self.engine_changed.emit()
