from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect


class SoundEffect:
    """Playback of sound effects appropriate for type of move."""

    def __init__(self, game: Game) -> None:
        self._game: Game = game

        self._sound_effects: dict[str, QSoundEffect] = {}
        self._preload_sound_effects()

    def _preload_sound_effects(self) -> None:
        """Preload sound effects for optimized playback performance."""
        file_names: tuple[str, ...] = (
            "game-over",
            "check",
            "promotion",
            "capture",
            "castling",
            "move",
        )

        for file_name in file_names:
            file_url: QUrl = QUrl(f"file:strikechess/assets/audio/{file_name}.wav")
            sound_effect: QSoundEffect = QSoundEffect()
            sound_effect.setSource(file_url)
            self._sound_effects[file_name] = sound_effect

    def _sound_effect_name(self, move: Move) -> str:
        """Get name of sound effect based on `move`."""
        if self._game.is_over_after(move):
            return "game-over"
        if self._game.gives_check(move):
            return "check"
        if move.promotion is not None:
            return "promotion"
        if self._game.board.is_capture(move):
            return "capture"
        if self._game.board.is_castling(move):
            return "castling"
        return "move"

    def play(self, move: Move) -> None:
        """Play sound effect for `move`."""
        sound_effect_name: str = self._sound_effect_name(move)
        self._sound_effects[sound_effect_name].play()

    def play_time_expired(self) -> None:
        """Play game-over sound effect for expired time event."""
        self._sound_effects["game-over"].play()
