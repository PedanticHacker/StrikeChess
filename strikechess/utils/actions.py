from PySide6.QtGui import QAction


def create_action(
    icon: QIcon,
    name: str,
    handler: Callable[[], None],
    shortcut: str,
    status_tip: str,
) -> QAction:
    """Create action for menu item or tool bar button."""
    action: QAction = QAction(icon, name)
    action.setShortcut(shortcut)
    action.setStatusTip(status_tip)
    action.triggered.connect(handler)
    return action
