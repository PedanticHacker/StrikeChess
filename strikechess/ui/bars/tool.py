from PySide6.QtWidgets import QToolBar

from strikechess.utils import create_tinted_icon


class ToolBar(QToolBar):
    """Immovable tool bar with visually separated buttons."""

    def __init__(self, main_window: MainWindow) -> None:
        super().__init__(main_window)

        self.setMovable(False)
        self.setWindowTitle(self.tr("Tool bar"))

        self.addAction(main_window.quit_action)
        self.addSeparator()

        self.addAction(main_window.new_game_action)
        self.addAction(main_window.load_from_pgn_action)
        self.addAction(main_window.save_as_pgn_action)
        self.addSeparator()

        self.addAction(main_window.flip_action)
        self.addAction(main_window.play_move_now_action)
        self.addSeparator()

        self.addAction(main_window.start_analysis_action)
        self.addAction(main_window.stop_analysis_action)
        self.addSeparator()

        self.addAction(main_window.load_engine_action)
        self.addAction(main_window.unload_engine_action)
        self.addSeparator()

        self.addAction(main_window.show_settings_dialog_action)
        self.addAction(main_window.about_action)

        self._icons: dict[QAction, QIcon] = {
            action: action.icon() for action in self.actions() if not action.isSeparator()
        }

    def tint_icons(self, color: QColor, disabled_color: QColor) -> None:
        """Tint icons in `color`, or in `disabled_color` if disabled."""
        for action, icon in self._icons.items():
            action.setIcon(create_tinted_icon(icon, color, disabled_color))
