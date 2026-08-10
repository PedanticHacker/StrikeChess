from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class TableModel(QAbstractTableModel):
    """Model providing moves in standard algebraic notation (SAN)."""

    def __init__(self, moves: list[str]) -> None:
        super().__init__()

        self._moves: list[str] = moves

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> str | None:
        """Get SAN representation for move at `index`."""
        if role == Qt.ItemDataRole.DisplayRole:
            move_index: int = 2 * index.row() + index.column()

            if 0 <= move_index < len(self._moves):
                return self._moves[move_index]

        return None

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        """Get interaction state based on data existence at `index`."""
        if self.data(index) is None:
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def rowCount(
        self,
        parent: QModelIndex | QPersistentModelIndex = QModelIndex(),
    ) -> int:
        """Get calculated row count needed for White/Black moves."""
        all_moves: int = len(self._moves) + 1
        return all_moves // 2

    def columnCount(
        self,
        parent: QModelIndex | QPersistentModelIndex = QModelIndex(),
    ) -> int:
        """Get fixed two column count needed for White/Black moves."""
        return 2

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> int | str | None:
        """Get numbers for rows and player labels for columns."""
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return [self.tr("White"), self.tr("Black")][section]

            if orientation == Qt.Orientation.Vertical:
                return section + 1

        return None

    def reset(self) -> None:
        """Clear stored move data from model."""
        self.beginResetModel()
        self._moves.clear()
        self.endResetModel()

    def update_view(self) -> None:
        """Update view to reflect model changes."""
        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()
