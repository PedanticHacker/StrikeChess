from enum import StrEnum
from functools import partial

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMenu

from strikechess.utils import create_action, create_colored_icon


class ThemeName(StrEnum):
    """Available dark and light themes."""

    DarkMint = "dark-mint"
    DarkOcean = "dark-ocean"
    LightMint = "light-mint"
    DarkForest = "dark-forest"
    DarkNebula = "dark-nebula"
    LightOcean = "light-ocean"
    LightForest = "light-forest"
    LightNebula = "light-nebula"

    @property
    def text(self) -> str:
        """Theme name in title-cased format."""
        return self.value.replace("-", " ").title()


class ThemeMenu(QMenu):
    """Menu with available dark and light themes."""

    theme_selected: ClassVar[Signal] = Signal(str)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._dark_forest_action: QAction = create_action(
            shortcut="Alt+1",
            name=self.tr("Dark Forest"),
            icon=create_colored_icon("#1f291f"),
            status_tip=self.tr("Applies the Dark Forest theme."),
            handler=partial(self.theme_selected.emit, ThemeName.DarkForest),
        )
        self._dark_mint_action: QAction = create_action(
            shortcut="Alt+2",
            name=self.tr("Dark Mint"),
            icon=create_colored_icon("#1a2e2e"),
            status_tip=self.tr("Applies the Dark Mint theme."),
            handler=partial(self.theme_selected.emit, ThemeName.DarkMint),
        )
        self._dark_nebula_action: QAction = create_action(
            shortcut="Alt+3",
            name=self.tr("Dark Nebula"),
            icon=create_colored_icon("#351d4d"),
            status_tip=self.tr("Applies the Dark Nebula theme."),
            handler=partial(self.theme_selected.emit, ThemeName.DarkNebula),
        )
        self._dark_ocean_action: QAction = create_action(
            shortcut="Alt+4",
            name=self.tr("Dark Ocean"),
            icon=create_colored_icon("#2e455e"),
            status_tip=self.tr("Applies the Dark Ocean theme."),
            handler=partial(self.theme_selected.emit, ThemeName.DarkOcean),
        )
        self._light_forest_action: QAction = create_action(
            shortcut="Alt+5",
            name=self.tr("Light Forest"),
            icon=create_colored_icon("#95a88c"),
            status_tip=self.tr("Applies the Light Forest theme."),
            handler=partial(self.theme_selected.emit, ThemeName.LightForest),
        )
        self._light_mint_action: QAction = create_action(
            shortcut="Alt+6",
            name=self.tr("Light Mint"),
            icon=create_colored_icon("#97cbc5"),
            status_tip=self.tr("Applies the Light Mint theme."),
            handler=partial(self.theme_selected.emit, ThemeName.LightMint),
        )
        self._light_nebula_action: QAction = create_action(
            shortcut="Alt+7",
            name=self.tr("Light Nebula"),
            icon=create_colored_icon("#c385f7"),
            status_tip=self.tr("Applies the Light Nebula theme."),
            handler=partial(self.theme_selected.emit, ThemeName.LightNebula),
        )
        self._light_ocean_action: QAction = create_action(
            shortcut="Alt+8",
            name=self.tr("Light Ocean"),
            icon=create_colored_icon("#87a6c3"),
            status_tip=self.tr("Applies the Light Ocean theme."),
            handler=partial(self.theme_selected.emit, ThemeName.LightOcean),
        )

        self.addAction(self._dark_forest_action)
        self.addAction(self._dark_mint_action)
        self.addAction(self._dark_nebula_action)
        self.addAction(self._dark_ocean_action)
        self.addAction(self._light_forest_action)
        self.addAction(self._light_mint_action)
        self.addAction(self._light_nebula_action)
        self.addAction(self._light_ocean_action)

        self.setTitle(self.tr("Theme"))

    def theme_name(self, file_name: str) -> str:
        """Get translated theme name based on `file_name`."""
        return self.tr(ThemeName(file_name).text)
