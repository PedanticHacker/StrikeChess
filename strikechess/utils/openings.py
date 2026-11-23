import json
from functools import lru_cache

from strikechess.utils.paths import root_path


def find_opening(fen: str) -> str | None:
    """Get opening name based on `fen`."""
    return _openings().get(fen)


@lru_cache(maxsize=1)
def _openings() -> dict[str, str]:
    """Load openings from openings.json file."""
    file_path: Path = root_path() / "assets" / "openings.json"

    with open(file_path, encoding="utf-8") as openings_file:
        return json.load(openings_file)
