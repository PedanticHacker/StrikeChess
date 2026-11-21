import sys
from pathlib import Path


def root_path() -> Path:
    """Get path to app's root directory."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent
