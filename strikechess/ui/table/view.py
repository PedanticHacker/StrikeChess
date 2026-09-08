from PySide6.QtCore import (
    QAbstractTableModel,
    QItemSelectionModel,
    QModelIndex,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableView


class TableView(QTableView):
    """View showing moves in standard algebraic notation (SAN)."""

    move_selected: ClassVar[Signal] = Signal(int)

    def __init__(self, table_model: QAbstractTableModel) -> None:
        super().__init__()

        self.setModel(table_model)

        self.setFixedWidth(200)
        self.setShowGrid(False)

        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.model().layoutChanged.connect(self.scrollToBottom)
        self.selectionModel().currentChanged.connect(self.send_selected_move)

    @property
    def current_move(self) -> int:
        """Currently selected move."""
        current_model_index: QModelIndex = self.selectionModel().currentIndex()
        return 2 * current_model_index.row() + current_model_index.column()

    @property
    def previous_model_index(self) -> QModelIndex:
        """Model index of previous move."""
        previous_row: int = (self.current_move - 1) // 2
        previous_column: int = (self.current_move - 1) % 2
        return self.model().index(previous_row, previous_column)

    @property
    def next_model_index(self) -> QModelIndex:
        """Model index of next move."""
        all_rows: int = self.model().rowCount()
        next_row: int = (self.current_move + 1) // 2
        next_column: int = (self.current_move + 1) % 2
        next_move: QModelIndex = self.model().index(next_row, next_column)

        if next_row < all_rows and next_move.data() is not None:
            return next_move
        return QModelIndex()

    def select_last_move(self) -> None:
        """Select move that exists as last."""
        last_row: int = self.model().rowCount() - 1
        last_column: int = 1 if self.model().index(last_row, 1).data() is not None else 0
        last_model_index: QModelIndex = self.model().index(last_row, last_column)
        self._select_model_index(last_model_index)

    def select_previous_move(self) -> None:
        """Select move that exists before current move."""
        if self.current_move == 0 and self.model().index(0, 0).data() == "...":
            return
        self._select_model_index(self.previous_model_index)

    def select_next_move(self) -> None:
        """Select move that exists after current move."""
        if self.current_move < 0:
            next_model_index: QModelIndex = self.model().index(0, 0)
        else:
            next_model_index = self.next_model_index

        if next_model_index.isValid():
            self._select_model_index(next_model_index)

    def is_last_move(self) -> bool:
        """Return True if currently selected move is last."""
        return self.current_move >= 0 and not self.next_model_index.isValid()

    def focusInEvent(self, event: QFocusEvent) -> None:
        """Ignore focus-in event to prevent automatic move selection."""
        event.ignore()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Select move using left/right arrow keys."""
        if event.key() == Qt.Key.Key_Left:
            self.select_previous_move()
        elif event.key() == Qt.Key.Key_Right:
            self.select_next_move()
        else:
            super().keyPressEvent(event)

    @Slot()
    def send_selected_move(self) -> None:
        """Send currently selected move when move selection changes."""
        self.move_selected.emit(self.current_move)

    def _select_model_index(self, model_index: QModelIndex) -> None:
        """Select move based on `model_index`."""
        self.selectionModel().setCurrentIndex(
            model_index,
            QItemSelectionModel.SelectionFlag.ClearAndSelect,
        )
