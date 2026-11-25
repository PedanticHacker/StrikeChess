from pathlib import Path


def root_path() -> Path:
    """Get path to app root directory."""
    return Path(__file__).parent.parent
