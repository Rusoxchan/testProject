"""
server.py — FastAPI backend with Dynamic Download Queue.
"""

import sys
import threading
import queue
import asyncio
import re
import uuid
from typing import List, Dict, Optional
from pathlib import Path

from fastapi import FastAPI, Request, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Import core logic
try:
    from core import download_video, OUTPUT_DIR
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    from core import download_video, OUTPUT_DIR

app = FastAPI()

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ──────────────────────────────────────────────
# Queue System
# ──────────────────────────────────────────────
class DownloadItem(BaseModel):
    id: str
    url: str
    format: str
    quality: str
    status: str = "pending"  # pending, downloading, completed, error
    progress: float = 0.0
    title: str = "Processing..."
    logs: List[str] = []

class DownloadQueue:
    def __init__(self):
        self.queue = queue.Queue()
        self.items: Dict[str, DownloadItem] = {}
        self.active_id: Optional[str] = None
        self.history: List[str] = []  # List of IDs in order
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        
        # WebSocket connections
        self.active_websockets: List[WebSocket] = []

    def add_item(self, url: str, fmt: str, qual: str) -> str:
        item_id = str(uuid.uuid4())[:8]
        item = DownloadItem(id=item_id, url=url, format=fmt, quality=qual)
        self.items[item_id] = item
        self.history.append(item_id)
        self.queue.put(item_id)
        self.broadcast_update()
        return item_id

    def get_all_items(self) -> List[Dict]:
        # Return items in order: Active -> Pending -> Completed (reversed)
        # Actually simplest is just return all in history order
        return [self.items[mid].model_dump() for mid in self.history]

    def _worker(self):
        while True:
            item_id = self.queue.get()
            self.active_id = item_id
            item = self.items[item_id]
            
            item.status = "downloading"
            self.broadcast_update()

            def on_output(line):
                item.logs.append(line)
                # Parse progress
                self._parse_progress(item, line)
                # We could broadcast every line, but that's heavy. 
                # Let's broadcast on percentage change or every N lines if needed.
                # For now, just broadcast progress changes > 1% or status change
                pass

            def on_done(retcode):
                item.status = "completed" if retcode == 0 else "error"
                item.progress = 100.0 if retcode == 0 else item.progress
                self.active_id = None
                self.broadcast_update()
            
            # Run download
            try:
                download_video(item.url, item.format, item.quality, on_output, on_done)
            except Exception as e:
                item.status = "error"
                item.logs.append(str(e))
                self.broadcast_update()
            
            self.queue.task_done()

    def _parse_progress(self, item: DownloadItem, line: str):
        # yt-dlp output example: "[download]  45.0% of 10.00MiB at 2.00MiB/s ETA 00:05"
        # Regex to find percentage
        match = re.search(r'(\d+\.\d+)%', line)
        if match:
            try:
                val = float(match.group(1))
                if val > item.progress:
                    item.progress = val
                    self.broadcast_update()
            except ValueError:
                pass
        
        # Also try to grab title if present in logs
        if "[download] Destination:" in line:
            parts = line.split("Destination:")
            if len(parts) > 1:
                filename = Path(parts[1].strip()).name
                # Remove "yt_" prefix and extension roughly
                name = filename.replace("yt_", "").rsplit(".", 2)[0] 
                item.title = name
                self.broadcast_update()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_websockets.append(websocket)
        # Send initial state
        await websocket.send_json({"type": "state", "data": self.get_all_items()})

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_websockets:
            self.active_websockets.remove(websocket)

    def broadcast_update(self):
        # Fire and forget async broadcast in thread-safe way?
        # FastAPI WebSockets are async. We need to run this on the event loop.
        # Ideally, we put updates in an async queue or use run_coroutine_threadsafe.
        # For simplicity, we'll let the endpoint poll or use a dedicated broadcaster loop.
        
        # Better approach: Queue updates to an asyncio loop.
        # But we are in a thread. 
        # Let's use a global event loop reference? No, messy.
        
        # PRO PATTERN: Store a reference to the event loop or use a thread-safe flag
        # that the websocket endpoint checks.
        pass # See websocket_endpoint implementation below

# Singleton
manager = DownloadQueue()

# ──────────────────────────────────────────────
# Pydantic Models & Routes
# ──────────────────────────────────────────────
class DownloadRequest(BaseModel):
    url: str
    format: str = "merged"
    quality: str = "best"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return TEMPLATES.TemplateResponse("index.html", {"request": request})

@app.post("/api/download")
async def start_download(req: DownloadRequest):
    item_id = manager.add_item(req.url, req.format, req.quality)
    return {"status": "ok", "message": "Added to queue", "id": item_id}

@app.websocket("/ws/queue")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Loop to send updates
        # Since manager.broadcast_update() is hard to call from thread to async loop directly
        # without complex setup, we will just Poll for changes? 
        # Polling is easier to implement reliably in this mixed context.
        # Or better: Manager has a 'change_event' (threading.Event) we can watch?
        # No, asyncio.Event is better.
        
        last_state = []
        while True:
            current_state = manager.get_all_items()
            # Simple diff or just always send if active (optimized by client)
            # Let's send only if hash changed? JSON serialization is cheap enough for <100 items.
            if current_state != last_state:
                await websocket.send_json({"type": "state", "data": current_state})
                last_state = current_state
            
            await asyncio.sleep(0.5) # 2 updates per second is enough for progress bars
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
