from functools import partial

from PySide6.QtWidgets import QMenu, QMessageBox

from strikechess.utils import create_action, create_svg_icon


class LanguageMenu(QMenu):
    """Menu with available languages, applied language at top."""

    def __init__(self, parent: QWidget, settings: SettingsService) -> None:
        super().__init__(parent)

        self._settings: SettingsService = settings

        self._english_action: QAction = create_action(
            shortcut="",
            name="English",
            icon=create_svg_icon("american-flag"),
            handler=partial(self.change_language, "en"),
            status_tip=self.tr("Applies the American English language."),
        )
        self._german_action: QAction = create_action(
            shortcut="",
            name="Deutsch",
            icon=create_svg_icon("german-flag"),
            handler=partial(self.change_language, "de"),
            status_tip=self.tr("Applies the German language."),
        )
        self._italian_action: QAction = create_action(
            shortcut="",
            name="Italiano",
            icon=create_svg_icon("italian-flag"),
            handler=partial(self.change_language, "it"),
            status_tip=self.tr("Applies the Italian language."),
        )
        self._spanish_action: QAction = create_action(
            shortcut="",
            name="Español",
            icon=create_svg_icon("spanish-flag"),
            handler=partial(self.change_language, "es"),
            status_tip=self.tr("Applies the Spanish language."),
        )

        self._add_actions()

        self.setTitle(self.tr("Language"))

    def change_language(self, language_code: str) -> None:
        """Save new language setting and prompt for app relaunch."""
        if language_code == self._settings.value("ui", "language"):
            return

        self._settings.set_value("ui", "language", language_code)

        QMessageBox.information(
            self.parentWidget(),
            self.tr("Relaunch Required"),
            self.tr("Please relaunch StrikeChess to apply the new language."),
        )

    def _add_actions(self) -> None:
        """Add language actions with applied language at top."""
        language_actions: dict[str, QAction] = {
            "de": self._german_action,
            "en": self._english_action,
            "es": self._spanish_action,
            "it": self._italian_action,
        }
        language_code: str = self._settings.value("ui", "language")

        if language_code not in language_actions:
            language_code = "en"

        self.addAction(language_actions.pop(language_code))
        self.addSeparator()

        for language_action in language_actions.values():
            self.addAction(language_action)
