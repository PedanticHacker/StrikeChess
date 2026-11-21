from PySide6.QtCore import Slot
from PySide6.QtWidgets import QLabel, QStatusBar

from strikechess.utils import find_opening


class StatusBar(QStatusBar):
    """Status bar for opening, theme, and engine ponder."""

    def __init__(
        self,
        game: GameService,
        engine: EngineService,
        settings: SettingsService,
    ) -> None:
        super().__init__()

        self._game: GameService = game
        self._engine: EngineService = engine
        self._settings: SettingsService = settings

        self._opening_label: QLabel = QLabel()
        self._theme_name_label: QLabel = QLabel()
        self._engine_ponder_label: QLabel = QLabel()

        self.addWidget(self._opening_label)
        self.addPermanentWidget(self._theme_name_label)
        self.addPermanentWidget(self._engine_ponder_label)

        self.show_engine_ponder()

    def show_opening(self) -> None:
        """Show name of current opening."""
        opening_name: str | None = find_opening(self._game.fen)

        if opening_name is not None:
            self._opening_label.setText(opening_name)

    def clear_opening(self) -> None:
        """Clear name of previously shown opening."""
        self._opening_label.clear()

    def show_theme_name(self, theme_name: str) -> None:
        """Show `theme_name` as name of applied theme."""
        theme_caption: str = self.tr("Theme")
        self._theme_name_label.setText(f"{theme_caption}: {theme_name}")

    @Slot()
    def show_engine_ponder(self) -> None:
        """Show engine ponder state, unavailable without engine."""
        is_engine_loaded: bool = self._engine.is_loaded()
        is_ponder_enabled: bool = self._settings.value("engine", "is_ponder_enabled")

        if not is_engine_loaded:
            ponder_state: str = self.tr("(unavailable)")
        elif is_ponder_enabled:
            ponder_state = self.tr("Enabled")
        else:
            ponder_state = self.tr("Disabled")

        ponder_caption: str = self.tr("Engine ponder")
        self._engine_ponder_label.setEnabled(is_engine_loaded)
        self._engine_ponder_label.setText(f"{ponder_caption}: {ponder_state}")
