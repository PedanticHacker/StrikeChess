from pathlib import Path

from PySide6.QtWidgets import QFileDialog


def save_with_file_manager(
    parent: QWidget | None, caption: str, file_filter: str, suggested_name: str
) -> str | None:
    """Show file manager to save file and return selected path."""
    file_path, _ = QFileDialog.getSaveFileName(
        parent=parent,
        caption=caption,
        filter=file_filter,
        dir=str(Path.home() / suggested_name),
    )
    return file_path or None


def show_file_manager(parent: QWidget | None, caption: str, file_filter: str) -> str | None:
    """Show file manager to open file and return selected path."""
    file_path, _ = QFileDialog.getOpenFileName(
        parent=parent,
        caption=caption,
        filter=file_filter,
        dir=str(Path.home()),
    )
    return file_path or None
