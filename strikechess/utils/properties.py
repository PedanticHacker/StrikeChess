from PySide6.QtGui import QColor
from PySide6.QtCore import Property


def create_color_property(attribute_name: str) -> Property:
    """Create QColor property stored in `attribute_name`."""
    return Property(
        QColor,
        lambda self: getattr(self, attribute_name),
        lambda self, color: setattr(self, attribute_name, color),
    )
