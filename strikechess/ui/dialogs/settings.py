from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QDialog,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QLineEdit,
    QHBoxLayout,
    QVBoxLayout,
    QRadioButton,
    QDialogButtonBox,
)


Save: Final[QDialogButtonBox.StandardButton] = QDialogButtonBox.StandardButton.Save
Cancel: Final[QDialogButtonBox.StandardButton] = QDialogButtonBox.StandardButton.Cancel


class SettingsDialog(QDialog):
    """Dialog for editing and saving settings."""

    def __init__(self, parent: QWidget | None, settings: SettingsService) -> None:
        super().__init__(parent)

        self._settings: SettingsService = settings

        self._button_box: QDialogButtonBox = QDialogButtonBox(Save | Cancel)
        self._button_box.button(Save).setDisabled(True)

        self._create_groups()
        self._create_widgets()
        self._set_vertical_layout()
        self._connect_signals_to_slots()

        self._initial_settings: dict[tuple[str, str], Any] = self._current_settings()

        self.setWindowTitle(self.tr("Settings"))

    def disable_engine_group(self) -> None:
        """Disable all settings in engine group."""
        self._engine_group.setDisabled(True)

    def disable_human_name_group(self) -> None:
        """Disable setting in human name group."""
        self._human_name_group.setDisabled(True)

    def disable_time_control_group(self) -> None:
        """Disable all settings in time control group."""
        self._time_control_group.setDisabled(True)

    @Slot()
    def enable_saving(self) -> None:
        """Enable Save button if any setting is edited."""
        self._button_box.button(Save).setEnabled(self._is_edited())

    @Slot()
    def save_settings(self) -> None:
        """Save edited settings to storage."""
        for (section, key), value in self._current_settings().items():
            self._settings.set_value(section, key, value)

    @Slot(bool)
    def show_human_color(self, is_engine_white: bool) -> None:
        """Show human's color as placeholder for human name."""
        human_color: str = self.tr("Black") if is_engine_white else self.tr("White")
        self._human_name.setPlaceholderText(human_color)

    def _create_groups(self) -> None:
        """Create group boxes for related settings."""
        self._engine_group: QGroupBox = QGroupBox(self.tr("Engine"))
        self._human_name_group: QGroupBox = QGroupBox(self.tr("Human name"))
        self._time_control_group: QGroupBox = QGroupBox(self.tr("Time control"))

    def _create_widgets(self) -> None:
        """Create widgets for human name, engine, and time control."""
        human_name_setting: str = self._settings.value("human", "name")
        clock_time_setting: float = self._settings.value("clock", "time")
        is_engine_white: bool = self._settings.value("engine", "is_white")
        clock_increment_setting: float = self._settings.value("clock", "increment")
        is_ponder_enabled: bool = self._settings.value("engine", "is_ponder_enabled")

        self._human_name: QLineEdit = QLineEdit(human_name_setting)
        self.show_human_color(is_engine_white)

        self._engine_black: QRadioButton = QRadioButton(self.tr("Black"))
        self._engine_black.setChecked(not is_engine_white)

        self._engine_white: QRadioButton = QRadioButton(self.tr("White"))
        self._engine_white.setChecked(is_engine_white)

        self._engine_ponder: QCheckBox = QCheckBox(self.tr("Ponder"))
        self._engine_ponder.setChecked(is_ponder_enabled)

        self._clock_time: QComboBox = QComboBox()
        self._clock_time.addItem(self.tr("1 minute"), 60.0)
        self._clock_time.addItem(self.tr("3 minutes"), 180.0)
        self._clock_time.addItem(self.tr("5 minutes"), 300.0)
        self._clock_time.addItem(self.tr("10 minutes"), 600.0)
        self._clock_time.addItem(self.tr("20 minutes"), 1200.0)
        self._clock_time.addItem(self.tr("30 minutes"), 1800.0)
        self._clock_time.addItem(self.tr("1 hour"), 3600.0)
        self._clock_time.addItem(self.tr("2 hours"), 7200.0)
        self._clock_time.setCurrentIndex(self._clock_time.findData(clock_time_setting))

        self._clock_increment: QComboBox = QComboBox()
        self._clock_increment.addItem(self.tr("0 seconds"), 0.0)
        self._clock_increment.addItem(self.tr("6 seconds"), 6.0)
        self._clock_increment.addItem(self.tr("12 seconds"), 12.0)
        self._clock_increment.addItem(self.tr("30 seconds"), 30.0)
        self._clock_increment.setCurrentIndex(
            self._clock_increment.findData(clock_increment_setting)
        )

    def _set_vertical_layout(self) -> None:
        """Set dialog layout, stacking groups and buttons vertically."""
        human_name_layout: QVBoxLayout = QVBoxLayout()
        human_name_layout.addWidget(self._human_name)
        self._human_name_group.setLayout(human_name_layout)

        engine_layout: QVBoxLayout = QVBoxLayout()
        engine_layout.addWidget(self._engine_black)
        engine_layout.addWidget(self._engine_white)
        engine_layout.addWidget(self._engine_ponder)
        self._engine_group.setLayout(engine_layout)

        time_control_layout: QHBoxLayout = QHBoxLayout()
        time_control_layout.addWidget(self._clock_time)
        time_control_layout.addWidget(self._clock_increment)
        self._time_control_group.setLayout(time_control_layout)

        vertical_layout: QVBoxLayout = QVBoxLayout()
        vertical_layout.addWidget(self._human_name_group)
        vertical_layout.addWidget(self._engine_group)
        vertical_layout.addWidget(self._time_control_group)
        vertical_layout.addWidget(self._button_box)
        self.setLayout(vertical_layout)

    def _connect_signals_to_slots(self) -> None:
        """Connect dialog, button, and widget signals to slots."""
        self.accepted.connect(self.save_settings)

        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

        self._clock_time.currentIndexChanged.connect(self.enable_saving)
        self._clock_increment.currentIndexChanged.connect(self.enable_saving)

        self._engine_black.toggled.connect(self.enable_saving)
        self._engine_white.toggled.connect(self.enable_saving)
        self._engine_ponder.toggled.connect(self.enable_saving)
        self._engine_white.toggled.connect(self.show_human_color)

        self._human_name.textChanged.connect(self.enable_saving)

    def _current_settings(self) -> dict[tuple[str, str], Any]:
        """Get current settings from widgets."""
        return {
            ("clock", "time"): self._clock_time.currentData(),
            ("human", "name"): self._human_name.text().strip(),
            ("engine", "is_white"): self._engine_white.isChecked(),
            ("clock", "increment"): self._clock_increment.currentData(),
            ("engine", "is_ponder_enabled"): self._engine_ponder.isChecked(),
        }

    def _is_edited(self) -> bool:
        """Return True if any setting is edited."""
        return self._current_settings() != self._initial_settings
