from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QLibraryInfo, QTranslator

from strikechess.utils.paths import root_path


def install_translators(language_code: str) -> None:
    """Install app and Qt translators for `language_code`."""
    if language_code == "en":
        return

    app_translations_directory: Path = root_path() / "assets" / "translations"
    qt_translations_directory: str = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)

    app: QApplication = QApplication.instance()
    qt_translator: QTranslator = QTranslator(app)
    app_translator: QTranslator = QTranslator(app)

    if app_translator.load(f"strikechess_{language_code}", str(app_translations_directory)):
        QApplication.installTranslator(app_translator)

    if qt_translator.load(f"qtbase_{language_code}", qt_translations_directory):
        QApplication.installTranslator(qt_translator)
