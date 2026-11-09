import json
from pathlib import Path

def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    music_dir = Path(config["music_directory"]).expanduser()
    config["music_directory"] = str(music_dir)
    config["supported_extensions"] = [
        ext.lower() if ext.startswith(".") else f".{ext.lower()}"
        for ext in config.get("supported_extensions", [])
    ]
    return config
