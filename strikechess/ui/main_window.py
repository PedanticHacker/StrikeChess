from functools import partial
from platform import system
from re import sub

from chess import BLACK, Move, WHITE
from chess.engine import EngineError, Score
from PySide6.QtCore import QThreadPool, QTimer, Slot
from PySide6.QtGui import QAction, QCloseEvent, QIcon, QWheelEvent
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QToolBar,
    QWidget,
)

from strikechess.services import (
    EngineService,
    GameService,
    PgnService,
    SettingsService,
)
from strikechess.ui.dialogs import PromotionDialog, SettingsDialog
from strikechess.ui.sounds import SoundPlayer
from strikechess.ui.table import TableModel, TableView
from strikechess.ui.themes import ClockStyleSheet, THEME_SWATCH, ThemeName
from strikechess.ui.widgets import (
    DigitalClock,
    EvaluationBar,
    FenEditor,
    SvgBoard,
)
from strikechess.utils import (
    ask_question,
    create_action,
    create_colored_icon,
    create_svg_icon,
    find_opening,
    install_translators,
    read_pgn_file,
    read_theme_stylesheet,
    save_with_file_manager,
    show_about,
    show_file_manager,
    show_info,
    show_warning,
    write_pgn_file,
)


ScrollThrottleIntervalMilliseconds: Final[int] = 180


