---
name: FastAPI Backend
description: Implement REST/WebSocket backend using FastAPI with DuckDB database, Protocol Buffers serialization, and clean decorator-based patterns. Optimized for rapid POC development.
dependencies: fastapi>=0.100.0, uvicorn>=0.23.0, duckdb>=0.9.0, protobuf>=4.0, grpcio-tools>=1.50.0
---

# FastAPI Backend Skill

## Overview

This skill implements production-ready backend APIs using:
- **FastAPI** - Modern Python web framework with automatic OpenAPI docs
- **DuckDB** - Zero-config embedded analytical database
- **Protocol Buffers** - Efficient binary serialization
- **WebSocket** - Real-time bidirectional communication
- **Clean decorators** - `@proto.get/post/put/delete` for automatic protobuf handling

## When to Use This Skill

**Use this skill when:**
- Building CRUD APIs with type-safe binary communication
- Need real-time updates across multiple clients
- Rapid POC development without complex infrastructure
- Single-file deployments are preferred

**Do NOT use when:**
- Need horizontal scaling (DuckDB is single-node)
- Complex transactions spanning multiple services
- Already have established backend patterns

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI App                          │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ @proto.get   │  │ @proto.post  │  │ @app.ws      │   │
│  │ (list/read)  │  │ (create)     │  │ (realtime)   │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                  │           │
│         └────────┬────────┴─────────────────┘           │
│                  ▼                                       │
│         ┌──────────────────┐                            │
│         │  Protobuf Utils  │                            │
│         │  - ProtobufRouter│                            │
│         │  - ProtobufBody  │                            │
│         └────────┬─────────┘                            │
│                  ▼                                       │
│         ┌──────────────────┐                            │
│         │     DuckDB       │                            │
│         │  (todos.db)      │                            │
│         └──────────────────┘                            │
└─────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Project Structure

```
project/
├── main.py              # FastAPI application
├── protobuf_utils.py    # Reusable protobuf helpers
├── protos/
│   ├── domain.proto     # Schema definition
│   ├── domain_pb2.py    # Generated Python code
│   └── domain_pb2.pyi   # Type hints
├── static/
│   └── domain.proto     # Copy for frontend
├── templates/
│   └── index.html       # Initial page template
└── requirements.txt
```

### Step 2: Protobuf Utilities

Create reusable utilities for protobuf handling:

```python
# protobuf_utils.py
from fastapi import Request
from fastapi.responses import Response
from google.protobuf.message import Message
from typing import Type, TypeVar, Callable
from functools import wraps
import inspect

T = TypeVar('T', bound=Message)

class ProtobufResponse(Response):
    """Custom response class for protobuf serialization"""
    media_type = "application/x-protobuf"
    
    def render(self, content) -> bytes:
        if isinstance(content, Message):
            return content.SerializeToString()
        elif isinstance(content, bytes):
            return content
        raise ValueError(f"Expected protobuf Message, got {type(content)}")


class ProtobufBody:
    """Dependency for automatic protobuf body parsing"""
    def __init__(self, message_type: Type[T]):
        self.message_type = message_type

    async def __call__(self, request: Request) -> T:
        body = await request.body()
        msg = self.message_type()
        msg.ParseFromString(body)
        return msg


class ProtobufRouter:
    """Wrapper providing @proto decorators for clean endpoints"""
    def __init__(self, app_or_router):
        self.router = app_or_router

    def _wrap_endpoint(self, func: Callable):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)
                return ProtobufResponse(result) if isinstance(result, Message) else result
            return wrapper
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                return ProtobufResponse(result) if isinstance(result, Message) else result
            return wrapper

    def _make_method(self, name: str):
        def method(path: str, **kwargs):
            kwargs.setdefault("response_class", ProtobufResponse)
            def decorator(func: Callable):
                wrapped = self._wrap_endpoint(func)
                getattr(self.router, name)(path, **kwargs)(wrapped)
                return func
            return decorator
        return method

    def __getattr__(self, name: str):
        if name in ("get", "post", "put", "delete", "patch"):
            return self._make_method(name)
        return getattr(self.router, name)
```

### Step 3: Database Initialization

