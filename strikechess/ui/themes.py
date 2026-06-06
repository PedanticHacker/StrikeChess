from enum import StrEnum


class ClockStyleSheet(StrEnum):
    """QSS style sheets for clock widgets."""

    Black = "color: white; background-color: black;"
    White = "color: black; background-color: white;"


class ThemeName(StrEnum):
    """Available dark and light themes."""

    DarkForest = "dark-forest"
    DarkMint = "dark-mint"
    DarkNebula = "dark-nebula"
    DarkOcean = "dark-ocean"
    LightForest = "light-forest"
    LightMint = "light-mint"
    LightNebula = "light-nebula"
    LightOcean = "light-ocean"

    @property
    def text(self) -> str:
        """Theme name in title-cased format."""
        return self.value.replace("-", " ").title()


THEME_SWATCH: dict[ThemeName, str] = {
    ThemeName.DarkForest: "#1f291f",
    ThemeName.DarkMint: "#1a2e2e",
    ThemeName.DarkNebula: "#351d4d",
    ThemeName.DarkOcean: "#2e455e",
    ThemeName.LightForest: "#95a88c",
    ThemeName.LightMint: "#97cbc5",
    ThemeName.LightNebula: "#c385f7",
    ThemeName.LightOcean: "#87a6c3",
}
