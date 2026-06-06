import json
import shutil
from pathlib import Path

from strikechess.utils import root_path


class SettingsService:
    """App settings retrieval and storage, ensuring persistence."""

    _allowed_values: dict[str, dict[str, set[str]]] = {
        "ui": {
            "theme": {
                "dark-forest",
                "dark-mint",
                "dark-nebula",
                "dark-ocean",
                "light-forest",
                "light-mint",
                "light-nebula",
                "light-ocean",
            },
            "language": {"en", "de", "es", "it"},
        },
    }

    def __init__(self) -> None:
        self._ensure_settings_exist()

        self._file_path: Path = self._user_settings_file_path()
        self._user_settings: dict[str, dict[str, Any]] = self._load(self._file_path)
        self._default_settings: dict[str, dict[str, Any]] = self._load(
            self._default_settings_file_path()
        )

    def value(self, section: str, key: str) -> Any:
        """Get value of `key` from `section` in settings."""
        default_value: Any = self._default_settings[section][key]

        try:
            stored_value: Any = self._user_settings[section][key]
        except KeyError:
            return default_value

        if not isinstance(stored_value, type(default_value)):
            return self._reset_to_default(section, key, default_value)

        if not self._is_allowed(section, key, stored_value):
            return self._reset_to_default(section, key, default_value)

        return stored_value

    def set_value(self, section: str, key: str, value: Any) -> None:
        """Set `value` to `key` for `section` in settings."""
        self._user_settings[section][key] = value
        self._save()

    def _is_allowed(self, section: str, key: str, value: Any) -> bool:
        """Return True if `value` is within allowed set for `key`."""
        allowed_values: set[str] | None = self._allowed_values.get(section, {}).get(key)
        return allowed_values is None or value in allowed_values

    def _reset_to_default(self, section: str, key: str, default_value: Any) -> Any:
        """Store and return `default_value` for invalid `key` in `section`."""
        self._user_settings[section][key] = default_value
        self._save()
        return default_value

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

    def _load(self, file_path: Path) -> dict[str, dict[str, Any]]:
        """Load settings from `file_path`."""
        with open(file_path, encoding="utf-8") as file:
            return json.load(file)

    def _save(self) -> None:
        """Save settings to user's settings.json file."""
        with open(self._file_path, mode="w", encoding="utf-8", newline="\n") as file:
            json.dump(self._user_settings, file, indent=2)
            file.write("\n")