```python
# main.py
import duckdb
from contextlib import asynccontextmanager
from fastapi import FastAPI

DB_PATH = "app.db"

def init_db():
    conn = duckdb.connect(DB_PATH)
    
    # Create sequence for auto-increment IDs
    conn.execute("CREATE SEQUENCE IF NOT EXISTS item_id_seq")
    
    # Create main table matching protobuf schema
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY DEFAULT nextval('item_id_seq'),
            title VARCHAR NOT NULL,
            description VARCHAR DEFAULT '',
            status VARCHAR DEFAULT 'active',
            priority INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add indexes for common queries
    conn.execute("CREATE INDEX IF NOT EXISTS idx_items_status ON items(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_items_created ON items(created_at)")
    
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)
```

### Step 4: Database Connection Context Manager

```python
@asynccontextmanager
async def get_db():
    conn = duckdb.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()
```

### Step 5: Row-to-Proto Mapper

```python
import protos.domain_pb2 as domain_pb
import time

def row_to_item_proto(row) -> domain_pb.Item:
    """Convert database row to protobuf message"""
    return domain_pb.Item(
        id=row[0],
        title=row[1],
        description=row[2] or '',
        status=row[3] or 'active',
        priority=row[4] or 0,
        created_at=int(row[5].timestamp()) if row[5] else int(time.time()),
        updated_at=int(row[6].timestamp()) if row[6] else int(time.time())
    )
```

### Step 6: Type Aliases for Request Bodies

```python
from typing import Annotated
from fastapi import Depends

# Annotated type aliases for clean endpoint signatures
CreateItemBody = Annotated[
    domain_pb.CreateItemRequest, 
    Depends(ProtobufBody(domain_pb.CreateItemRequest))
]

UpdateItemBody = Annotated[
    domain_pb.UpdateItemRequest, 
    Depends(ProtobufBody(domain_pb.UpdateItemRequest))
]
```

### Step 7: CRUD Endpoints

```python
from protobuf_utils import ProtobufRouter

proto = ProtobufRouter(app)

# LIST all items
@proto.get("/api/items")
async def get_items():
    async with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM items ORDER BY created_at DESC"
        ).fetchall()
    
    item_list = domain_pb.ItemList()
    for row in rows:
        item_list.items.add().CopyFrom(row_to_item_proto(row))
    
    return item_list


# CREATE new item
@proto.post("/api/items")
async def create_item(req: CreateItemBody):
    async with get_db() as conn:
        row = conn.execute(
            "INSERT INTO items (title, description) VALUES (?, ?) RETURNING *",
            [req.title, req.description]
        ).fetchone()
    
    item = row_to_item_proto(row)
    await broadcast_event(domain_pb.CREATED, item=item)
    
    return domain_pb.ApiResponse(success=True, message="Created", item=item)


# READ single item
@proto.get("/api/items/{item_id}")
async def get_item(item_id: int):
    async with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM items WHERE id = ?", [item_id]
        ).fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return row_to_item_proto(row)


# UPDATE item
@proto.put("/api/items/{item_id}")
async def update_item(item_id: int, req: UpdateItemBody):
    async with get_db() as conn:
        conn.execute("""
            UPDATE items 
            SET title = COALESCE(?, title),
                description = COALESCE(?, description),
                status = COALESCE(?, status),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, [req.title or None, req.description or None, req.status or None, item_id])
        
        row = conn.execute("SELECT * FROM items WHERE id = ?", [item_id]).fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item = row_to_item_proto(row)
    await broadcast_event(domain_pb.UPDATED, item=item)
    
    return domain_pb.ApiResponse(success=True, message="Updated", item=item)


# DELETE item
@proto.delete("/api/items/{item_id}")
async def delete_item(item_id: int):
    async with get_db() as conn:
        conn.execute("DELETE FROM items WHERE id = ?", [item_id])
    
    await broadcast_event(domain_pb.DELETED, deleted_id=item_id)
    
    return domain_pb.ApiResponse(success=True, message="Deleted")


# GET statistics
@proto.get("/api/stats")
async def get_stats():
    async with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        active = conn.execute(
            "SELECT COUNT(*) FROM items WHERE status = 'active'"
        ).fetchone()[0]
    
    return domain_pb.ApiResponse(
        success=True,
        stats=domain_pb.ItemStats(total=total, active=active, completed=total-active)
    )
```

