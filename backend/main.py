from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .radio import RadioEngine
from .library import scan_library
from .config import load_config

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG = load_config(BASE_DIR / "config" / "config.json")
radio = RadioEngine(CONFIG, BASE_DIR)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await radio.start()
    yield
    await radio.stop()

app = FastAPI(title="windflower.chroma", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/status")
async def status():
    return radio.status()

@app.get("/api/library")
async def library():
    return {"tracks": scan_library(CONFIG["music_directory"])}

@app.get("/api/history")
async def history(limit: int = 30):
    return {"history": radio.get_history(max(1, min(limit, 200)))}

@app.post("/api/skip")
async def skip():
    radio.request_skip()
    return {"ok": True, "message": "Skip solicitado."}

@app.get("/stream")
async def stream():
    return StreamingResponse(
        radio.subscribe(),
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "no-cache, no-store",
            "icy-name": CONFIG.get("station_name", "windflower.chroma"),
            "icy-description": "Local music radio",
            "Access-Control-Allow-Origin": "*",
        },
    )

@app.get("/")
async def index():
    return FileResponse(BASE_DIR / "frontend" / "index.html")

app.mount("/assets", StaticFiles(directory=BASE_DIR / "frontend"), name="assets")
