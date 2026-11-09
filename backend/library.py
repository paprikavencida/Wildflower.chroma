from pathlib import Path

def scan_library(directory: str) -> list[dict]:
    root = Path(directory).expanduser()
    extensions = {".mp3", ".flac", ".wav", ".ogg", ".opus", ".m4a", ".aac", ".wma"}
    if not root.exists():
        return []

    tracks = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in extensions:
            tracks.append({
                "title": path.stem,
                "filename": path.name,
                "path": str(path),
                "extension": path.suffix.lower(),
            })
    return tracks
