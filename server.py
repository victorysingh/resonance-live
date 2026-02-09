from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json, asyncio, time

app = FastAPI()

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= STATE =================
clients = set()
lock = asyncio.Lock()
SESSION_LOG = []

# ================= HEALTH =================
@app.get("/health")
def health():
    return {"ok": True, "ts": time.time()}

# ================= PUSH =================
@app.post("/push")
async def push_data(req: Request):
    data = await req.json()
    print("📥 Received /push:", data)

    # Ignore heartbeat packets
    if data.get("type") == "heartbeat":
        return {"ok": True}

    # Log for export/report
    SESSION_LOG.append(data)

    await broadcast(data)
    return {"ok": True}

# ================= EXPORT =================
@app.get("/export")
def export_session():
    return JSONResponse({
        "session_id": SESSION_LOG[-1]["session_id"] if SESSION_LOG else "none",
        "total_events": len(SESSION_LOG),
        "events": SESSION_LOG
    })

# ================= WS =================
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    async with lock:
        clients.add(ws)
    print("🟢 WS connected:", len(clients))

    try:
        while True:
            # keep alive (we don't actually expect messages)
            await ws.receive_text()
    except:
        pass
    finally:
        async with lock:
            if ws in clients:
                clients.remove(ws)
        print("🔴 WS disconnected:", len(clients))

# ================= BROADCAST =================
async def broadcast(data: dict):
    msg = json.dumps(data)
    print("📤 Broadcasting REAL payload:", msg)

    dead = []
    async with lock:
        for ws in clients:
            try:
                await ws.send_text(msg)
            except:
                dead.append(ws)

        for d in dead:
            if d in clients:
                clients.remove(d)
