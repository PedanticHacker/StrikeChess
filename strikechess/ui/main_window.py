from enum import StrEnum
from functools import partial
from pathlib import Path
from re import sub
from typing import Final, Literal

from chess import BLACK, WHITE, Move
from chess.engine import Score
from PySide6.QtCore import Qt, QThreadPool, QTimer, Slot
from PySide6.QtGui import QCloseEvent, QWheelEvent
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QGridLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QWidget,
)

from strikechess.core import Engine, Game
from strikechess.ui.audio import SoundEffect
from strikechess.ui.dialogs import SettingsDialog
from strikechess.ui.table import TableModel, TableView
from strikechess.ui.widgets import DigitalClock, EvaluationBar, FenEditor, SvgBoard
from strikechess.utils import (
    colorize_icon,
    create_action,
    engine_file_filter,
    find_opening,
    set_setting_value,
    setting_value,
    show_info,
    style_name,
    svg_icon,
)


class ClockColor(StrEnum):
    """CSS color style enum for clocks of Black and White players."""

    Black = "color: white; background-color: black;"
    White = "color: black; background-color: white;"


class MainWindow(QMainWindow):
    """Container and layout manager for all widgets."""

    def __init__(self) -> None:
        super().__init__()

        self._game: Game = Game()
        self._engine: Engine = Engine(self._game)

        self._table_model: TableModel = TableModel(self._game.moves)
        self._table_view: TableView = TableView(self._table_model)

        self._black_clock: DigitalClock = DigitalClock(ClockColor.Black)
        self._white_clock: DigitalClock = DigitalClock(ClockColor.White)

        self._board: SvgBoard = SvgBoard(self._game)
        self._fen_editor: FenEditor = FenEditor(self._game)
        self._sound_effect: SoundEffect = SoundEffect(self._game)
        self._evaluation_bar: EvaluationBar = EvaluationBar()

        self._engine_analysis_label: QLabel = QLabel()
        self._engine_analysis_label.setObjectName("engineAnalysis")
        self._engine_analysis_label.hide()

        self._engine_name_label: QLabel = QLabel()
        self._engine_name_label.setObjectName("engineName")
        self._engine_name_label.setText(self._engine.name)
        self._engine_name_label.setToolTip(self._engine_name_label.text())

        self._game_notifications_label: QLabel = QLabel()
        self._game_notifications_label.setObjectName("gameNotifications")

        self._human_name_label: QLabel = QLabel()
        self._human_name_label.setObjectName("humanName")
        self._human_name_label.setText(setting_value("human", "name"))

        self._openings_label: QLabel = QLabel()
        self._style_name_label: QLabel = QLabel()

        self._scroll_timer: QTimer = QTimer(self)
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.setInterval(180)

        self.create_layout()
        self.create_actions()
        self.create_menubar()
        self.create_toolbar()
        self.create_statusbar()
        self.apply_widget_sizes()
        self.retain_layout_size()
        self.switch_clock_timers()
        self.adjust_toolbar_buttons()
        self.connect_signals_to_slots()
        self.apply_style(setting_value("ui", "style"))

        self.align_orientation_to_engine()
        self.invoke_engine()

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
        self._grid_layout.addWidget(self._game_notifications_label, 5, 3)

        self._grid_layout.setRowStretch(0, 1)
        self._grid_layout.setRowStretch(3, 1)
        self._grid_layout.setRowStretch(6, 1)

        self._grid_layout.setColumnStretch(0, 1)
        self._grid_layout.setColumnStretch(6, 1)

        central_widget: QWidget = QWidget()
        central_widget.setLayout(self._grid_layout)
        self.setCentralWidget(central_widget)

    def create_actions(self) -> None:
        """Create menu and toolbar actions."""
        self.about_action = create_action(
            handler=self.show_about,
            icon=svg_icon("about"),
            name="About StrikeChess",
            shortcut="F1",
            status_tip="Shows the About dialog.",
        )
        self.dark_forest_style_action = create_action(
            handler=partial(self.apply_style, "dark-forest"),
            icon=colorize_icon("#2d382d"),
            name="Dark forest",
            shortcut="Alt+1",
            status_tip="Applies the dark forest style.",
        )
        self.dark_mint_style_action = create_action(
            handler=partial(self.apply_style, "dark-mint"),
            icon=colorize_icon("#1a2e2e"),
            name="Dark mint",
            shortcut="Alt+2",
            status_tip="Applies the dark mint style.",
        )
        self.dark_nebula_style_action = create_action(
            handler=partial(self.apply_style, "dark-nebula"),
            icon=colorize_icon("#1a1025"),
            name="Dark nebula",
            shortcut="Alt+3",
            status_tip="Applies the dark nebula style.",
        )
        self.dark_ocean_style_action = create_action(
            handler=partial(self.apply_style, "dark-ocean"),
            icon=colorize_icon("#1a2838"),
            name="Dark ocean",
            shortcut="Alt+4",
            status_tip="Applies the dark ocean style.",
        )
        self.flip_action = create_action(
            handler=self.flip,
            icon=svg_icon("flip"),
            name="Flip",
            shortcut="Ctrl+F",
            status_tip="Flips the orientation of board and its related widgets.",
        )
        self.light_forest_style_action = create_action(
            handler=partial(self.apply_style, "light-forest"),
            icon=colorize_icon("#e8efe6"),
            name="Light forest",
            shortcut="Alt+5",
            status_tip="Applies the light forest style.",
        )
        self.light_mint_style_action = create_action(
            handler=partial(self.apply_style, "light-mint"),
            icon=colorize_icon("#ebf5f3"),
            name="Light mint",
            shortcut="Alt+6",
            status_tip="Applies the light mint style.",
        )
        self.light_nebula_style_action = create_action(
            handler=partial(self.apply_style, "light-nebula"),
            icon=colorize_icon("#f4ebff"),
            name="Light nebula",
            shortcut="Alt+7",
            status_tip="Applies the light nebula style.",
        )
        self.light_ocean_style_action = create_action(
            handler=partial(self.apply_style, "light-ocean"),
            icon=colorize_icon("#ebf3f8"),
            name="Light ocean",
            shortcut="Alt+8",
            status_tip="Applies the light ocean style.",
        )
        self.load_engine_action = create_action(
            handler=self.load_engine,
            icon=svg_icon("load-engine"),
            name="Load engine...",
            shortcut="Ctrl+L",
            status_tip="Shows the file manager to load an engine.",
        )
        self.new_game_action = create_action(
            handler=self.offer_new_game,
            icon=svg_icon("new-game"),
            name="New game",
            shortcut="Ctrl+N",
            status_tip="Shows a dialog offering to start a new game.",
        )
        self.play_move_now_action = create_action(
            handler=self.play_move_now,
            icon=svg_icon("play-move-now"),
            name="Play move now",
            shortcut="Ctrl+P",
            status_tip="Forces the engine to play on current turn.",
        )
        self.quit_action = create_action(
            handler=self.quit,
            icon=svg_icon("quit"),
            name="Quit...",
            shortcut="Ctrl+Q",
            status_tip="Offers to quit the app.",
        )
        self.settings_action = create_action(
            handler=self.show_settings_dialog,
            icon=svg_icon("settings"),
            name="Settings...",
            shortcut="Ctrl+,",
            status_tip="Shows a dialog to edit the settings.",
        )
        self.start_analysis_action = create_action(
            handler=self.start_analysis,
            icon=svg_icon("start-analysis"),
            name="Start analysis",
            shortcut="F3",
            status_tip="Starts analyzing the current position.",
        )
        self.stop_analysis_action = create_action(
            handler=self.stop_analysis,
            icon=svg_icon("stop-analysis"),
            name="Stop analysis",
            shortcut="F4",
            status_tip="Stops analyzing the current position.",
        )

    def create_menubar(self) -> None:
        """Create menubar with actions in separate menus."""

        # Menubar
        menubar = self.menuBar()

        # General menu
        general_menu = menubar.addMenu("General")

        # Style menu
        style_menu = menubar.addMenu("Style")

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        # Help menu
        help_menu = menubar.addMenu("Help")

        # General menu > Load engine...
        general_menu.addAction(self.load_engine_action)

        # General menu separator
        general_menu.addSeparator()

        # General menu > Quit...
        general_menu.addAction(self.quit_action)

        # Style menu > Dark forest
        style_menu.addAction(self.dark_forest_style_action)

        # Style menu > Dark mint
        style_menu.addAction(self.dark_mint_style_action)

        # Style menu > Dark nebula
        style_menu.addAction(self.dark_nebula_style_action)

        # Style menu > Dark ocean
        style_menu.addAction(self.dark_ocean_style_action)

        # Style menu > Light forest
        style_menu.addAction(self.light_forest_style_action)

        # Style menu > Light mint
        style_menu.addAction(self.light_mint_style_action)

        # Style menu > Light nebula
        style_menu.addAction(self.light_nebula_style_action)

        # Style menu > Light ocean
        style_menu.addAction(self.light_ocean_style_action)

        # Edit menu > Settings...
        edit_menu.addAction(self.settings_action)

        # Help menu > About
        help_menu.addAction(self.about_action)

    def create_toolbar(self) -> None:
        """Create toolbar with buttons in separate areas."""

        # General area
        general_area = self.addToolBar("General")

        # Edit area
        edit_area = self.addToolBar("Edit")

        # Help area
        help_area = self.addToolBar("Help")

        # General area > Quit
        general_area.addAction(self.quit_action)

        # Edit area > New game
        edit_area.addAction(self.new_game_action)

        # Edit area > Flip orientation
        edit_area.addAction(self.flip_action)

        # Edit area > Play move now
        edit_area.addAction(self.play_move_now_action)

        # Edit area > Start analysis
        edit_area.addAction(self.start_analysis_action)

        # Edit area > Stop analysis
        edit_area.addAction(self.stop_analysis_action)

        # Edit area > Settings
        edit_area.addAction(self.settings_action)

        # Edit area > Load engine
        edit_area.addAction(self.load_engine_action)

        # Help area > About
        help_area.addAction(self.about_action)

    def create_statusbar(self) -> None:
        """Create statusbar to show openings, style name, and tips."""
        self.statusBar().addWidget(self._openings_label)
        self.statusBar().addPermanentWidget(self._style_name_label)

    def update_font_size(self) -> None:
        """Update font size based on current board size."""
        board_size: Literal["small", "normal", "big"] = setting_value("board", "size")
        font_size_options: dict[str, int] = {"small": 12, "normal": 14, "big": 16}
        self.centralWidget().setStyleSheet(
            f"font-size: {font_size_options[board_size]}px;"
        )

    def apply_widget_sizes(self) -> None:
        """Apply size of board and its related widgets."""
        self.update_font_size()
        self._board.update_board_size()

        board_size: int = self._board.board_size
        third_board_size: int = board_size // 3
        ninth_board_size: int = board_size // 9

        self._human_name_label.setFixedWidth(third_board_size)
        self._engine_name_label.setFixedWidth(third_board_size)
        self._table_view.setFixedSize(third_board_size, board_size)
        self._evaluation_bar.setFixedSize(ninth_board_size, board_size)
        self._black_clock.setFixedSize(third_board_size, ninth_board_size)
        self._white_clock.setFixedSize(third_board_size, ninth_board_size)
        self._engine_analysis_label.setFixedSize(third_board_size, board_size)

    def retain_layout_size(self) -> None:
        """Retain layout size for hidden widgets."""
        size_policy: QSizePolicy = self.sizePolicy()
        size_policy.setRetainSizeWhenHidden(True)
        self._engine_analysis_label.setSizePolicy(size_policy)
        self._evaluation_bar.setSizePolicy(size_policy)

    def switch_clock_timers(self) -> None:
        """Switch between Black and White clock timers based on turn."""
        if self._game.is_over():
            return

        if self._game.is_white_on_turn():
            self._black_clock.stop_timer()
            self._white_clock.start_timer()
            if self._game.is_in_progress():
                self._black_clock.add_increment()
        else:
            self._white_clock.stop_timer()
            self._black_clock.start_timer()
            if self._game.is_in_progress():
                self._white_clock.add_increment()

    def adjust_toolbar_buttons(self) -> None:
        """Adjust state of engine-related toolbar buttons."""
        self.play_move_now_action.setEnabled(True)
        self.start_analysis_action.setEnabled(True)
        self.stop_analysis_action.setDisabled(True)

        if self._game.is_over():
            self.play_move_now_action.setDisabled(True)

    def connect_signals_to_slots(self) -> None:
        """Connect component signals to corresponding slot methods."""
        self._black_clock.time_expired.connect(self.on_black_time_expired)
        self._engine.best_move_analyzed.connect(self.on_best_move_analyzed)
        self._engine.load_failed.connect(self.on_load_failed)
        self._engine.move_played.connect(self.on_move_played)
        self._engine.score_analyzed.connect(self.on_score_analyzed)
        self._engine.variation_analyzed.connect(self.on_variation_analyzed)
        self._fen_editor.fen_validated.connect(self.on_fen_validated)
        self._game.move_played.connect(self.on_move_played)
        self._game.sound_effect_played.connect(self.on_sound_effect_played)
        self._table_view.item_selected.connect(self.on_item_selected)
        self._white_clock.time_expired.connect(self.on_white_time_expired)

    def apply_style(self, file_name: str) -> None:
        """Apply QSS style at `file_name` and show its name."""
        with open(f"strikechess/assets/styles/{file_name}.qss") as qss_file:
            self.setStyleSheet(qss_file.read())
        set_setting_value("ui", "style", file_name)
        self._style_name_label.setText(f"Style: {style_name(file_name)}")

    def should_invoke_engine(self) -> bool:
        """Return True if engine has all requirements to be invoked."""
        if self._game.is_engine_on_turn() and not self._game.is_over():
            return True
        return False

    def invoke_engine(self, by_force: bool = False) -> None:
        """Invoke engine when on turn or when `by_force` is True."""
        if self.should_invoke_engine() or by_force:
            QThreadPool.globalInstance().start(self._engine.play_move)
            self._game_notifications_label.setText("Thinking...")

    def invoke_analysis(self) -> None:
        """Invoke engine to start analysis."""
        QThreadPool.globalInstance().start(self._engine.start_analysis)
        self._game_notifications_label.setText("Analyzing...")

    def quit(self) -> None:
        """Trigger close event of main window."""
        self.close()

    def flip(self) -> None:
        """Flip current orientation from settings and update it."""
        required_orientation: bool = not setting_value("board", "orientation")
        set_setting_value("board", "orientation", required_orientation)
        self.update_orientation()

    def align_orientation_to_engine(self) -> None:
        """Align board orientation to color of engine pieces."""
        required_orientation: bool = not setting_value("engine", "is_white")
        set_setting_value("board", "orientation", required_orientation)
        self.update_orientation()

    def update_orientation(self) -> None:
        """Align board orientation with board-related widgets."""
        current_orientation: bool = setting_value("board", "orientation")

        self._board.update_orientation(current_orientation)
        self._evaluation_bar.update_chunk_appearance(current_orientation)

        self.flip_clocks(current_orientation)
        self.flip_player_names(current_orientation)

    def play_move_now(self) -> None:
        """Force engine to play move on current turn."""
        self._game.clear_arrow()

        self.stop_analysis()
        self.invoke_engine(by_force=True)

    def show_settings_dialog(self) -> None:
        """Show dialog to edit settings."""
        settings_dialog: SettingsDialog = SettingsDialog()

        if self._game.is_in_progress():
            settings_dialog.disable_setting_groups()

        if settings_dialog.exec() == QDialog.DialogCode.Accepted:
            self.apply_saved_settings()

    def apply_saved_settings(self) -> None:
        """Act on edited settings being saved."""
        if not self._game.is_in_progress():
            self._black_clock.reset()
            self._white_clock.reset()
            self._human_name_label.setText(setting_value("human", "name"))

        self.apply_widget_sizes()
        self.align_orientation_to_engine()
        self.invoke_engine()

    def load_engine(self) -> None:
        """Show file manager to load engine."""
        path_to_file, _ = QFileDialog.getOpenFileName(
            self,
            "File Manager",
            Path.home().as_posix(),
            engine_file_filter(),
        )

        if path_to_file:
            self.start_new_engine(path_to_file)

    def start_new_engine(self, path_to_file: str) -> None:
        """Start new engine from file at `path_to_file`."""
        self.stop_analysis()

        self._engine.load_from_file_at(path_to_file)
        self._engine_name_label.setText(self._engine.name)
        self._engine_name_label.setToolTip(self._engine.name)

        self.invoke_engine()

    def show_about(self) -> None:
        """Show About dialog."""
        QMessageBox.about(
            self,
            "About",
            (
                "This is an app for playing chess.\n\n"
                "Copyright (C) 2025 Boštjan Mejak\n"
                "MIT License"
            ),
        )

    def flip_clocks(self, orientation: bool) -> None:
        """Flip clocks based on `orientation`."""
        self._grid_layout.removeWidget(self._black_clock)
        self._grid_layout.removeWidget(self._white_clock)

        if orientation:
            self._grid_layout.addWidget(self._black_clock, 1, 1)
            self._grid_layout.addWidget(self._white_clock, 4, 1)
        else:
            self._grid_layout.addWidget(self._white_clock, 1, 1)
            self._grid_layout.addWidget(self._black_clock, 4, 1)

    def flip_player_names(self, orientation: bool) -> None:
        """Flip player names based on `orientation`."""
        self._grid_layout.removeWidget(self._engine_name_label)
        self._grid_layout.removeWidget(self._human_name_label)

        if orientation == setting_value("engine", "is_white"):
            self._grid_layout.addWidget(self._human_name_label, 2, 1)
            self._grid_layout.addWidget(self._engine_name_label, 5, 1)
        else:
            self._grid_layout.addWidget(self._engine_name_label, 2, 1)
            self._grid_layout.addWidget(self._human_name_label, 5, 1)

    def show_analysis_ui(self) -> None:
        """Show evaluation bar and engine analysis label."""
        self._evaluation_bar.show()
        self._engine_analysis_label.show()

    def hide_analysis_ui(self) -> None:
        """Hide engine analysis label and evaluation bar."""
        self._engine_analysis_label.hide()
        self._evaluation_bar.hide()

    def start_analysis(self) -> None:
        """Start analyzing current position."""
        self.invoke_analysis()
        self.show_analysis_ui()

        self._black_clock.stop_timer()
        self._white_clock.stop_timer()

        self.start_analysis_action.setDisabled(True)
        self.stop_analysis_action.setEnabled(True)

    def stop_analysis(self) -> None:
        """Stop analyzing current position."""
        self._engine.stop_analysis()

        self._game_notifications_label.clear()

        self.adjust_toolbar_buttons()
        self.switch_clock_timers()
        self.hide_analysis_ui()

    def show_fen(self) -> None:
        """Show FEN in editor."""
        self._fen_editor.clearFocus()
        self._fen_editor.hide_warning()
        self._fen_editor.setText(self._game.fen)

    def show_opening(self) -> None:
        """Show ECO code and opening name."""
        openings_data: list[str] | None = find_opening(self._game.fen)

        if openings_data is not None:
            eco_code, opening_name = openings_data
            self._openings_label.setText(f"{eco_code}: {opening_name}")

    def refresh_ui(self) -> None:
        """Refresh current state of UI."""
        self._game.is_history = False

        self._table_model.refresh_view()
        self._table_view.select_last_item()

        self.show_fen()
        self.show_opening()
        self.stop_analysis()
        self.invoke_engine()

        if self._game.is_over():
            self._black_clock.stop_timer()
            self._white_clock.stop_timer()
            self._game_notifications_label.setText(self._game.result)

    def offer_new_game(self) -> None:
        """Show dialog offering to start new game."""
        answer: QMessageBox.StandardButton = QMessageBox.question(
            self,
            "New game",
            "Do you want to start a new game?",
        )

        if answer == answer.Yes:
            self.start_new_game()

    def start_new_game(self) -> None:
        """Start new game by resetting and clearing everything."""
        self._game.is_history = False

        self._black_clock.reset()
        self._white_clock.reset()

        self._table_model.reset()
        self._openings_label.clear()
        self._game.prepare_new_game()
        self._board.enable_interaction()

        self.show_fen()
        self.stop_analysis()
        self.align_orientation_to_engine()
        self.invoke_engine()

    def destruct(self) -> None:
        """Terminate engine process and destroy main window."""
        self._engine.quit()
        self.destroy()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Ask whether to quit StrikeChess by closing its main window."""
        answer: QMessageBox.StandardButton = QMessageBox.question(
            self,
            "Quit",
            "Do you really want to quit StrikeChess?",
        )

        if answer == QMessageBox.StandardButton.Yes:
            self._engine.quit()
            event.accept()
        else:
            event.ignore()

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle wheel scroll events with timer-based throttling."""
        if not self._scroll_timer.isActive():
            scroll_step: int = event.angleDelta().y()

            if scroll_step > 0:
                self._table_view.select_previous_item()
            elif scroll_step < 0:
                self._table_view.select_next_item()

            self._scroll_timer.start()

    @Slot(Move)
    def on_best_move_analyzed(self, best_move: Move) -> None:
        """Show `best_move` as arrow on board."""
        self._game.set_arrow(best_move)

    @Slot()
    def on_black_time_expired(self) -> None:
        """Handle game termination when Black's time expires."""
        self._black_clock.stop_timer()
        self._white_clock.stop_timer()

        self._sound_effect.play_time_expired()

        self._game.declare_time_loss_for(BLACK)
        self._game_notifications_label.setText(self._game.result)

        self._board.disable_interaction()
        self._board.update()

        self.adjust_toolbar_buttons()

    @Slot()
    def on_white_time_expired(self) -> None:
        """Handle game termination when White's time expires."""
        self._black_clock.stop_timer()
        self._white_clock.stop_timer()

        self._sound_effect.play_time_expired()

        self._game.declare_time_loss_for(WHITE)
        self._game_notifications_label.setText(self._game.result)

        self._board.disable_interaction()
        self._board.update()

        self.adjust_toolbar_buttons()

    @Slot()
    def on_fen_validated(self) -> None:
        """Refresh UI after FEN has been validated."""
        self.refresh_ui()

    @Slot(int)
    def on_item_selected(self, item_index: int) -> None:
        """Show move based on `item_index`."""
        self._game.is_history = True

        if item_index < 0:
            self._openings_label.clear()
            self._game.set_root_position()
        else:
            self._game.update_state(item_index)

        self._black_clock.stop_timer()
        self._white_clock.stop_timer()
        self._game.reset_selected_squares()

        self.show_fen()
        self.show_opening()
        self.stop_analysis()

        if self._game.is_over():
            self._game_notifications_label.setText(self._game.result)

    @Slot(str)
    def on_load_failed(self, engine_message: str) -> None:
        """Show `engine_message` after engine load attempt failed."""
        show_info(self, engine_message)

    @Slot(Move)
    def on_move_played(self, move: Move) -> None:
        """Play `move` and refresh UI."""
        self._game.push(move)
        self.refresh_ui()

    @Slot(Move)
    def on_sound_effect_played(self, move: Move) -> None:
        """Play sound effect for received `move`."""
        self._sound_effect.play(move)

    @Slot(str)
    def on_variation_analyzed(self, variation: str) -> None:
        """Show formatted `variation` based on engine analysis."""
        formatted_variation: str = sub(r"(?=(\b\d+\.+))", "\n", variation).strip()
        self._engine_analysis_label.setText(formatted_variation)

    @Slot(Score)
    def on_score_analyzed(self, score: Score) -> None:
        """Show position evaluation based on `score`."""
        self._evaluation_bar.animate(score)