class MainWindow(QMainWindow):
    """Main app window."""

    def __init__(self) -> None:
        super().__init__()

        # App settings
        self._settings: SettingsService = SettingsService()

        # Language
        self.apply_language()

        # Core services
        self._game: GameService = GameService(self._settings)
        self._engine: EngineService = EngineService(self._settings)
        self._pgn: PgnService = PgnService()

        # Sound player
        self._sound_player: SoundPlayer = SoundPlayer(self._game)

        # Widgets
        self._evaluation_bar: EvaluationBar = EvaluationBar(self._settings)
        self._board: SvgBoard = SvgBoard(self._game, self._engine, self._settings)
        self._black_clock: DigitalClock = DigitalClock(ClockStyleSheet.Black, self._settings)
        self._white_clock: DigitalClock = DigitalClock(ClockStyleSheet.White, self._settings)
        self._table_model: TableModel = TableModel(self._game.moves)
        self._table_view: TableView = TableView(self._table_model)
        self._fen_editor: FenEditor = FenEditor(self._game)

        # Labels
        self._engine_analysis_label: QLabel = QLabel()
        self._engine_analysis_label.setFixedWidth(200)
        self._engine_analysis_label.setObjectName("engineAnalysis")

        self._engine_name_label: QLabel = QLabel(self._engine.name)
        self._engine_name_label.setObjectName("engineName")

        self._notifications_label: QLabel = QLabel()
        self._notifications_label.setObjectName("notifications")

        self._human_name_label: QLabel = QLabel(
            self._settings.value("human", "name") or self.tr("Player")
        )
        self._human_name_label.setObjectName("humanName")

        self._openings_label: QLabel = QLabel()
        self._theme_name_label: QLabel = QLabel()

        # Timers
        self._scroll_throttle_timer: QTimer = QTimer(self)
        self._scroll_throttle_timer.setSingleShot(True)
        self._scroll_throttle_timer.setInterval(ScrollThrottleIntervalMilliseconds)

        # UI setup
        self.create_layout()
        self.create_actions()
        self.update_actions()
        self.create_menu_bar()
        self.create_tool_bar()
        self.create_status_bar()
        self.orient_board_for_human()
        self.connect_signals_to_slots()
        self.apply_theme(self._settings.value("ui", "theme"))

    def connect_signals_to_slots(self) -> None:
        """Connect component signals to corresponding slot methods."""

        # Clocks
        self._black_clock.expired.connect(self.expire_clock_for_black)
        self._white_clock.expired.connect(self.expire_clock_for_white)

        # Engine
        self._engine.best_move_analyzed.connect(self.show_best_move_arrow)
        self._engine.move_played.connect(self.play_move)
        self._engine.score_analyzed.connect(self.animate_evaluation)
        self._engine.variation_analyzed.connect(self.show_engine_variation)

        # Game
        self._game.move_played.connect(self.play_move)

        # Widgets
        self._fen_editor.fen_validated.connect(self.apply_validated_fen)
        self._table_view.move_selected.connect(self.show_historical_move)

    def create_actions(self) -> None:
        """Create menu item and tool bar button actions."""
        self.about_action: QAction = create_action(
            icon=create_svg_icon("about"),
            name=self.tr("About StrikeChess"),
            handler=self.show_about,
            shortcut="F1",
            status_tip=self.tr("Shows the About dialog."),
        )
        self.flip_action: QAction = create_action(
            icon=create_svg_icon("flip"),
            name=self.tr("Flip"),
            handler=self.flip,
            shortcut="Ctrl+F",
            status_tip=self.tr("Flips board orientation and board-related elements."),
        )
        self.load_engine_action: QAction = create_action(
            icon=create_svg_icon("load-engine"),
            name=self.tr("Load engine..."),
            handler=self.load_engine,
            shortcut="Ctrl+L",
            status_tip=self.tr("Shows the file manager to select and load an engine."),
        )
        self.load_from_pgn_action: QAction = create_action(
            icon=create_svg_icon("load-from-pgn"),
            name=self.tr("Load from PGN..."),
            handler=self.load_from_pgn,
            shortcut="Ctrl+O",
            status_tip=self.tr("Loads a game from PGN, prompts if a game is in progress."),
        )
        self.new_game_action: QAction = create_action(
            icon=create_svg_icon("new-game"),
            name=self.tr("New game"),
            handler=self.offer_new_game,
            shortcut="Ctrl+N",
            status_tip=self.tr("Starts a new game, prompts if a game is in progress."),
        )
        self.play_move_now_action: QAction = create_action(
            icon=create_svg_icon("play-move-now"),
            name=self.tr("Play move now"),
            handler=self.play_move_now,
            shortcut="Ctrl+P",
            status_tip=self.tr("Forces the engine to play a move on the current turn."),
        )
        self.quit_action: QAction = create_action(
            icon=create_svg_icon("quit"),
            name=self.tr("Quit..."),
            handler=self.quit,
            shortcut="Ctrl+Q",
            status_tip=self.tr("Quits the app by closing the main window."),
        )
        self.save_as_pgn_action: QAction = create_action(
            icon=create_svg_icon("save-as-pgn"),
            name=self.tr("Save as PGN..."),
            handler=self.save_as_pgn,
            shortcut="Ctrl+S",
            status_tip=self.tr("Saves the current game as PGN."),
        )
        self.show_settings_dialog_action: QAction = create_action(
            icon=create_svg_icon("settings"),
            name=self.tr("Settings..."),
            handler=self.show_settings_dialog,
            shortcut="F2",
            status_tip=self.tr("Shows a dialog to edit the settings."),
        )
        self.start_analysis_action: QAction = create_action(
            icon=create_svg_icon("start-analysis"),
            name=self.tr("Start analysis"),
            handler=self.start_analysis,
            shortcut="F3",
            status_tip=self.tr("Starts analyzing the current position."),
        )
        self.stop_analysis_action: QAction = create_action(
            icon=create_svg_icon("stop-analysis"),
            name=self.tr("Stop analysis"),
            handler=self.stop_analysis,
            shortcut="F4",
            status_tip=self.tr("Stops analyzing the current position."),
        )
        self.unload_engine_action: QAction = create_action(
            icon=create_svg_icon("unload-engine"),
            name=self.tr("Unload engine..."),
            handler=self.unload_engine,
            shortcut="Ctrl+U",
            status_tip=self.tr("Prompts whether to unload the currently loaded engine."),
        )

        self.create_theme_actions()
        self.create_language_actions()

    def create_theme_actions(self) -> None:
        """Create one theme-applying action per available theme."""
        theme_specs: list[tuple[ThemeName, str, str]] = [
            (
                ThemeName.DarkForest,
                self.tr("Dark Forest"),
                self.tr("Applies the Dark Forest theme."),
            ),
            (
                ThemeName.DarkMint,
                self.tr("Dark Mint"),
                self.tr("Applies the Dark Mint theme."),
            ),
            (
                ThemeName.DarkNebula,
                self.tr("Dark Nebula"),
                self.tr("Applies the Dark Nebula theme."),
            ),
            (
                ThemeName.DarkOcean,
                self.tr("Dark Ocean"),
                self.tr("Applies the Dark Ocean theme."),
            ),
            (
                ThemeName.LightForest,
                self.tr("Light Forest"),
                self.tr("Applies the Light Forest theme."),
            ),
            (
                ThemeName.LightMint,
                self.tr("Light Mint"),
                self.tr("Applies the Light Mint theme."),
            ),
            (
                ThemeName.LightNebula,
                self.tr("Light Nebula"),
                self.tr("Applies the Light Nebula theme."),
            ),
            (
                ThemeName.LightOcean,
                self.tr("Light Ocean"),
                self.tr("Applies the Light Ocean theme."),
            ),
        ]

        self._theme_actions: dict[ThemeName, QAction] = {}

        for index, (theme, name, status_tip) in enumerate(theme_specs, start=1):
            self._theme_actions[theme] = create_action(
                icon=create_colored_icon(THEME_SWATCH[theme]),
                name=name,
                handler=partial(self.apply_theme, theme),
                shortcut=f"Alt+{index}",
                status_tip=status_tip,
            )

    def create_language_actions(self) -> None:
        """Create one language-applying action per available language."""
        language_specs: list[tuple[str, str, str, str]] = [
            ("de", "german-flag", "Deutsch", self.tr("Applies the German language.")),
            (
                "en",
                "american-flag",
                "English",
                self.tr("Applies the American English language."),
            ),
            ("es", "spanish-flag", "Español", self.tr("Applies the Spanish language.")),
            ("it", "italian-flag", "Italiano", self.tr("Applies the Italian language.")),
        ]

        self._language_actions: list[QAction] = []

        for language_code, flag_icon, name, status_tip in language_specs:
            self._language_actions.append(
                create_action(
                    icon=create_svg_icon(flag_icon),
                    name=name,
                    handler=partial(self.change_language, language_code),
                    shortcut="",
                    status_tip=status_tip,
                )
            )

    def create_layout(self) -> None:
        """Create grid layout with fixed widget positions."""
        self._grid_layout: QGridLayout = QGridLayout()

        self._grid_layout.addWidget(self._black_clock, 1, 1)
        self._grid_layout.addWidget(self._board, 1, 2, 4, 1)
        self._grid_layout.addWidget(self._table_view, 1, 3, 4, 1)
        self._grid_layout.addWidget(self._evaluation_bar, 1, 4, 4, 1)
        self._grid_layout.addWidget(self._engine_analysis_label, 1, 5, 4, 1)
        self._grid_layout.addWidget(self._engine_name_label, 2, 1)
        self._grid_layout.addWidget(self._white_clock, 4, 1)
        self._grid_layout.addWidget(self._human_name_label, 5, 1)
        self._grid_layout.addWidget(self._fen_editor, 5, 2)
        self._grid_layout.addWidget(self._notifications_label, 5, 3)

        self._grid_layout.setRowStretch(0, 1)
        self._grid_layout.setRowStretch(3, 1)
        self._grid_layout.setRowStretch(6, 1)

        self._grid_layout.setColumnStretch(0, 1)
        self._grid_layout.setColumnStretch(6, 1)

        central_widget: QWidget = QWidget()
        central_widget.setLayout(self._grid_layout)
        self.setCentralWidget(central_widget)

    def create_menu_bar(self) -> None:
        """Create menu bar with actions in separate menus."""
        menu_bar: QMenuBar = self.menuBar()

        general_menu: QMenu = menu_bar.addMenu(self.tr("General"))
        theme_menu: QMenu = menu_bar.addMenu(self.tr("Theme"))
        language_menu: QMenu = menu_bar.addMenu(self.tr("Language"))
        edit_menu: QMenu = menu_bar.addMenu(self.tr("Edit"))
        help_menu: QMenu = menu_bar.addMenu(self.tr("Help"))

        general_menu.addAction(self.load_from_pgn_action)
        general_menu.addAction(self.save_as_pgn_action)
        general_menu.addSeparator()
        general_menu.addAction(self.load_engine_action)
        general_menu.addAction(self.unload_engine_action)
        general_menu.addSeparator()
        general_menu.addAction(self.quit_action)

        for theme_action in self._theme_actions.values():
            theme_menu.addAction(theme_action)

        for language_action in self._language_actions:
            language_menu.addAction(language_action)

        edit_menu.addAction(self.show_settings_dialog_action)

        help_menu.addAction(self.about_action)

    def create_status_bar(self) -> None:
        """Create status bar to show opening name and theme name."""
        self.statusBar().addWidget(self._openings_label)
        self.statusBar().addPermanentWidget(self._theme_name_label)

    def create_tool_bar(self) -> None:
        """Create immovable tool bar with visually separated buttons."""
        tool_bar: QToolBar = self.addToolBar(self.tr("Tool bar"))
        tool_bar.setMovable(False)

        tool_bar.addAction(self.quit_action)
        tool_bar.addSeparator()

        tool_bar.addAction(self.new_game_action)
        tool_bar.addAction(self.load_from_pgn_action)
        tool_bar.addAction(self.save_as_pgn_action)
        tool_bar.addSeparator()

        tool_bar.addAction(self.flip_action)
        tool_bar.addAction(self.play_move_now_action)
        tool_bar.addSeparator()

        tool_bar.addAction(self.start_analysis_action)
        tool_bar.addAction(self.stop_analysis_action)
        tool_bar.addSeparator()

        tool_bar.addAction(self.load_engine_action)
        tool_bar.addAction(self.unload_engine_action)
        tool_bar.addSeparator()

        tool_bar.addAction(self.show_settings_dialog_action)
        tool_bar.addAction(self.about_action)

    def apply_language(self) -> None:
        """Apply language from settings on app launch."""
        install_translators(self._settings.value("ui", "language"))

    def apply_saved_settings(self) -> None:
        """Act on edited settings being saved."""
        if not self._game.is_in_progress():
            self._black_clock.reset()
            self._white_clock.reset()

            self._human_name_label.setText(
                self._settings.value("human", "name") or self.tr("Player")
            )

        self.orient_board_for_human()
        self.request_engine_move()

    def apply_theme(self, file_name: str) -> None:
        """Apply QSS theme based on `file_name` and show theme name."""
        self.setStyleSheet(read_theme_stylesheet(file_name))

        self._settings.set_value("ui", "theme", file_name)
        theme_name: ThemeName = ThemeName(file_name)
        self._theme_name_label.setText(f"Theme: {theme_name.text}")

    def change_language(self, language_code: str) -> None:
        """Save new language setting and prompt for app relaunch."""
        if language_code == self._settings.value("ui", "language"):
            return

        self._settings.set_value("ui", "language", language_code)

        QMessageBox.information(
            self,
            self.tr("Relaunch"),
            self.tr("Please relaunch StrikeChess to apply the new language."),
        )

    def flip(self) -> None:
        """Flip board orientation and board-related elements."""
        is_white_at_bottom: bool = not self._settings.value("ui", "is_white_at_bottom")
        self._settings.set_value("ui", "is_white_at_bottom", is_white_at_bottom)
        self.orient_board_elements()

    def load_engine(self) -> None:
        """Show file manager to select and load engine."""
        engine_filter: str = self.tr("UCI engine (*.exe)") if system() == "Windows" else ""
        file_path: str | None = show_file_manager(self, self.tr("Load Engine"), engine_filter)

        if file_path is None:
            return

        try:
            self.stop_analysis()

            self._engine.load_file(file_path)
            self._engine_name_label.setText(self._engine.name)

            self.update_actions()
            self.request_engine_move()

        except EngineError as error:
            show_warning(self, self.tr("Engine Error"), str(error))

    def load_from_pgn(self) -> None:
        """Load game from PGN, prompt if game is in progress."""
        if self._game.is_in_progress():
            if not ask_question(
                self,
                self.tr("Load Game"),
                self.tr("You will lose the current game.\n" "Load from PGN anyway?"),
            ):
                return

        file_path: str | None = show_file_manager(
            self, self.tr("Load Game"), self.tr("PGN file (*.pgn)")
        )

        if file_path is None:
            return

        try:
            pgn_text: str = read_pgn_file(file_path)
            moves, fen, result = self._pgn.parse_pgn(pgn_text)

            self._game.reset()

            if fen is not None:
                self._game.fen = fen

            self._game.load_moves(moves)

            self._black_clock.reset()
            self._white_clock.reset()
            self._openings_label.clear()

            if result == "1-0" and not self._game.is_over_by_rules():
                self._game.expire_clock_for(BLACK)
                self._black_clock.zero_time()
            elif result == "0-1" and not self._game.is_over_by_rules():
                self._game.expire_clock_for(WHITE)
                self._white_clock.zero_time()

            self.update_ui_state()

            show_info(self, self.tr("Game loaded from PGN."))

        except ValueError as error:
            show_warning(self, self.tr("Load Error"), str(error))
        except (OSError, UnicodeDecodeError):
            show_warning(
                self,
                self.tr("File Error"),
                self.tr(
                    "Cannot read PGN.\n\n"
                    "The file may be locked or corrupted.\n"
                    "Check file permissions and try again."
                ),
            )

    def offer_new_game(self) -> None:
        """Start new game, prompt if game is in progress."""
        if self._game.is_in_progress():
            if not ask_question(
                self,
                self.tr("New Game"),
                self.tr("You will lose the current game.\n" "Start a new game anyway?"),
            ):
                return

        self.start_new_game()

    def orient_board_elements(self) -> None:
        """Orient board-related elements based on board orientation."""
        is_white_at_bottom: bool = self._settings.value("ui", "is_white_at_bottom")

        self._board.set_orientation(is_white_at_bottom)
        self._evaluation_bar.invert_fill(is_white_at_bottom)

        self.position_clocks(is_white_at_bottom)
        self.position_player_names(is_white_at_bottom)

    def orient_board_for_human(self) -> None:
        """Place human at bottom if playing against engine."""
        is_engine_white: bool = self._settings.value("engine", "is_white")
        self._settings.set_value("ui", "is_white_at_bottom", not is_engine_white)
        self.orient_board_elements()

    def play_move_now(self) -> None:
        """Force engine to play move on current turn."""
        self._game.clear_arrow()

        self.stop_analysis()
        self.request_engine_move(force=True)

    def position_clocks(self, is_white_at_bottom: bool) -> None:
        """Position clock widgets based on `is_white_at_bottom`."""
        self._grid_layout.removeWidget(self._black_clock)
        self._grid_layout.removeWidget(self._white_clock)

        if is_white_at_bottom:
            self._grid_layout.addWidget(self._black_clock, 1, 1)
            self._grid_layout.addWidget(self._white_clock, 4, 1)
        else:
            self._grid_layout.addWidget(self._white_clock, 1, 1)
            self._grid_layout.addWidget(self._black_clock, 4, 1)

    def position_player_names(self, is_white_at_bottom: bool) -> None:
        """Position player name labels based on `is_white_at_bottom`."""
        self._grid_layout.removeWidget(self._engine_name_label)
        self._grid_layout.removeWidget(self._human_name_label)

        is_engine_white: bool = self._settings.value("engine", "is_white")

        if is_white_at_bottom == is_engine_white:
            self._grid_layout.addWidget(self._human_name_label, 2, 1)
            self._grid_layout.addWidget(self._engine_name_label, 5, 1)
        else:
            self._grid_layout.addWidget(self._engine_name_label, 2, 1)
            self._grid_layout.addWidget(self._human_name_label, 5, 1)

    def quit(self) -> None:
        """Quit app by closing main window."""
        self.close()

    def request_engine_analysis(self) -> None:
        """Request engine to analyze current position."""
        self._engine.is_analyzing = True
        self._notifications_label.setText(self.tr("Analyzing..."))

        board: Board = self._game.board.copy()
        QThreadPool.globalInstance().start(lambda: self._engine.start_analysis(board))

    def request_engine_move(self, force: bool = False) -> None:
        """Request engine to play move if loaded, on turn, or forced."""
        if not self._engine.is_loaded():
            return

        if self._game.is_engine_to_move() or force:
            black_time: float = self._black_clock.time
            black_increment: float = self._black_clock.increment
            white_time: float = self._white_clock.time
            white_increment: float = self._white_clock.increment

            self._engine.is_thinking = True
            self._notifications_label.setText(self.tr("Thinking..."))

            self.update_actions()

            board: Board = self._game.board.copy()
            QThreadPool.globalInstance().start(
                lambda: self._engine.play_move(
                    board,
                    black_time=black_time,
                    black_increment=black_increment,
                    white_time=white_time,
                    white_increment=white_increment,
                )
            )

    def save_as_pgn(self) -> None:
        """Save current game as PGN."""
        engine_name: str = self._settings.value("engine", "name")
        is_engine_white: bool = self._settings.value("engine", "is_white")
        human_name: str = self._settings.value("human", "name") or self.tr("Player")
        suggested_file_name: str = self._pgn.suggest_file_name(
            human_name,
            engine_name,
            is_engine_white,
        )

        file_path: str | None = save_with_file_manager(
            self,
            self.tr("Save Game"),
            self.tr("PGN file (*.pgn)"),
            suggested_file_name,
        )

        if file_path is None:
            return

        try:
            pgn_text: str = self._pgn.export_to_pgn(
                self._game,
                human_name,
                engine_name,
                is_engine_white,
            )

            write_pgn_file(file_path, pgn_text)

            show_info(self, self.tr("Game saved successfully."))

        except ValueError as error:
            show_warning(self, self.tr("Save Error"), str(error))

        except OSError:
            show_warning(
                self,
                self.tr("Save Error"),
                self.tr(
                    "Cannot save game as PGN.\n\n"
                    "The destination may be read-only or full.\n"
                    "Try saving to a different location."
                ),
            )

    def show_about(self) -> None:
        """Show About dialog."""
        show_about(self)

    def show_fen(self) -> None:
        """Show FEN in editor."""
        self._fen_editor.clearFocus()
        self._fen_editor.hide_warning()
        self._fen_editor.setText(self._game.fen)

    def show_opening(self) -> None:
        """Show name of current opening."""
        opening_data: str | None = find_opening(self._game.fen) or find_opening(
            self._game.root_fen
        )

        if opening_data is not None:
            self._openings_label.setText(opening_data)

    def show_settings_dialog(self) -> None:
        """Show dialog to edit settings."""
        settings_dialog: SettingsDialog = SettingsDialog(self._settings)

        if not self._engine.is_loaded():
            settings_dialog.disable_engine_group()

        if self._game.is_in_progress():
            settings_dialog.disable_human_name_group()
            settings_dialog.disable_time_control_group()

        if settings_dialog.exec() == QDialog.DialogCode.Accepted:
            self.apply_saved_settings()

    def start_analysis(self) -> None:
        """Start analyzing current position."""
        self._black_clock.stop_timer()
        self._white_clock.stop_timer()

        self.request_engine_analysis()
        self.update_actions()

    def start_new_game(self) -> None:
        """Reset game and UI states to start new game."""
        self._game.is_viewing_history = False

        self._game.reset()
        self._table_model.reset()

        self._black_clock.reset()
        self._white_clock.reset()

        self._openings_label.clear()
        self._board.enable_interaction()

        self.show_fen()
        self.stop_analysis()

        self.orient_board_for_human()
        self.request_engine_move()

    def stop_analysis(self) -> None:
        """Stop analyzing current position."""
        self._engine.stop_analysis()
        self._notifications_label.clear()
        self._engine_analysis_label.clear()
        self._evaluation_bar.reset_appearance()

        self.update_clock_timers()
        self.update_actions()

    def terminate_engine(self) -> None:
        """Terminate engine process."""
        self._engine.terminate()

    def unload_engine(self) -> None:
        """Prompt whether to unload currently loaded engine."""
        if not ask_question(
            self,
            self.tr("Unload Engine"),
            self.tr("Are you sure you want to unload the engine?"),
        ):
            return

        self.stop_analysis()

        self._engine.unload()
        self._engine_name_label.setText(self.tr("(no engine)"))

        self._notifications_label.clear()

        self.update_actions()

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
            is_engine_not_loaded or is_game_over_by_result or is_game_over_by_rules
        )
        should_disable_start_analysis: bool = (
            is_engine_thinking
            or is_engine_analyzing
            or is_engine_not_loaded
            or (is_game_over_by_rules and is_last_move)
        )

        self.save_as_pgn_action.setEnabled(is_game_in_progress)

        self.start_analysis_action.setDisabled(should_disable_start_analysis)
        self.stop_analysis_action.setEnabled(is_engine_analyzing)

        self.unload_engine_action.setDisabled(is_engine_not_loaded)
        self.play_move_now_action.setDisabled(should_disable_play_move_now)

    def update_clock_timers(self) -> None:
        """Start/stop clocks and add increment based on current turn."""
        if self._game.is_over_by_result() or self._game.is_viewing_history:
            return

        if self._game.is_white_to_move():
            self._black_clock.stop_timer()
            self._white_clock.start_timer()
            if self._game.is_in_progress():
                self._black_clock.add_increment()
        else:
            self._white_clock.stop_timer()
            self._black_clock.start_timer()
            if self._game.is_in_progress():
                self._white_clock.add_increment()

    def update_ui_state(self) -> None:
        """Update UI to reflect current game state."""
        self._board.enable_interaction()

        self._table_model.update_view()
        self._table_view.select_last_move()

        self._game.is_viewing_history = False

        self.show_fen()
        self.show_opening()
        self.stop_analysis()

        if self._game.is_over_by_result():
            self._black_clock.stop_timer()
            self._white_clock.stop_timer()
            self._board.disable_interaction()
            self._notifications_label.setText(self._game.result())
            return

        self.request_engine_move()

    @Slot(Score)
    def animate_evaluation(self, score: Score) -> None:
        """Show position evaluation based on `score`."""
        self._evaluation_bar.animate(score)

    @Slot()
    def apply_validated_fen(self) -> None:
        """Apply new position based on validated FEN."""
        self._black_clock.reset()
        self._white_clock.reset()
        self._openings_label.clear()

        self.update_ui_state()

    @Slot()
    def expire_clock_for_black(self) -> None:
        """End game when Black's clock expires."""
        self._expire_clock(BLACK)

    @Slot()
    def expire_clock_for_white(self) -> None:
        """End game when White's clock expires."""
        self._expire_clock(WHITE)

    def _expire_clock(self, color: Color) -> None:
        """End game when clock of player with `color` expires."""
        self._black_clock.stop_timer()
        self._white_clock.stop_timer()

        self._sound_player.play_game_over()

        self._game.expire_clock_for(color)
        self._notifications_label.setText(self._game.result())

        self._board.disable_interaction()
        self._board.update()

        self.update_actions()

    @Slot(Move)
    def play_move(self, move: Move) -> None:
        """Play `move` with optional promotion and update UI."""
        is_promotion: bool = move.promotion is not None
        is_human_move: bool = self.sender() is self._game

        if is_promotion and is_human_move:
            promotion_dialog: PromotionDialog = PromotionDialog(self, self._game.turn)
            promotion_dialog.exec()

            move.promotion = promotion_dialog.piece_type

            if move.promotion is None:
                return

        self._sound_player.play(move)
        self._game.push(move)

        self._engine.is_thinking = False

        self.update_ui_state()

    @Slot(Move)
    def show_best_move_arrow(self, best_move: Move) -> None:
        """Show `best_move` as arrow marker on board."""
        self._game.set_arrow(best_move)

    @Slot(str)
    def show_engine_variation(self, variation: str) -> None:
        """Show formatted variation based on engine analysis."""
        formatted_variation: str = sub(r"(?=(\b\d+\.+))", "\n", variation).strip()
        self._engine_analysis_label.setText(formatted_variation)

    @Slot(int)
    def show_historical_move(self, move_index: int) -> None:
        """Show position from historical move at `move_index`."""
        self._game.is_viewing_history = True

        if move_index < 0:
            self._openings_label.clear()
            self._game.set_root_position()
        else:
            self._game.update_state(move_index)

        self._black_clock.stop_timer()
        self._white_clock.stop_timer()

        self.show_fen()
        self.show_opening()
        self.stop_analysis()

        if self._game.is_over_by_result():
            self._notifications_label.setText(self._game.result())

    def closeEvent(self, event: QCloseEvent) -> None:
        """Prompt whether to quit app."""
        if ask_question(self, self.tr("Quit"), self.tr("Are you sure you want to quit?")):
            self.terminate_engine()
            event.accept()
        else:
            event.ignore()

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle wheel scroll events with timer-based throttling."""
        if not self._scroll_throttle_timer.isActive():
            scroll_step: int = event.angleDelta().y()

            if scroll_step > 0:
                self._table_view.select_previous_move()
            elif scroll_step < 0:
                self._table_view.select_next_move()

            self._scroll_throttle_timer.start()
