class BoardOrientation:
    """Orientation of board and board-related elements."""

    def __init__(
        self,
        grid_layout: QGridLayout,
        board: SvgBoard,
        chess_clock: ChessClock,
        evaluation_bar: EvaluationBar,
        human_name_label: QLabel,
        engine_name_label: QLabel,
        settings: SettingsService,
    ) -> None:
        self._board: SvgBoard = board
        self._settings: SettingsService = settings
        self._chess_clock: ChessClock = chess_clock
        self._grid_layout: QGridLayout = grid_layout
        self._human_name_label: QLabel = human_name_label
        self._engine_name_label: QLabel = engine_name_label
        self._evaluation_bar: EvaluationBar = evaluation_bar

    def flip(self) -> None:
        """Flip board orientation and board-related elements."""
        is_white_at_bottom: bool = not self._settings.value("ui", "is_white_at_bottom")
        self._settings.set_value("ui", "is_white_at_bottom", is_white_at_bottom)
        self._orient_board_elements()

    def orient_board_for_human(self) -> None:
        """Place human at bottom if playing against engine."""
        is_engine_white: bool = self._settings.value("engine", "is_white")
        self._settings.set_value("ui", "is_white_at_bottom", not is_engine_white)
        self._orient_board_elements()

    def _orient_board_elements(self) -> None:
        """Orient board-related elements based on board orientation."""
        is_white_at_bottom: bool = self._settings.value("ui", "is_white_at_bottom")

        self._board.set_orientation(is_white_at_bottom)
        self._evaluation_bar.invert_fill(is_white_at_bottom)

        self._place_clocks(is_white_at_bottom)
        self._place_player_names(is_white_at_bottom)

    def _place_clocks(self, is_white_at_bottom: bool) -> None:
        """Place clock widgets based on `is_white_at_bottom`."""
        self._grid_layout.removeWidget(self._chess_clock.black)
        self._grid_layout.removeWidget(self._chess_clock.white)

        if is_white_at_bottom:
            self._grid_layout.addWidget(self._chess_clock.black, 1, 1)
            self._grid_layout.addWidget(self._chess_clock.white, 4, 1)
        else:
            self._grid_layout.addWidget(self._chess_clock.black, 4, 1)
            self._grid_layout.addWidget(self._chess_clock.white, 1, 1)

    def _place_player_names(self, is_white_at_bottom: bool) -> None:
        """Place player name labels based on `is_white_at_bottom`."""
        self._grid_layout.removeWidget(self._human_name_label)
        self._grid_layout.removeWidget(self._engine_name_label)

        is_engine_white: bool = self._settings.value("engine", "is_white")

        if is_white_at_bottom == is_engine_white:
            self._grid_layout.addWidget(self._human_name_label, 2, 1)
            self._grid_layout.addWidget(self._engine_name_label, 5, 1)
        else:
            self._grid_layout.addWidget(self._human_name_label, 5, 1)
            self._grid_layout.addWidget(self._engine_name_label, 2, 1)
