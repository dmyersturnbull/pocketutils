from pathlib import Path


def load(parts):
    if isinstance(parts, str):
        parts = [parts]
    return Path(Path(__file__).parent.parent, "resources", "common", *parts)
