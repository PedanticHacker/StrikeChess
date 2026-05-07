from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
)


Cancel: Final[QDialogButtonBox.StandardButton] = QDialogButtonBox.StandardButton.Cancel
Save: Final[QDialogButtonBox.StandardButton] = QDialogButtonBox.StandardButton.Save


class SettingsDialog(QDialog):
    """Dialog for editing and saving settings."""

    def __init__(self, settings: SettingsService) -> None:
        super().__init__()

        self._settings: SettingsService = settings

        self._initial_settings: dict[str, bool | float | str] = {
            "clock_increment": self._settings.value("clock", "increment"),
            "clock_time": self._settings.value("clock", "time"),
            "human_name": self._settings.value("human", "name"),
            "is_engine_ponder_enabled": self._settings.value("engine", "is_ponder_enabled"),
            "is_engine_white": self._settings.value("engine", "is_white"),
        }

        self._button_box: QDialogButtonBox = QDialogButtonBox(Save | Cancel)
        self._button_box.button(Save).setDisabled(True)

        self.create_groups()
        self.create_options()
        self.set_vertical_layout()
        self.connect_signals_to_slots()

        self.setWindowTitle(self.tr("Settings"))

    def create_groups(self) -> None:
        """Create group boxes for related settings."""
        self._human_name_group: QGroupBox = QGroupBox(self.tr("Human name"))
        self._engine_group: QGroupBox = QGroupBox(self.tr("Engine"))
        self._time_control_group: QGroupBox = QGroupBox(self.tr("Time control"))

    def create_options(self) -> None:
        """Create option widgets to represent settings."""
        clock_increment: float = self._settings.value("clock", "increment")
        clock_time: float = self._settings.value("clock", "time")
        human_name: str = self._settings.value("human", "name")
        is_engine_white: bool = self._settings.value("engine", "is_white")
        is_ponder_enabled: bool = self._settings.value("engine", "is_ponder_enabled")

        self._human_name_option: QLineEdit = QLineEdit(human_name)
        self._human_name_option.setPlaceholderText(self.tr("Player"))

        self._engine_black_option: QRadioButton = QRadioButton(self.tr("Black"))
        self._engine_black_option.setChecked(not is_engine_white)

        self._engine_white_option: QRadioButton = QRadioButton(self.tr("White"))
        self._engine_white_option.setChecked(is_engine_white)

        self._engine_ponder_option: QCheckBox = QCheckBox(self.tr("Ponder"))
        self._engine_ponder_option.setChecked(is_ponder_enabled)

        self._clock_time_option: QComboBox = QComboBox()
        self._clock_time_option.addItem(self.tr("1 minute"), 60.0)
        self._clock_time_option.addItem(self.tr("3 minutes"), 180.0)
        self._clock_time_option.addItem(self.tr("5 minutes"), 300.0)
        self._clock_time_option.addItem(self.tr("10 minutes"), 600.0)
        self._clock_time_option.addItem(self.tr("20 minutes"), 1200.0)
        self._clock_time_option.addItem(self.tr("30 minutes"), 1800.0)
        self._clock_time_option.addItem(self.tr("1 hour"), 3600.0)
        self._clock_time_option.addItem(self.tr("2 hours"), 7200.0)
        self._clock_time_option.setCurrentIndex(self._clock_time_option.findData(clock_time))

        self._clock_increment_option: QComboBox = QComboBox()
        self._clock_increment_option.addItem(self.tr("0 seconds"), 0.0)
        self._clock_increment_option.addItem(self.tr("6 seconds"), 6.0)
        self._clock_increment_option.addItem(self.tr("12 seconds"), 12.0)
        self._clock_increment_option.addItem(self.tr("30 seconds"), 30.0)
        self._clock_increment_option.setCurrentIndex(
            self._clock_increment_option.findData(clock_increment)
        )

    def set_vertical_layout(self) -> None:
        """Set dialog layout for widgets to be arranged vertically."""
        human_name_layout: QVBoxLayout = QVBoxLayout()
        human_name_layout.addWidget(self._human_name_option)
        self._human_name_group.setLayout(human_name_layout)

        engine_layout: QVBoxLayout = QVBoxLayout()
        engine_layout.addWidget(self._engine_black_option)
        engine_layout.addWidget(self._engine_white_option)
        engine_layout.addWidget(self._engine_ponder_option)
        self._engine_group.setLayout(engine_layout)

        time_control_layout: QHBoxLayout = QHBoxLayout()
        time_control_layout.addWidget(self._clock_time_option)
        time_control_layout.addWidget(self._clock_increment_option)
        self._time_control_group.setLayout(time_control_layout)

        vertical_layout: QVBoxLayout = QVBoxLayout()
        vertical_layout.addWidget(self._human_name_group)
        vertical_layout.addWidget(self._engine_group)
        vertical_layout.addWidget(self._time_control_group)
        vertical_layout.addWidget(self._button_box)
        self.setLayout(vertical_layout)

    def connect_signals_to_slots(self) -> None:
        """Connect signals to appropriate slot methods."""
        self.accepted.connect(self.save_settings)

        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

        self._clock_increment_option.currentIndexChanged.connect(self.enable_saving)
        self._clock_time_option.currentIndexChanged.connect(self.enable_saving)

        self._engine_black_option.toggled.connect(self.enable_saving)
        self._engine_ponder_option.toggled.connect(self.enable_saving)
        self._engine_white_option.toggled.connect(self.enable_saving)

        self._human_name_option.textChanged.connect(self.enable_saving)

    def disable_engine_group(self) -> None:
        """Disable engine settings if no engine is loaded."""
        self._engine_group.setDisabled(True)

    def disable_human_name_group(self) -> None:
        """Disable changing human name to preserve player identity."""
        self._human_name_group.setDisabled(True)

    def disable_time_control_group(self) -> None:
        """Disable time control settings if game is in progress."""
        self._time_control_group.setDisabled(True)

    def is_edited(self) -> bool:
        """Return True if any setting is edited."""
        current_settings: dict[str, bool | float | str] = {
            "clock_increment": self._clock_increment_option.currentData(),
            "clock_time": self._clock_time_option.currentData(),
            "human_name": self._human_name_option.text().strip(),
            "is_engine_ponder_enabled": self._engine_ponder_option.isChecked(),
            "is_engine_white": self._engine_white_option.isChecked(),
        }
        return current_settings != self._initial_settings

    @Slot()
    def enable_saving(self) -> None:
        """Enable Save button if any setting is edited."""
        self._button_box.button(Save).setEnabled(self.is_edited())

    @Slot()
    def save_settings(self) -> None:
        """Save edited settings to storage."""
        self._settings.set_value(
            "human",
            "name",
            self._human_name_option.text().strip(),
        )
        self._settings.set_value(
            "engine",
            "is_white",
            self._engine_white_option.isChecked(),
        )
        self._settings.set_value(
            "engine",
            "is_ponder_enabled",
            self._engine_ponder_option.isChecked(),
        )
        self._settings.set_value(
            "clock",
            "time",
            self._clock_time_option.currentData(),
        )
        self._settings.set_value(
            "clock",
            "increment",
            self._clock_increment_option.currentData(),
        )
