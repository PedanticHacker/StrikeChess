from __future__ import annotations

from typing import ClassVar

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
    """View for move history in SAN format."""

    item_selected: ClassVar[Signal] = Signal(int)

    def __init__(self, table_model: QAbstractTableModel) -> None:
        super().__init__()

        self.setModel(table_model)

        self.setShowGrid(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.model().layoutChanged.connect(self.scrollToBottom)
        self.selectionModel().currentChanged.connect(self.on_current_changed)

    @property
    def item_index(self) -> int:
        """Get index of selected move."""
        current_model_index: QModelIndex = self.selectionModel().currentIndex()
        return 2 * current_model_index.row() + current_model_index.column()

    @property
    def previous_model_index(self) -> QModelIndex:
        """Get model index of previous move."""
        previous_row: int = (self.item_index - 1) // 2
        previous_column: int = (self.item_index - 1) % 2
        return self.model().index(previous_row, previous_column)

    @property
    def next_model_index(self) -> QModelIndex:
        """Get model index of next move."""
        all_rows: int = self.model().rowCount()
        next_row: int = (self.item_index + 1) // 2
        next_column: int = (self.item_index + 1) % 2
        next_index: QModelIndex = self.model().index(next_row, next_column)

        if next_row < all_rows and next_index.data():
            return next_index
        return QModelIndex()

    def select_last_item(self) -> None:
        """Select most recently played move."""
        last_row: int = self.model().rowCount() - 1
        last_column: int = 1 if self.model().index(last_row, 1).data() else 0
        last_model_index: QModelIndex = self.model().index(last_row, last_column)
        self.select_model_index(last_model_index)

    def select_previous_item(self) -> None:
        """Select previous move in history."""
        if self.item_index == 0 and self.model().index(0, 0).data() == "...":
            return
        self.select_model_index(self.previous_model_index)

    def select_next_item(self) -> None:
        """Select next move in history."""
        if self.item_index < 0:
            next_model_index: QModelIndex = self.model().index(0, 0)
        else:
            next_model_index = self.next_model_index

        if next_model_index.isValid():
            self.select_model_index(next_model_index)

    def select_model_index(self, model_index: QModelIndex) -> None:
        """Select move based on `model_index`."""
        self.selectionModel().setCurrentIndex(
            model_index,
            QItemSelectionModel.SelectionFlag.ClearAndSelect,
        )

    def focusInEvent(self, event: QFocusEvent) -> None:
        """Ignore focus-in event to prevent automatic item selection."""
        event.ignore()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Select move using left/right arrow keys."""
        if event.key() == Qt.Key.Key_Left:
            self.select_previous_item()
        elif event.key() == Qt.Key.Key_Right:
            self.select_next_item()

    @Slot()
    def on_current_changed(self) -> None:
        """Emit item index of selected move."""
        self.item_selected.emit(self.item_index)
