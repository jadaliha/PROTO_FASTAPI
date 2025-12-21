"""
Unified Todo Server
Single WebSocket endpoint syncs state machine with all clients
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from runtime import load_machine
import protos.app_pb2 as pb

# ═══════════════════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════════════════

MACHINE = None
CLIENTS: list[WebSocket] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    global MACHINE
    MACHINE = load_machine('machines/todo.machine.yaml')
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/protos", StaticFiles(directory="protos"), name="protos")
app.mount("/machines", StaticFiles(directory="machines"), name="machines")

# ═══════════════════════════════════════════════════════════════
# PROTO HELPERS
# ═══════════════════════════════════════════════════════════════

def context_to_proto(ctx: dict) -> pb.AppContext:
    return pb.AppContext(
        items=[pb.Todo(id=i['id'], title=i['title'], completed=i['completed']) for i in ctx.get('items', [])],
        filter=ctx.get('filter', 'all'),
        next_id=ctx.get('next_id', 1)
    )

def state_to_proto() -> pb.MachineState:
    return pb.MachineState(
        state=MACHINE.state,
        context=context_to_proto(MACHINE.context),
        version=MACHINE.version
    )

def decode_payload(event_type: str, data: bytes) -> dict:
    """Decode event payload based on type"""
    if event_type == 'CREATE':
        p = pb.CreatePayload(); p.ParseFromString(data)
        return {'title': p.title}
    if event_type == 'TOGGLE':
        p = pb.TogglePayload(); p.ParseFromString(data)
        return {'id': p.id, 'completed': p.completed}
    if event_type == 'DELETE':
        p = pb.DeletePayload(); p.ParseFromString(data)
        return {'id': p.id}
    if event_type == 'FILTER':
        p = pb.FilterPayload(); p.ParseFromString(data)
        return {'filter': p.filter}
    return {}

# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def index():
    return open('templates/index.html').read()

@app.websocket("/ws")
async def websocket_sync(ws: WebSocket):
    await ws.accept()
    CLIENTS.append(ws)
    
    # Send current state
    msg = pb.SyncMessage(snapshot=state_to_proto())
    await ws.send_bytes(msg.SerializeToString())
    
    try:
        while True:
            data = await ws.receive_bytes()
            sync_msg = pb.SyncMessage()
            sync_msg.ParseFromString(data)
            
            if sync_msg.HasField('event'):
                event = sync_msg.event
                payload = decode_payload(event.type, event.payload)
                
                success, error = MACHINE.send(event.type, payload)
                
                if success:
                    # Broadcast new state to ALL clients
                    update = pb.SyncMessage(update=state_to_proto())
                    for client in CLIENTS:
                        try:
                            await client.send_bytes(update.SerializeToString())
                        except:
                            pass
                else:
                    # Send error only to this client
                    err = pb.SyncMessage(error=error or "Unknown error")
                    await ws.send_bytes(err.SerializeToString())
    
    except WebSocketDisconnect:
        CLIENTS.remove(ws)

# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

