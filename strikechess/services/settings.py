import json
import shutil
from pathlib import Path

from strikechess.utils import root_path


class SettingsService:
    """App settings retrieval and storage, ensuring persistence."""

    def __init__(self) -> None:
        self._user_file_path: Path = self._user_settings_file_path()
        self._default_file_path: Path = self._default_settings_file_path()

        self._ensure_settings_exist()

        self._user_settings: dict[str, dict[str, Any]] = self._load_user_settings()
        self._default_settings: dict[str, dict[str, Any]] = self._load(self._default_file_path)

    def value(self, section: str, key: str) -> Any:
        """Get value of `key` from `section` in settings."""
        default_value: Any = self._default_settings[section][key]

        try:
            stored_value: Any = self._user_settings[section][key]
        except (KeyError, TypeError):
            return default_value

        if not isinstance(stored_value, type(default_value)):
            self._user_settings[section][key] = default_value
            self._save()
            return default_value

        return stored_value

    def set_value(self, section: str, key: str, value: Any) -> None:
        """Set `value` to `key` for `section` in settings."""
        if section not in self._user_settings:
            self._user_settings[section] = {}

        try:
            self._user_settings[section][key] = value
        except TypeError:
            self._user_settings[section] = {key: value}

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
        if not self._user_file_path.exists():
            shutil.copy(self._default_file_path, self._user_file_path)

    def _load_user_settings(self) -> dict[str, dict[str, Any]]:
        """Load user's settings, restoring defaults if unreadable."""
        try:
            return self._load(self._user_file_path)
        except (OSError, ValueError):
            return self._restore_default_settings()

    def _restore_default_settings(self) -> dict[str, dict[str, Any]]:
        """Restore default settings to user's settings.json file."""
        shutil.copy(self._default_file_path, self._user_file_path)
        return self._load(self._default_file_path)

    def _load(self, file_path: Path) -> dict[str, dict[str, Any]]:
        """Load settings from `file_path`."""
        with open(file_path, encoding="utf-8") as file:
            return json.load(file)

    def _save(self) -> None:
        """Save settings to user's settings.json file."""
        temporary_file_path: Path = self._user_file_path.with_suffix(".tmp")

        with open(
            temporary_file_path, mode="w", encoding="utf-8", newline="\n"
        ) as temporary_file:
            json.dump(self._user_settings, temporary_file, indent=2)
            temporary_file.write("\n")

        temporary_file_path.replace(self._user_file_path)
