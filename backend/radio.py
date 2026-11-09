import asyncio
import random
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator

from .library import scan_library

CHUNK_SIZE = 16 * 1024

class RadioEngine:
    """One shared audio broadcast. Every listener receives the same live audio."""

    def __init__(self, config: dict, base_dir: Path):
        self.config = config
        self.base_dir = base_dir
        self.tracks: list[dict] = []
        self.shuffle_bag: list[dict] = []
        self.current_track: dict | None = None
        self.started_at: str | None = None
        self.listeners: set[asyncio.Queue] = set()
        self.task: asyncio.Task | None = None
        self.skip_event = asyncio.Event()
        self.lock = asyncio.Lock()
        self.db_path = base_dir / "data" / "history.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    path TEXT NOT NULL,
                    played_at TEXT NOT NULL
                )
            """)

    async def start(self):
        self.refresh_library()
        self.task = asyncio.create_task(self._broadcast_loop())

    async def stop(self):
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    def refresh_library(self):
        self.tracks = scan_library(self.config["music_directory"])
        known = {t["path"] for t in self.tracks}
        self.shuffle_bag = [t for t in self.shuffle_bag if t["path"] in known]

    def _next_track(self):
        self.refresh_library()
        if not self.tracks:
            return None
        if not self.shuffle_bag:
            self.shuffle_bag = self.tracks.copy()
            random.shuffle(self.shuffle_bag)
            # Avoid an immediate repeat when a new cycle begins.
            if len(self.shuffle_bag) > 1 and self.current_track:
                if self.shuffle_bag[-1]["path"] == self.current_track["path"]:
                    self.shuffle_bag[0], self.shuffle_bag[-1] = self.shuffle_bag[-1], self.shuffle_bag[0]
        return self.shuffle_bag.pop() if self.shuffle_bag else None

    async def _broadcast_loop(self):
        while True:
            track = self._next_track()
            if track is None:
                self.current_track = None
                await asyncio.sleep(10)
                continue

            self.current_track = track
            self.started_at = datetime.now(timezone.utc).isoformat()
            with self._connect() as db:
                db.execute(
                    "INSERT INTO history(title, path, played_at) VALUES (?, ?, ?)",
                    (track["title"], track["path"], self.started_at),
                )

            await self._play_track(track)

    async def _play_track(self, track: dict):
        ffmpeg = self.config.get("ffmpeg_path", "ffmpeg")
        bitrate = str(self.config.get("stream_bitrate", "192k"))
        command = [
            ffmpeg, "-hide_banner", "-loglevel", "error",
            "-i", track["path"],
            "-vn", "-ac", "2", "-ar", "44100",
            "-codec:a", "libmp3lame", "-b:a", bitrate,
            "-f", "mp3", "pipe:1",
        ]
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except FileNotFoundError:
            await asyncio.sleep(5)
            return

        try:
            while True:
                if self.skip_event.is_set():
                    self.skip_event.clear()
                    process.terminate()
                    break
                chunk_task = asyncio.create_task(process.stdout.read(CHUNK_SIZE))
                skip_task = asyncio.create_task(self.skip_event.wait())
                done, pending = await asyncio.wait(
                    {chunk_task, skip_task}, return_when=asyncio.FIRST_COMPLETED
                )
                for task in pending:
                    task.cancel()
                if skip_task in done and skip_task.result():
                    self.skip_event.clear()
                    process.terminate()
                    break
                chunk = chunk_task.result()
                if not chunk:
                    break
                await self._publish(chunk)
            await process.wait()
        finally:
            if process.returncode is None:
                process.kill()
                await process.wait()

    async def _publish(self, chunk: bytes):
        async with self.lock:
            queues = list(self.listeners)
        for queue in queues:
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(chunk)
            except asyncio.QueueFull:
                pass

    async def subscribe(self) -> AsyncIterator[bytes]:
        queue: asyncio.Queue = asyncio.Queue(maxsize=64)
        async with self.lock:
            self.listeners.add(queue)
        try:
            while True:
                chunk = await queue.get()
                yield chunk
        finally:
            async with self.lock:
                self.listeners.discard(queue)

    def request_skip(self):
        self.skip_event.set()

    def status(self):
        return {
            "station": self.config.get("station_name", "windflower.chroma"),
            "online": bool(self.task and not self.task.done()),
            "current_track": self.current_track,
            "started_at": self.started_at,
            "library_count": len(self.tracks),
            "listeners": len(self.listeners),
            "stream_url": "/stream",
        }

    def get_history(self, limit: int = 30):
        with self._connect() as db:
            rows = db.execute(
                "SELECT title, path, played_at FROM history ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [{"title": r[0], "path": r[1], "played_at": r[2]} for r in rows]