### Step 8: WebSocket Connection Manager

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import List

class ConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, event: domain_pb.DomainEvent):
        """Broadcast protobuf event to all connected clients"""
        data = event.SerializeToString()
        for ws in self.connections[:]:  # Copy to avoid mutation during iteration
            try:
                await ws.send_bytes(data)
            except:
                self.connections.remove(ws)

ws_manager = ConnectionManager()
```

### Step 9: Broadcast Helper

```python
async def get_current_stats():
    """Helper to fetch current statistics"""
    async with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        active = conn.execute(
            "SELECT COUNT(*) FROM items WHERE status = 'active'"
        ).fetchone()[0]
    return domain_pb.ItemStats(total=total, active=active, completed=total-active)


async def broadcast_event(event_type: int, item=None, deleted_id=None):
    """Broadcast change event to all WebSocket clients"""
    stats = await get_current_stats()
    event = domain_pb.DomainEvent(type=event_type, stats=stats)
    
    if item:
        event.item.CopyFrom(item)
    if deleted_id:
        event.deleted_id = deleted_id
    
    await ws_manager.broadcast(event)
```

### Step 10: WebSocket Endpoint

```python
@app.websocket("/ws/items")
async def websocket_items(ws: WebSocket):
    """Subscribe to real-time item changes"""
    await ws_manager.connect(ws)
    try:
        while True:
            await ws.receive_bytes()  # Keep alive, ignore client messages
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
```

### Step 11: Static Files & Templates

```python
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/protos", StaticFiles(directory="protos"), name="protos")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    async with get_db() as conn:
        items = conn.execute("SELECT * FROM items ORDER BY created_at DESC").fetchall()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "items": [{"id": i[0], "title": i[1], "status": i[3]} for i in items]
    })
```

### Step 12: Application Entry Point

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

## Decorator Patterns

### Clean Protobuf Endpoints

```python
# Instead of manual serialization:
@app.get("/api/items")
async def get_items():
    items = fetch_items()
    return Response(
        content=items.SerializeToString(),
        media_type="application/x-protobuf"
    )

# Use the decorator pattern:
@proto.get("/api/items")
async def get_items():
    return fetch_items()  # Automatically serialized!
```

### Type-Safe Request Bodies

```python
# Define once:
CreateItemBody = Annotated[
    domain_pb.CreateItemRequest, 
    Depends(ProtobufBody(domain_pb.CreateItemRequest))
]

# Use everywhere with full type hints:
@proto.post("/api/items")
async def create_item(req: CreateItemBody):
    print(req.title)  # IDE knows this is a string!
```

## DuckDB Patterns

### Transactions for Bulk Operations

```python
async def bulk_create(items: List[dict]):
    async with get_db() as conn:
        conn.begin()
        try:
            for item in items:
                conn.execute("INSERT INTO items (title) VALUES (?)", [item['title']])
            conn.commit()
        except:
            conn.rollback()
            raise
```

### Efficient Aggregations

```python
@proto.get("/api/analytics")
async def get_analytics():
    async with get_db() as conn:
        result = conn.execute("""
            SELECT 
                status,
                COUNT(*) as count,
                AVG(priority) as avg_priority
            FROM items
            GROUP BY status
        """).fetchall()
    
    # Return as protobuf...
```

## Validation Checklist

Before deployment:

- [ ] Database initialized with proper sequences
- [ ] All CRUD endpoints use `@proto` decorators
- [ ] Request bodies use `Annotated` type aliases
- [ ] WebSocket broadcasts on all mutations
- [ ] Error handling returns proper HTTP status codes
- [ ] Proto files copied to static directory
- [ ] Indexes created for frequently queried columns
- [ ] Connection manager handles disconnects gracefully

## Requirements

```txt
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
duckdb>=0.9.0
protobuf>=4.0
grpcio-tools>=1.50.0
jinja2>=3.0.0
python-multipart>=0.0.6
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [Protocol Buffers Guide](https://protobuf.dev/)
- Reference implementation: `main.py` and `protobuf_utils.py` in this boilerplate

