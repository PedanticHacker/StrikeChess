import json
import shutil
from pathlib import Path

from strikechess.utils import root_path


class SettingsService:
    """App settings retrieval and storage, ensuring persistence."""

    def __init__(self) -> None:
        self._ensure_settings_exist()

        self._file_path: Path = self._user_settings_file_path()
        self._default_data: dict[str, dict[str, Any]] = self._load(
            self._default_settings_file_path()
        )
        self._data: dict[str, dict[str, Any]] = self._load(self._file_path)
        self._validate_and_repair()

    def value(self, section: str, key: str) -> Any:
        """Get value of `key` from `section` in settings."""
        try:
            return self._data[section][key]
        except KeyError:
            return self._default_data[section][key]

    def set_value(self, section: str, key: str, value: Any) -> None:
        """Set `value` to `key` for `section` in settings."""
        self._data[section][key] = value
        self._save()

    def _user_settings_file_path(self) -> Path:
        """Get path to user's settings.json file."""
        user_directory: Path = Path.home() / ".StrikeChess"
        user_directory.mkdir(exist_ok=True)
        return user_directory / "settings.json"

    def _default_settings_file_path(self) -> Path:
        """Get path to default settings.json file."""
        return root_path() / "settings.json"

    def _ensure_settings_exist(self) -> None:
        """Copy default settings if user's settings don't exist."""
        user_file_path: Path = self._user_settings_file_path()
        default_file_path: Path = self._default_settings_file_path()

        if not user_file_path.exists():
            shutil.copy(default_file_path, user_file_path)

    def _validate_and_repair(self) -> None:
        """Validate settings and repair data with mismatched types."""
        is_repaired: bool = False

        for section, keys in self._default_data.items():
            if section not in self._data or not isinstance(self._data[section], dict):
                self._data[section] = dict(keys)
                is_repaired = True
                continue

            for key, default_value in keys.items():
                if key not in self._data[section]:
                    self._data[section][key] = default_value
                    is_repaired = True
                elif not isinstance(self._data[section][key], type(default_value)):
                    self._data[section][key] = default_value
                    is_repaired = True

        if is_repaired:
            self._save()

    def _load(self, file_path: Path) -> dict[str, dict[str, Any]]:
        """Load settings from `file_path`."""
        with open(file_path, encoding="utf-8") as file:
            return json.load(file)

    def _save(self) -> None:
        """Save settings to user's settings.json file."""
        with open(self._file_path, mode="w", encoding="utf-8", newline="\n") as file:
            json.dump(self._data, file, indent=2)
            file.write("\n")
