from enum import StrEnum

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect

from strikechess.utils import root_path


class SoundEffectName(StrEnum):
    """Sound effect names for game events."""

    Capture = "capture"
    Castling = "castling"
    Check = "check"
    GameOver = "game-over"
    Move = "move"
    Promotion = "promotion"


class SoundPlayer:
    """Sound effect playback for game events."""

    def __init__(self, game: GameService) -> None:
        self._game: GameService = game

        self._sound_effects: dict[SoundEffectName, QSoundEffect] = self._preload_sound_effects()

    def play(self, move: Move) -> None:
        """Play sound effect for `move`."""
        sound_effect_name: SoundEffectName = self._sound_effect_name(move)
        self._sound_effects[sound_effect_name].play()

    def play_game_over(self) -> None:
        """Play game-over sound effect."""
        self._sound_effects[SoundEffectName.GameOver].play()

    def _preload_sound_effects(self) -> dict[SoundEffectName, QSoundEffect]:
        """Optimize playback performance by preloading sound effects."""
        sound_effects: dict[SoundEffectName, QSoundEffect] = {}

        for name in SoundEffectName:
            file_path: Path = root_path() / "assets" / "audio" / f"{name}.wav"
            file_url: QUrl = QUrl(f"file:{file_path}")
            sound_effect: QSoundEffect = QSoundEffect()
            sound_effect.setSource(file_url)
            sound_effects[name] = sound_effect

        return sound_effects

    def _sound_effect_name(self, move: Move) -> SoundEffectName:
        """Get sound effect name based on `move`."""
        if self._game.is_over_after(move):
            return SoundEffectName.GameOver
        if self._game.gives_check(move):
            return SoundEffectName.Check
        if move.promotion is not None:
            return SoundEffectName.Promotion
        if self._game.is_capture(move):
            return SoundEffectName.Capture
        if self._game.is_castling(move):
            return SoundEffectName.Castling
        return SoundEffectName.Move
