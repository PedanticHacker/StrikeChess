from PySide6.QtWidgets import QMenuBar


class MenuBar(QMenuBar):
    """Menu bar with actions in separate menus."""

    def __init__(
        self,
        main_window: MainWindow,
        theme_menu: ThemeMenu,
        language_menu: LanguageMenu,
    ) -> None:
        super().__init__(main_window)

        general_menu: QMenu = self.addMenu(self.tr("General"))
        self.addMenu(theme_menu)
        self.addMenu(language_menu)
        edit_menu: QMenu = self.addMenu(self.tr("Edit"))
        help_menu: QMenu = self.addMenu(self.tr("Help"))

        general_menu.addAction(main_window.load_from_pgn_action)
        general_menu.addAction(main_window.save_as_pgn_action)
        general_menu.addSeparator()
        general_menu.addAction(main_window.load_engine_action)
        general_menu.addAction(main_window.unload_engine_action)
        general_menu.addSeparator()
        general_menu.addAction(main_window.quit_action)

        edit_menu.addAction(main_window.show_settings_dialog_action)

        help_menu.addAction(main_window.about_action)
