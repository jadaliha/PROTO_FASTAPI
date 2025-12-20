from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import duckdb
from typing import Optional, Annotated
import time

# Import protobuf utilities
from protobuf_utils import ProtobufResponse, ProtobufBody, ProtobufRouter

# Import generated protobuf classes
import protos.todo_pb2 as todo_pb

# Annotated type aliases for protobuf request bodies
CreateTodoBody = Annotated[todo_pb.CreateTodoRequest, Depends(ProtobufBody(todo_pb.CreateTodoRequest))]
UpdateTodoBody = Annotated[todo_pb.UpdateTodoRequest, Depends(ProtobufBody(todo_pb.UpdateTodoRequest))]

# Database initialization
DB_PATH = "todos.db"

def init_db():
    conn = duckdb.connect(DB_PATH)
    conn.execute("CREATE SEQUENCE IF NOT EXISTS todo_id_seq")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY DEFAULT nextval('todo_id_seq'),
            title VARCHAR NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/protos", StaticFiles(directory="protos"), name="protos")
templates = Jinja2Templates(directory="templates")

# Initialize Protobuf Router
proto = ProtobufRouter(app)

@asynccontextmanager
async def get_db():
    conn = duckdb.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def row_to_todo_proto(row):
    """Convert database row to protobuf Todo message"""
    todo = todo_pb.Todo()
    todo.id = row[0]
    todo.title = row[1]
    todo.completed = row[2]
    todo.created_at = int(row[3].timestamp()) if row[3] else int(time.time())
    return todo

# HTML endpoints (for initial page load)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    async with get_db() as conn:
        todos = conn.execute("SELECT * FROM todos ORDER BY created_at DESC").fetchall()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "todos": [{"id": t[0], "title": t[1], "completed": t[2], "created_at": t[3]} for t in todos]
    })

# Protobuf API endpoints using the simplified @proto decorators
@proto.get("/api/todos")
async def get_todos_proto():
    """Get all todos as protobuf"""
    async with get_db() as conn:
        rows = conn.execute("SELECT * FROM todos ORDER BY created_at DESC").fetchall()
    
    todo_list = todo_pb.TodoList()
    for row in rows:
        todo_list.todos.add().CopyFrom(row_to_todo_proto(row))
    
    return todo_list

@proto.post("/api/todos")
async def create_todo_proto(req: CreateTodoBody):
    """Create todo via protobuf - request automatically parsed!"""
    async with get_db() as conn:
        row = conn.execute("INSERT INTO todos (title) VALUES (?) RETURNING *", [req.title]).fetchone()
    
    return todo_pb.ApiResponse(
        success=True, 
        message="Todo created", 
        todo=row_to_todo_proto(row)
    )

@proto.put("/api/todos/{todo_id}/toggle")
async def toggle_todo_proto(todo_id: int, req: UpdateTodoBody):
    """Toggle todo completion via protobuf - request automatically parsed!"""
    async with get_db() as conn:
        conn.execute("UPDATE todos SET completed = ? WHERE id = ?", [req.completed, todo_id])
        row = conn.execute("SELECT * FROM todos WHERE id = ?", [todo_id]).fetchone()
    
    if not row: raise HTTPException(status_code=404)
    
    return todo_pb.ApiResponse(
        success=True, 
        message="Todo updated", 
        todo=row_to_todo_proto(row)
    )

@proto.delete("/api/todos/{todo_id}")
async def delete_todo_proto(todo_id: int):
    """Delete todo via protobuf"""
    async with get_db() as conn:
        conn.execute("DELETE FROM todos WHERE id = ?", [todo_id])
    
    return todo_pb.ApiResponse(success=True, message="Todo deleted")

@proto.get("/api/stats")
async def get_stats_proto():
    """Get statistics via protobuf"""
    async with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
        completed = conn.execute("SELECT COUNT(*) FROM todos WHERE completed = TRUE").fetchone()[0]
    
    return todo_pb.ApiResponse(
        success=True,
        stats=todo_pb.TodoStats(total=total, completed=completed, active=total-completed)
    )

# Legacy HTMX endpoint (optional fallback)
@app.post("/todos", response_class=HTMLResponse)
async def create_todo(request: Request, title: str = Form(...)):
    async with get_db() as conn:
        conn.execute("INSERT INTO todos (title) VALUES (?)", [title])
        todos = conn.execute("SELECT * FROM todos ORDER BY created_at DESC").fetchall()
    return templates.TemplateResponse("partials/todo_list.html", {
        "request": request,
        "todos": [{"id": t[0], "title": t[1], "completed": t[2], "created_at": t[3]} for t in todos]
    })

@app.get("/system-info", response_class=HTMLResponse)
async def system_info(request: Request):
    async with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
    return templates.TemplateResponse("partials/system_info.html", {
        "request": request,
        "todo_count": count,
        "time": time.strftime("%H:%M:%S")
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)