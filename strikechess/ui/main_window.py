from enum import StrEnum
from functools import partial
from pathlib import Path
from platform import system
from re import sub

from chess import BLACK, Move, WHITE
from chess.engine import EngineError, Score
from PySide6.QtCore import QThreadPool, QTimer, Slot
from PySide6.QtGui import QAction, QCloseEvent, QWheelEvent
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
from strikechess.ui.widgets import (
    ClockStyleSheet,
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
    root_path,
    save_with_file_manager,
    show_about,
    show_file_manager,
    show_info,
    show_warning,
    write_pgn_file,
)


ScrollThrottleIntervalMilliseconds: Final[int] = 180


class ThemeName(StrEnum):
    """Available dark and light themes."""

    DarkForest = "dark-forest"
    DarkMint = "dark-mint"
    DarkNebula = "dark-nebula"
    DarkOcean = "dark-ocean"
    LightForest = "light-forest"
    LightMint = "light-mint"
    LightNebula = "light-nebula"
    LightOcean = "light-ocean"

    @property
    def text(self) -> str:
        """Theme name in title-cased format."""
        return self.value.replace("-", " ").title()


class MainWindow(QMainWindow):
    """Main app window."""

    def __init__(self) -> None:
        super().__init__()

        # App settings
        self._settings: SettingsService = SettingsService()

        # Language
        self._apply_language()

        # Core services
        self._game: GameService = GameService(self._settings)
        self._engine: EngineService = EngineService(self._settings)
        self._pgn: PgnService = PgnService()

        self._engine_fen: str = self._game.fen

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
        self._create_layout()
        self._create_actions()
        self._update_actions()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._orient_board_for_human()
        self._connect_signals_to_slots()
        self.apply_theme(self._settings.value("ui", "theme"))

    def apply_theme(self, file_name: str) -> None:
        """Apply QSS theme based on `file_name` and show theme name."""
        file_path: Path = root_path() / "assets" / "themes" / f"{file_name}.qss"

        with open(file_path, encoding="utf-8") as qss_file:
            self.setStyleSheet(qss_file.read())

        self._settings.set_value("ui", "theme", file_name)
        theme_name: ThemeName = ThemeName(file_name)
        self._theme_name_label.setText(f"{self.tr('Theme')}: {self.tr(theme_name.text)}")

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
        self._orient_board_elements()

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

            self._update_actions()
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

            self._update_ui_state()

            show_info(self, self.tr("Game loaded from PGN."))

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
        except ValueError as error:
            show_warning(self, self.tr("Load Error"), str(error))

    def offer_new_game(self) -> None:
        """Start new game, prompt if game is in progress."""
        if self._game.is_in_progress():
            if not ask_question(
                self,
                self.tr("New Game"),
                self.tr("You will lose the current game.\n" "Start a new game anyway?"),
            ):
                return

        self._start_new_game()

    def play_move_now(self) -> None:
        """Force engine to play move on current turn."""
        self._game.clear_arrow()
        self._board.update()

        self.stop_analysis()
        self.request_engine_move(force=True)

    def quit(self) -> None:
        """Quit app by closing main window."""
        self.close()

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

            board: Board = self._game.board_copy()

            black_time: float = self._black_clock.time
            black_increment: float = self._black_clock.increment
            white_time: float = self._white_clock.time
            white_increment: float = self._white_clock.increment

            self._engine.is_thinking = True
            self._notifications_label.setText(self.tr("Thinking..."))

            self._update_actions()

            QThreadPool.globalInstance().start(
                partial(
                    self._engine.play_move,
                    board=board,
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

    def start_analysis(self) -> None:
        """Start analyzing current position."""
        self._black_clock.stop_timer()
        self._white_clock.stop_timer()

        self._request_engine_analysis()
        self._update_actions()

    def stop_analysis(self) -> None:
        """Stop analyzing current position."""
        self._engine.stop_analysis()
        self._notifications_label.clear()
        self._engine_analysis_label.clear()
        self._evaluation_bar.reset_appearance()

        self.update_clock_timers()
        self._update_actions()

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

        self._update_actions()

    def update_clock_timers(self) -> None:
        """Start/stop clocks based on current turn."""
        if not self._game.is_in_progress():
            self._black_clock.stop_timer()
            self._white_clock.stop_timer()
            return

        if self._game.is_over_by_result() or self._game.is_viewing_history:
            return

        if self._game.is_white_to_move():
            self._black_clock.stop_timer()
            self._white_clock.start_timer()
        else:
            self._white_clock.stop_timer()
            self._black_clock.start_timer()

    @Slot(Score)
    def animate_evaluation(self, score: Score) -> None:
        """Show position evaluation based on `score`."""
        self._evaluation_bar.animate(score)

    @Slot(str)
    def apply_validated_fen(self, fen: str) -> None:
        """Apply position based on `fen`, prompt if game is in progress."""
        if self._game.is_in_progress():
            if not ask_question(
                self,
                self.tr("Apply FEN"),
                self.tr("You will lose the current game.\n" "Apply the FEN anyway?"),
            ):
                self._show_fen()
                return

        self._game.fen = fen

        self._black_clock.reset()
        self._white_clock.reset()
        self._openings_label.clear()

        self._update_ui_state()

    @Slot()
    def expire_clock_for_black(self) -> None:
        """End game when Black's clock expires."""
        self._black_clock.stop_timer()
        self._white_clock.stop_timer()

        self._board.disable_interaction()
        self._game.expire_clock_for(BLACK)
        self._sound_player.play_game_over()
        self._notifications_label.setText(self._game.result())

        self._update_actions()

    @Slot()
    def expire_clock_for_white(self) -> None:
        """End game when White's clock expires."""
        self._black_clock.stop_timer()
        self._white_clock.stop_timer()

        self._board.disable_interaction()
        self._game.expire_clock_for(WHITE)
        self._sound_player.play_game_over()
        self._notifications_label.setText(self._game.result())

        self._update_actions()

    @Slot(Move)
    def play_engine_move(self, move: Move) -> None:
        """Play engine's `move` or discard it when stale."""
        self._engine.is_thinking = False

        is_game_over_by_result: bool = self._game.is_over_by_result()

        if self._game.fen != self._engine_fen or is_game_over_by_result:
            if is_game_over_by_result:
                self._notifications_label.setText(self._game.result())
            else:
                self._notifications_label.clear()

            self._update_actions()
            self.request_engine_move()
            return

        self._play_move(move)

    @Slot(Move)
    def play_human_move(self, move: Move) -> None:
        """Play human's `move` with optional promotion."""
        if move.promotion is not None:
            promotion_dialog: PromotionDialog = PromotionDialog(self, self._game.turn)
            promotion_dialog.exec()

            move.promotion = promotion_dialog.piece_type

            if move.promotion is None:
                return

        self._play_move(move)

    @Slot(Move)
    def show_best_move_arrow(self, best_move: Move) -> None:
        """Show `best_move` as arrow marker on board."""
        self._game.set_arrow(best_move)
        self._board.update()

    @Slot(str)
    def show_engine_variation(self, variation: str) -> None:
        """Show formatted variation based on engine analysis."""
        formatted_variation: str = sub(r"(?=(\b\d+\.+))", "\n", variation).strip()
        self._engine_analysis_label.setText(formatted_variation)

    @Slot(int)
    def show_historical_move(self, move_index: int) -> None:
        """Show position from historical move at `move_index`."""
        is_last_move: bool = move_index == len(self._game.moves) - 1 or not self._game.moves
        is_returning_from_history: bool = is_last_move and self._game.is_viewing_history

        self._game.is_viewing_history = not is_last_move

        if move_index < 0:
            self._openings_label.clear()
            self._game.set_root_position()
        else:
            self._game.update_state(move_index)

        if not is_last_move:
            self._black_clock.stop_timer()
            self._white_clock.stop_timer()

        self._show_fen()
        self._show_opening()
        self.stop_analysis()

        if self._game.is_over_by_result():
            self._notifications_label.setText(self._game.result())

        self._board.update()

        if is_returning_from_history:
            self.request_engine_move()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Prompt whether to quit app."""
        if ask_question(self, self.tr("Quit"), self.tr("Are you sure you want to quit?")):
            self._terminate_engine()
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

    def _apply_increment(self) -> None:
        """Add increment to player's clock based on current turn."""
        if self._game.player_with_expired_clock is not None:
            return

        if self._game.is_white_to_move():
            self._black_clock.add_increment()
        else:
            self._white_clock.add_increment()

    def _apply_language(self) -> None:
        """Apply language from settings on app launch."""
        install_translators(self._settings.value("ui", "language"))

    def _apply_saved_settings(self) -> None:
        """Act on edited settings being saved."""
        if not self._game.is_in_progress():
            self._black_clock.reset()
            self._white_clock.reset()

            self._human_name_label.setText(
                self._settings.value("human", "name") or self.tr("Player")
            )

        self._orient_board_for_human()
        self.request_engine_move()

    def _connect_signals_to_slots(self) -> None:
        """Connect component signals to corresponding slot methods."""

        # Clocks
        self._black_clock.expired.connect(self.expire_clock_for_black)
        self._white_clock.expired.connect(self.expire_clock_for_white)

        # Engine
        self._engine.best_move_analyzed.connect(self.show_best_move_arrow)
        self._engine.move_played.connect(self.play_engine_move)
        self._engine.score_analyzed.connect(self.animate_evaluation)
        self._engine.variation_analyzed.connect(self.show_engine_variation)

        # Game
        self._game.move_played.connect(self.play_human_move)

        # Widgets
        self._fen_editor.fen_validated.connect(self.apply_validated_fen)
        self._table_view.move_selected.connect(self.show_historical_move)

    def _create_actions(self) -> None:
        """Create menu item and tool bar button actions."""
        self.about_action: QAction = create_action(
            icon=create_svg_icon("about"),
            name=self.tr("About StrikeChess"),
            handler=self.show_about,
            shortcut="F1",
            status_tip=self.tr("Shows the About dialog."),
        )
        self.dark_forest_theme_action: QAction = create_action(
            icon=create_colored_icon("#1f291f"),
            name=self.tr("Dark Forest"),
            handler=partial(self.apply_theme, ThemeName.DarkForest),
            shortcut="Alt+1",
            status_tip=self.tr("Applies the Dark Forest theme."),
        )
        self.dark_mint_theme_action: QAction = create_action(
            icon=create_colored_icon("#1a2e2e"),
            name=self.tr("Dark Mint"),
            handler=partial(self.apply_theme, ThemeName.DarkMint),
            shortcut="Alt+2",
            status_tip=self.tr("Applies the Dark Mint theme."),
        )
        self.dark_nebula_theme_action: QAction = create_action(
            icon=create_colored_icon("#351d4d"),
            name=self.tr("Dark Nebula"),
            handler=partial(self.apply_theme, ThemeName.DarkNebula),
            shortcut="Alt+3",
            status_tip=self.tr("Applies the Dark Nebula theme."),
        )
        self.dark_ocean_theme_action: QAction = create_action(
            icon=create_colored_icon("#2e455e"),
            name=self.tr("Dark Ocean"),
            handler=partial(self.apply_theme, ThemeName.DarkOcean),
            shortcut="Alt+4",
            status_tip=self.tr("Applies the Dark Ocean theme."),
        )
        self.english_language_action: QAction = create_action(
            icon=create_svg_icon("american-flag"),
            name="English",
            handler=partial(self.change_language, "en"),
            shortcut="",
            status_tip=self.tr("Applies the American English language."),
        )
        self.flip_action: QAction = create_action(
            icon=create_svg_icon("flip"),
            name=self.tr("Flip"),
            handler=self.flip,
            shortcut="Ctrl+F",
            status_tip=self.tr("Flips board orientation and board-related elements."),
        )
        self.german_language_action: QAction = create_action(
            icon=create_svg_icon("german-flag"),
            name="Deutsch",
            handler=partial(self.change_language, "de"),
            shortcut="",
            status_tip=self.tr("Applies the German language."),
        )
        self.italian_language_action: QAction = create_action(
            icon=create_svg_icon("italian-flag"),
            name="Italiano",
            handler=partial(self.change_language, "it"),
            shortcut="",
            status_tip=self.tr("Applies the Italian language."),
        )
        self.light_forest_theme_action: QAction = create_action(
            icon=create_colored_icon("#95a88c"),
            name=self.tr("Light Forest"),
            handler=partial(self.apply_theme, ThemeName.LightForest),
            shortcut="Alt+5",
            status_tip=self.tr("Applies the Light Forest theme."),
        )
        self.light_mint_theme_action: QAction = create_action(
            icon=create_colored_icon("#97cbc5"),
            name=self.tr("Light Mint"),
            handler=partial(self.apply_theme, ThemeName.LightMint),
            shortcut="Alt+6",
            status_tip=self.tr("Applies the Light Mint theme."),
        )
        self.light_nebula_theme_action: QAction = create_action(
            icon=create_colored_icon("#c385f7"),
            name=self.tr("Light Nebula"),
            handler=partial(self.apply_theme, ThemeName.LightNebula),
            shortcut="Alt+7",
            status_tip=self.tr("Applies the Light Nebula theme."),
        )
        self.light_ocean_theme_action: QAction = create_action(
            icon=create_colored_icon("#87a6c3"),
            name=self.tr("Light Ocean"),
            handler=partial(self.apply_theme, ThemeName.LightOcean),
            shortcut="Alt+8",
            status_tip=self.tr("Applies the Light Ocean theme."),
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
        self.spanish_language_action: QAction = create_action(
            icon=create_svg_icon("spanish-flag"),
            name="Español",
            handler=partial(self.change_language, "es"),
            shortcut="",
            status_tip=self.tr("Applies the Spanish language."),
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

    def _create_layout(self) -> None:
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

    def _create_menu_bar(self) -> None:
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

        theme_menu.addAction(self.dark_forest_theme_action)
        theme_menu.addAction(self.dark_mint_theme_action)
        theme_menu.addAction(self.dark_nebula_theme_action)
        theme_menu.addAction(self.dark_ocean_theme_action)
        theme_menu.addAction(self.light_forest_theme_action)
        theme_menu.addAction(self.light_mint_theme_action)
        theme_menu.addAction(self.light_nebula_theme_action)
        theme_menu.addAction(self.light_ocean_theme_action)

        language_menu.addAction(self.german_language_action)
        language_menu.addAction(self.english_language_action)
        language_menu.addAction(self.spanish_language_action)
        language_menu.addAction(self.italian_language_action)

        edit_menu.addAction(self.show_settings_dialog_action)

        help_menu.addAction(self.about_action)

    def _create_status_bar(self) -> None:
        """Create status bar to show opening name and theme name."""
        self.statusBar().addWidget(self._openings_label)
        self.statusBar().addPermanentWidget(self._theme_name_label)

    def _create_tool_bar(self) -> None:
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

    def _orient_board_elements(self) -> None:
        """Orient board-related elements based on board orientation."""
        is_white_at_bottom: bool = self._settings.value("ui", "is_white_at_bottom")

        self._board.set_orientation(is_white_at_bottom)
        self._evaluation_bar.invert_fill(is_white_at_bottom)

        self._position_clocks(is_white_at_bottom)
        self._position_player_names(is_white_at_bottom)

    def _orient_board_for_human(self) -> None:
        """Place human at bottom if playing against engine."""
        is_engine_white: bool = self._settings.value("engine", "is_white")
        self._settings.set_value("ui", "is_white_at_bottom", not is_engine_white)
        self._orient_board_elements()

    def _play_move(self, move: Move) -> None:
        """Play `move` and update UI state."""
        if not self._game.is_legal(move):
            return

        self._sound_player.play(move)

        self._game.push(move)
        self._apply_increment()

        self._engine.is_thinking = False

        self._update_ui_state()

    def _position_clocks(self, is_white_at_bottom: bool) -> None:
        """Position clock widgets based on `is_white_at_bottom`."""
        self._grid_layout.removeWidget(self._black_clock)
        self._grid_layout.removeWidget(self._white_clock)

        if is_white_at_bottom:
            self._grid_layout.addWidget(self._black_clock, 1, 1)
            self._grid_layout.addWidget(self._white_clock, 4, 1)
        else:
            self._grid_layout.addWidget(self._white_clock, 1, 1)
            self._grid_layout.addWidget(self._black_clock, 4, 1)

    def _position_player_names(self, is_white_at_bottom: bool) -> None:
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

    def _request_engine_analysis(self) -> None:
        """Request engine to analyze current position."""
        self._engine.is_analyzing = True
        self._notifications_label.setText(self.tr("Analyzing..."))

        board: Board = self._game.board_copy()
        QThreadPool.globalInstance().start(partial(self._engine.start_analysis, board))

    def _show_fen(self) -> None:
        """Show FEN in editor."""
        self._fen_editor.hide_warning()
        self._fen_editor.setText(self._game.fen)
        self._fen_editor.clearFocus()

    def _show_opening(self) -> None:
        """Show name of current opening."""
        opening_data: str | None = find_opening(self._game.fen) or find_opening(
            self._game.root_fen
        )

        if opening_data is not None:
            self._openings_label.setText(opening_data)

    def _start_new_game(self) -> None:
        """Reset game and UI states to start new game."""
        self._game.is_viewing_history = False

        self._game.reset()
        self._table_model.reset()

        self._black_clock.reset()
        self._white_clock.reset()

        self._openings_label.clear()
        self._board.enable_interaction()

        self._show_fen()
        self.stop_analysis()

        self._orient_board_for_human()
        self.request_engine_move()

    def _terminate_engine(self) -> None:
        """Terminate engine process."""
        self._engine.terminate()

    def _update_actions(self) -> None:
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
            or is_game_over_by_result
            or is_game_over_by_rules
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

    def _update_ui_state(self) -> None:
        """Update UI to reflect current game state."""
        self._game.is_viewing_history = False

        self._board.enable_interaction()
        self._board.update()

        self._table_model.update_view()
        self._table_view.select_last_move()

        self._show_fen()
        self._show_opening()
        self.stop_analysis()

        if self._game.is_over_by_result():
            self._black_clock.stop_timer()
            self._white_clock.stop_timer()
            self._board.disable_interaction()
            self._notifications_label.setText(self._game.result())
            return

        self.request_engine_move()
