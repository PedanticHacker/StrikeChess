from functools import partial

from PySide6.QtGui import QColor
from chess import BLACK, Color, Move, WHITE
from PySide6.QtCore import QThreadPool, QTimer, Slot
from PySide6.QtWidgets import QDialog, QGridLayout, QLabel, QMainWindow, QWidget

from strikechess.ui.pgn_files import PgnFiles
from strikechess.ui.sounds import SoundPlayer
from strikechess.ui.table import TableModel, TableView
from strikechess.ui.menus import LanguageMenu, ThemeMenu
from strikechess.ui.bars import MenuBar, StatusBar, ToolBar
from strikechess.ui.board_orientation import BoardOrientation
from strikechess.ui.engine import EngineAnalysis, EngineLoader
from strikechess.ui.dialogs import PromotionDialog, SettingsDialog
from strikechess.services import EngineService, GameService, SettingsService
from strikechess.ui.widgets import ChessClock, EvaluationBar, FenEditor, SvgBoard
from strikechess.utils import (
    root_path,
    elide_name,
    show_about,
    ask_question,
    create_action,
    create_svg_icon,
    install_translators,
    create_color_property,
)


ScrollThrottleIntervalInMilliseconds: Final[int] = 180


class MainWindow(QMainWindow):
    """Main app window."""

    icon_color = create_color_property("_icon_color")
    disabled_icon_color = create_color_property("_disabled_icon_color")

    def __init__(self) -> None:
        super().__init__()

        self._icon_color: QColor = QColor()
        self._disabled_icon_color: QColor = QColor()

        # App settings
        self._settings: SettingsService = SettingsService()

        # Language
        install_translators(self._settings.value("ui", "language"))

        # Core services
        self._game: GameService = GameService(self._settings)
        self._engine: EngineService = EngineService(self._settings)

        self._engine_fen: str = self._game.fen

        # Sound player
        self._sound_player: SoundPlayer = SoundPlayer(self._game)

        # Widgets
        self._fen_editor: FenEditor = FenEditor(self._game)
        self._evaluation_bar: EvaluationBar = EvaluationBar()
        self._table_model: TableModel = TableModel(self._game.moves)
        self._table_view: TableView = TableView(self._table_model)
        self._board: SvgBoard = SvgBoard(self._game, self._engine, self._settings)
        self._black_clock: ChessClock = ChessClock(BLACK, self._game, self._settings)
        self._white_clock: ChessClock = ChessClock(WHITE, self._game, self._settings)

        # Labels
        self._engine_analysis_label: QLabel = QLabel()
        self._engine_analysis_label.setFixedWidth(200)
        self._engine_analysis_label.setObjectName("engineAnalysis")

        self._engine_name_label: QLabel = QLabel(elide_name(self._engine.name))
        self._engine_name_label.setFixedWidth(200)
        self._engine_name_label.setObjectName("engineName")

        self._notifications_label: QLabel = QLabel()
        self._notifications_label.setObjectName("notifications")

        self._human_name_label: QLabel = QLabel(
            elide_name(self._settings.value("human", "name") or self.tr("Player"))
        )
        self._human_name_label.setFixedWidth(200)
        self._human_name_label.setObjectName("humanName")

        # Timers
        self._scroll_throttle_timer: QTimer = QTimer(self)
        self._scroll_throttle_timer.setSingleShot(True)
        self._scroll_throttle_timer.setInterval(ScrollThrottleIntervalInMilliseconds)

        # UI setup
        self._create_layout()
        self._create_handlers()

        self._create_actions()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._connect_signals_to_slots()

        self.update_actions()
        self._board_orientation.orient_board_for_human()
        self.apply_theme(self._settings.value("ui", "theme"))

    def offer_new_game(self) -> None:
        """Start new game, prompt if game is in progress."""
        if self._game.is_in_progress():
            if not ask_question(
                self,
                self.tr("New Game"),
                self.tr(
                    "You will lose the current game.\n"
                    "Start a new game anyway?"
                ),
            ):
                return

        self._game.reset()
        self.reset_ui_state()

        self._board_orientation.orient_board_for_human()

    def play_move_now(self) -> None:
        """Force engine to play move on current turn."""
        self._board.clear_arrow()

        self._engine_analysis.stop()
        self.request_engine_move(force=True)

    def quit(self) -> None:
        """Quit app by closing main window."""
        self.close()

    def show_about(self) -> None:
        """Show About dialog."""
        show_about(self)

    def show_settings_dialog(self) -> None:
        """Show dialog to edit settings."""
        settings_dialog: SettingsDialog = SettingsDialog(self, self._settings)

        if not self._engine.is_loaded():
            settings_dialog.disable_engine_group()

        if self._game.is_in_progress():
            settings_dialog.disable_human_name_group()
            settings_dialog.disable_time_control_group()

        if settings_dialog.exec() == QDialog.DialogCode.Accepted:
            self._apply_saved_settings()

    @Slot(str)
    def apply_theme(self, file_name: str) -> None:
        """Apply QSS theme based on `file_name` and show theme name."""
        file_path: Path = root_path() / "assets" / "themes" / f"{file_name}.qss"

        with open(file_path, encoding="utf-8") as qss_file:
            self.setStyleSheet(qss_file.read())

        self.ensurePolished()
        self._tool_bar.tint_icons(self._icon_color, self._disabled_icon_color)
        self._status_bar.show_theme_name(self._theme_menu.theme_name(file_name))

        self._settings.set_value("ui", "theme", file_name)

    @Slot(str)
    def apply_validated_fen(self, fen: str) -> None:
        """Apply position from `fen`, prompt if game is in progress."""
        if self._game.is_in_progress():
            if not ask_question(
                self,
                self.tr("Apply FEN"),
                self.tr(
                    "You will lose the current game.\n"
                    "Apply the FEN anyway?"
                ),
            ):
                self._show_fen()
                return

        self._game.fen = fen
        self.reset_ui_state()

    @Slot(Color)
    def expire_clock_for(self, player_color: Color) -> None:
        """End game when clock of `player_color` expires."""
        self._black_clock.stop_timer()
        self._white_clock.stop_timer()

        self._game.player_with_expired_clock = player_color
        self._notifications_label.setText(self._game.result())

        self._engine.stop_ponder()

        self._board.disable_interaction()

        self._sound_player.play_game_over()

        self.update_actions()

    @Slot(Move)
    def play_engine_move(self, move: Move) -> None:
        """Play engine's `move` or discard it when stale."""
        self._engine.is_thinking = False

        if not self._settings.value("engine", "is_ponder_enabled"):
            self._engine.stop_ponder()

        is_game_over_by_result: bool = self._game.is_over_by_result()

        if self._game.fen != self._engine_fen or is_game_over_by_result:
            if is_game_over_by_result:
                self._notifications_label.setText(self._game.result())
            else:
                self._notifications_label.clear()

            self.update_actions()

            self.request_engine_move()
            self._engine.stop_ponder()
            return

        self._play_move(move)

    @Slot(Move)
    def play_human_move(self, move: Move) -> None:
        """Play human's `move` with optional promotion."""
        if move.promotion is not None:
            promotion_dialog: PromotionDialog = PromotionDialog(self, self._game.turn)
            promotion_dialog.exec()
            promotion_dialog.deleteLater()

            move.promotion = promotion_dialog.piece_type

            if move.promotion is None or self._game.is_over_by_result():
                return

        self._play_move(move)

    @Slot()
    def request_engine_move(self, force: bool = False) -> None:
        """Request engine to play move if loaded, on turn, or forced."""
        if not self._engine.is_loaded():
            return

        if self._engine.is_thinking:
            return

        if self._game.is_over_by_result():
            return

        if self._game.is_viewing_history and not force:
            return

        if self._game.is_engine_to_move() or force:
            self._engine_fen = self._game.fen

            self._engine.is_thinking = True
            self._notifications_label.setText(self.tr("Thinking..."))

            self.update_actions()

            QThreadPool.globalInstance().start(
                partial(
                    self._engine.play_move,
                    board=self._game.board_copy(),
                    black_time=self._black_clock.time,
                    white_time=self._white_clock.time,
                    black_increment=self._black_clock.increment,
                    white_increment=self._white_clock.increment,
                )
            )

    @Slot()
    def reset_ui_state(self) -> None:
        """Reset UI to default state for current game."""
        self._black_clock.reset()
        self._white_clock.reset()

        self._engine.stop_ponder()

        self._board.clear_arrow()
        self._status_bar.clear_opening()

        self._update_ui_state()

    @Slot()
    def show_engine_name(self) -> None:
        """Show name of engine, shortened to fit its label."""
        self._engine_name_label.setText(elide_name(self._engine.name))

    @Slot(int)
    def show_historical_move(self, move_index: int) -> None:
        """Show position from historical move at `move_index`."""
        is_last_move: bool = move_index == len(self._game.moves) - 1 or not self._game.moves
        is_returning_from_history: bool = is_last_move and self._game.is_viewing_history

        self._game.is_viewing_history = not is_last_move

        if move_index < 0:
            self._game.set_root_position()
            self._status_bar.clear_opening()
        else:
            self._game.update_state(move_index)

        if not is_last_move:
            self._black_clock.stop_timer()
            self._white_clock.stop_timer()

        self._engine_analysis.stop()

        self._show_fen()
        self._status_bar.show_opening()

        self._board.set_last_move_arrow()

        if is_returning_from_history:
            self.request_engine_move()

    @Slot()
    def update_actions(self) -> None:
        """Update availability of actions based on game state."""
        is_engine_thinking: bool = self._engine.is_thinking
        is_engine_analyzing: bool = self._engine.is_analyzing
        is_engine_not_loaded: bool = not self._engine.is_loaded()

        is_game_in_progress: bool = self._game.is_in_progress()
        is_game_over_by_rules: bool = self._game.is_over_by_rules()
        is_game_over_by_result: bool = self._game.is_over_by_result()

        is_last_move: bool = self._table_view.is_last_move()

        should_disable_play_move_now: bool = (
            is_engine_thinking
            or is_engine_not_loaded
            or is_game_over_by_rules
            or is_game_over_by_result
        )
        should_disable_start_analysis: bool = (
            is_engine_thinking
            or is_engine_analyzing
            or is_engine_not_loaded
            or (is_game_over_by_rules and is_last_move)
        )

        self.save_as_pgn_action.setEnabled(is_game_in_progress)

        self.stop_analysis_action.setEnabled(is_engine_analyzing)
        self.start_analysis_action.setDisabled(should_disable_start_analysis)

        self.unload_engine_action.setDisabled(is_engine_not_loaded)
        self.play_move_now_action.setDisabled(should_disable_play_move_now)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Prompt whether to quit app."""
        if ask_question(self, self.tr("Quit"), self.tr("Are you sure you want to quit?")):
            event.accept()
        else:
            event.ignore()

    def showEvent(self, event: QShowEvent) -> None:
        """Request engine move when main window is shown."""
        self.request_engine_move()

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Select previous or next move on wheel scroll."""
        if not self._scroll_throttle_timer.isActive():
            scroll_step: int = event.angleDelta().y()

            if scroll_step > 0:
                self._table_view.select_previous_move()
            elif scroll_step < 0:
                self._table_view.select_next_move()

            self._scroll_throttle_timer.start()

    def _apply_saved_settings(self) -> None:
        """Act on edited settings being saved."""
        if not self._game.is_in_progress():
            self._black_clock.reset()
            self._white_clock.reset()

            self._human_name_label.setText(
                elide_name(self._settings.value("human", "name") or self.tr("Player"))
            )

        if not self._settings.value("engine", "is_ponder_enabled"):
            self._engine.stop_ponder()

        self.request_engine_move()

        self._status_bar.show_engine_ponder()
        self._board_orientation.orient_board_for_human()

    def _connect_signals_to_slots(self) -> None:
        """Connect component signals to corresponding slot methods."""

        # Clocks
        self._black_clock.expired.connect(self.expire_clock_for)
        self._white_clock.expired.connect(self.expire_clock_for)

        # Engine
        self._engine.move_played.connect(self.play_engine_move)
        self._engine_analysis.started.connect(self.update_actions)
        self._engine_analysis.stopped.connect(self.update_actions)
        self._engine_loader.engine_changed.connect(self.update_actions)
        self._engine_loader.engine_changed.connect(self.show_engine_name)
        self._engine_loader.engine_loaded.connect(self.request_engine_move)
        self._engine_loader.engine_changed.connect(self._status_bar.show_engine_ponder)

        # Game
        self._game.move_played.connect(self.play_human_move)
        self._pgn_files.game_loaded.connect(self.reset_ui_state)

        # Widgets
        self._theme_menu.theme_selected.connect(self.apply_theme)
        self._fen_editor.fen_validated.connect(self.apply_validated_fen)
        self._table_view.move_selected.connect(self.show_historical_move)

    def _create_actions(self) -> None:
        """Create menu item and tool bar button actions."""
        self.about_action: QAction = create_action(
            shortcut="F1",
            handler=self.show_about,
            icon=create_svg_icon("about"),
            name=self.tr("About StrikeChess"),
            status_tip=self.tr("Shows the About dialog."),
        )
        self.flip_action: QAction = create_action(
            shortcut="Ctrl+F",
            name=self.tr("Flip"),
            icon=create_svg_icon("flip"),
            handler=self._board_orientation.flip,
            status_tip=self.tr("Flips the board orientation and board-related elements."),
        )
        self.load_engine_action: QAction = create_action(
            shortcut="Ctrl+L",
            name=self.tr("Load engine..."),
            icon=create_svg_icon("load-engine"),
            handler=self._engine_loader.load_engine,
            status_tip=self.tr("Shows the file manager to select and load an engine."),
        )
        self.load_from_pgn_action: QAction = create_action(
            shortcut="Ctrl+O",
            name=self.tr("Load from PGN..."),
            handler=self._pgn_files.load_from_pgn,
            icon=create_svg_icon("load-from-pgn"),
            status_tip=self.tr("Loads a game from PGN, prompts if a game is in progress."),
        )
        self.new_game_action: QAction = create_action(
            shortcut="Ctrl+N",
            name=self.tr("New game"),
            handler=self.offer_new_game,
            icon=create_svg_icon("new-game"),
            status_tip=self.tr("Starts a new game, prompts if a game is in progress."),
        )
        self.play_move_now_action: QAction = create_action(
            shortcut="Ctrl+P",
            handler=self.play_move_now,
            name=self.tr("Play move now"),
            icon=create_svg_icon("play-move-now"),
            status_tip=self.tr("Forces the engine to play a move on the current turn."),
        )
        self.quit_action: QAction = create_action(
            handler=self.quit,
            shortcut="Ctrl+Q",
            name=self.tr("Quit"),
            icon=create_svg_icon("quit"),
            status_tip=self.tr("Quits the app by closing the main window."),
        )
        self.save_as_pgn_action: QAction = create_action(
            shortcut="Ctrl+S",
            name=self.tr("Save as PGN..."),
            handler=self._pgn_files.save_as_pgn,
            icon=create_svg_icon("save-as-pgn"),
            status_tip=self.tr("Saves the current game as PGN."),
        )
        self.show_settings_dialog_action: QAction = create_action(
            shortcut="F2",
            name=self.tr("Settings..."),
            icon=create_svg_icon("settings"),
            handler=self.show_settings_dialog,
            status_tip=self.tr("Shows a dialog to edit the settings."),
        )
        self.start_analysis_action: QAction = create_action(
            shortcut="F3",
            name=self.tr("Start analysis"),
            handler=self._engine_analysis.start,
            icon=create_svg_icon("start-analysis"),
            status_tip=self.tr("Starts analyzing the current position."),
        )
        self.stop_analysis_action: QAction = create_action(
            shortcut="F4",
            name=self.tr("Stop analysis"),
            handler=self._engine_analysis.stop,
            icon=create_svg_icon("stop-analysis"),
            status_tip=self.tr("Stops analyzing the current position."),
        )
        self.unload_engine_action: QAction = create_action(
            shortcut="Ctrl+U",
            name=self.tr("Unload engine"),
            icon=create_svg_icon("unload-engine"),
            handler=self._engine_loader.unload_engine,
            status_tip=self.tr("Prompts whether to unload the currently loaded engine."),
        )

    def _create_handlers(self) -> None:
        """Create PGN file, engine, and board orientation handlers."""
        self._pgn_files: PgnFiles = PgnFiles(self, self._game, self._engine, self._settings)

        self._engine_analysis: EngineAnalysis = EngineAnalysis(
            self._game,
            self._engine,
            self._board,
            self._black_clock,
            self._white_clock,
            self._evaluation_bar,
            self._notifications_label,
            self._engine_analysis_label,
        )
        self._engine_loader: EngineLoader = EngineLoader(self, self._engine, self._engine_analysis)

        self._board_orientation: BoardOrientation = BoardOrientation(
            self._grid_layout,
            self._board,
            self._black_clock,
            self._white_clock,
            self._evaluation_bar,
            self._human_name_label,
            self._engine_name_label,
            self._settings,
        )

    def _create_layout(self) -> None:
        """Create grid layout with fixed widget placement."""
        self._grid_layout: QGridLayout = QGridLayout()

        self._grid_layout.addWidget(self._board, 1, 2, 4, 1)
        self._grid_layout.addWidget(self._table_view, 1, 3, 4, 1)
        self._grid_layout.addWidget(self._evaluation_bar, 1, 4, 4, 1)
        self._grid_layout.addWidget(self._engine_analysis_label, 1, 5, 4, 1)
        self._grid_layout.addWidget(self._fen_editor, 5, 2)
        self._grid_layout.addWidget(self._notifications_label, 5, 3)

        self._grid_layout.setRowStretch(3, 1)

        self._grid_layout.setColumnStretch(0, 1)
        self._grid_layout.setColumnStretch(6, 1)

        for widget in (self._evaluation_bar, self._engine_analysis_label):
            size_policy: QSizePolicy = widget.sizePolicy()
            size_policy.setRetainSizeWhenHidden(True)
            widget.setSizePolicy(size_policy)
            widget.hide()

        central_widget: QWidget = QWidget()
        central_widget.setLayout(self._grid_layout)
        self.setCentralWidget(central_widget)

    def _create_menu_bar(self) -> None:
        """Create menu bar with actions in separate menus."""
        self._theme_menu: ThemeMenu = ThemeMenu(self)
        self._language_menu: LanguageMenu = LanguageMenu(self, self._settings)

        self._menu_bar: MenuBar = MenuBar(self, self._theme_menu, self._language_menu)
        self.setMenuBar(self._menu_bar)

    def _create_status_bar(self) -> None:
        """Create status bar for opening, theme, and engine ponder."""
        self._status_bar: StatusBar = StatusBar(self._game, self._engine, self._settings)
        self.setStatusBar(self._status_bar)

    def _create_tool_bar(self) -> None:
        """Create immovable tool bar with visually separated buttons."""
        self._tool_bar: ToolBar = ToolBar(self)
        self.addToolBar(self._tool_bar)

    def _play_move(self, move: Move) -> None:
        """Play `move` and update UI state."""
        if not self._game.is_legal(move):
            return

        self._sound_player.play(move)

        self._game.push(move)
        self._black_clock.add_increment()
        self._white_clock.add_increment()

        self._engine.is_thinking = False

        self._update_ui_state()

    def _show_fen(self) -> None:
        """Show FEN in editor."""
        self._table_view.setFocus()
        self._fen_editor.hide_warning()
        self._fen_editor.setText(self._game.fen)

    def _update_ui_state(self) -> None:
        """Update UI to reflect current game state."""
        self._game.is_viewing_history = False

        self._board.update()
        self._board.enable_interaction()

        self._table_model.update_view()
        self._table_view.select_last_move()

        self._engine_analysis.stop()

        self._show_fen()
        self._status_bar.show_opening()

        if self._game.is_over_by_result():
            self._black_clock.stop_timer()
            self._white_clock.stop_timer()

            self._engine.stop_ponder()

            self._board.disable_interaction()
            return

        self.request_engine_move()
