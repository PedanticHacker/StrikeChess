class BoardOrientation:
    """Orientation of board and board-related elements."""

    def __init__(
        self,
        grid_layout: QGridLayout,
        board: SvgBoard,
        black_clock: ChessClock,
        white_clock: ChessClock,
        evaluation_bar: EvaluationBar,
        human_name_label: QLabel,
        engine_name_label: QLabel,
        settings: SettingsService,
    ) -> None:
        self._board: SvgBoard = board
        self._settings: SettingsService = settings
        self._black_clock: ChessClock = black_clock
        self._white_clock: ChessClock = white_clock
        self._grid_layout: QGridLayout = grid_layout
        self._human_name_label: QLabel = human_name_label
        self._engine_name_label: QLabel = engine_name_label
        self._evaluation_bar: EvaluationBar = evaluation_bar

    def flip(self) -> None:
        """Flip board orientation and board-related elements."""
        self._orient_board_elements(not self._board.is_white_at_bottom)

    def orient_board_for_human(self) -> None:
        """Place human at bottom if playing against engine."""
        self._orient_board_elements(not self._settings.value("engine", "is_white"))

    def _orient_board_elements(self, is_white_at_bottom: bool) -> None:
        """Orient board elements based on `is_white_at_bottom`."""
        self._board.set_orientation(is_white_at_bottom)
        self._evaluation_bar.invert_fill(is_white_at_bottom)

        self._place_clocks(is_white_at_bottom)
        self._place_player_names(is_white_at_bottom)

    def _place_clocks(self, is_white_at_bottom: bool) -> None:
        """Place clock widgets based on `is_white_at_bottom`."""
        self._grid_layout.removeWidget(self._black_clock)
        self._grid_layout.removeWidget(self._white_clock)

        if is_white_at_bottom:
            self._grid_layout.addWidget(self._black_clock, 1, 1)
            self._grid_layout.addWidget(self._white_clock, 4, 1)
        else:
            self._grid_layout.addWidget(self._black_clock, 4, 1)
            self._grid_layout.addWidget(self._white_clock, 1, 1)

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
