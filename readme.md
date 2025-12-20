# FastAPI + Protobuf + XState5 Todo App

A minimalist, future-proof todo application with efficient binary communication using Protocol Buffers.

## Tech Stack

- **Backend**: FastAPI
- **Database**: DuckDB (local file-based)
- **API Protocol**: Protocol Buffers (Protobuf)
- **Frontend**: HTML + Vanilla JavaScript + CSS
- **Server-side rendering**: Jinja2 (initial load only)
- **State management**: XState5
- **Communication**: Binary protobuf over HTTP

## Why Protobuf?

✅ **Type-safe**: Schema-defined messages prevent errors
✅ **Efficient**: 3-10x smaller payload than JSON
✅ **Future-proof**: Easy to add fields without breaking compatibility
✅ **Language-agnostic**: Same schema for Python backend & JS frontend
✅ **AI-friendly**: Clear contracts make code generation easier

## Project Structure

```
.
├── main.py                    # FastAPI backend with protobuf endpoints
├── protobuf_utils.py          # Custom serialization layer
├── requirements.txt           # Python dependencies
├── setup.sh                   # Setup script
├── todos.db                   # DuckDB database (auto-created)
├── protos/
│   ├── todo.proto            # Protobuf schema definition
│   └── todo_pb2.py           # Generated Python code
├── templates/
│   ├── index.html            # Main page
│   └── partials/             # Optional HTMX partials
│       ├── todo_list.html
│       ├── todo_item.html
│       └── stats.html
└── static/
    ├── todo.proto            # Proto file for frontend
    ├── app.js                # XState5 + Protobuf client
    └── styles.css            # Styling
```

## Setup

1. Run the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

Or manually:
```bash
# Install dependencies
pip install -r requirements.txt

# Generate protobuf Python code
python -m grpc_tools.protoc -I./protos --python_out=./protos ./protos/todo.proto

# Copy proto for frontend
cp protos/todo.proto static/todo.proto
```

2. Run the application:
```bash
python main.py
```

3. Open browser at `http://localhost:8080`

## Elegant Protobuf Integration

We've created a clean, FastAPI-idiomatic way to handle protobuf:

### Custom Response Class
```python
@app.get("/api/todos", response_class=ProtobufResponse)
async def get_todos():
    todo_list = todo_pb.TodoList()
    # ... populate todo_list
    return todo_list  # Automatically serialized!
```

### Dependency Injection for Request Parsing
```python
@app.post("/api/todos", response_class=ProtobufResponse)
async def create_todo(req: CreateTodoRequest = Depends(ProtobufBody(CreateTodoRequest))):
    # req is already parsed and type-safe!
    print(req.title)  # Direct access
    return response
```

**Benefits:**
- ✅ No manual `SerializeToString()` or `ParseFromString()` calls
- ✅ Type hints work properly in IDEs
- ✅ FastAPI handles serialization layer automatically
- ✅ Follows FastAPI's dependency injection pattern
- ✅ Clean, readable endpoint code

## API Endpoints

### Protobuf Endpoints (Primary)
- `GET /api/todos` - Get all todos (returns TodoList protobuf)
- `POST /api/todos` - Create todo (accepts CreateTodoRequest)
- `PUT /api/todos/{id}/toggle` - Toggle completion (accepts UpdateTodoRequest)
- `DELETE /api/todos/{id}` - Delete todo
- `GET /api/stats` - Get statistics (returns TodoStats)

### HTML Endpoints (Fallback)
- `GET /` - Main page
- `POST /todos` - Create todo (HTMX fallback)

## Protobuf Schema

```protobuf
message Todo {
  int32 id = 1;
  string title = 2;
  bool completed = 3;
  int64 created_at = 4;
}

message CreateTodoRequest {
  string title = 1;
}

message UpdateTodoRequest {
  int32 id = 1;
  bool completed = 2;
}

message TodoStats {
  int32 total = 1;
  int32 active = 2;
  int32 completed = 3;
}
```

## How It Works

1. **Frontend** uses protobuf.js to encode/decode messages
2. **XState5** manages application state and API calls
3. **FastAPI** receives binary protobuf, processes, and responds
4. **DuckDB** stores data efficiently in a single file
5. **Type safety** is enforced by the protobuf schema

## Benefits Over JSON

| Aspect        | JSON             | Protobuf            |
| ------------- | ---------------- | ------------------- |
| Payload size  | ~200 bytes       | ~60 bytes           |
| Parsing speed | Baseline         | 2-3x faster         |
| Type safety   | None             | Full                |
| Validation    | Manual           | Automatic           |
| Versioning    | Breaking changes | Backward compatible |

## Extending the App

### Add a new field to Todo
```protobuf
message Todo {
  int32 id = 1;
  string title = 2;
  bool completed = 3;
  int64 created_at = 4;
  string priority = 5;  // NEW: Add without breaking existing clients
}
```

Then regenerate:
```bash
python -m grpc_tools.protoc -I./protos --python_out=./protos ./protos/todo.proto
```

### Add filtering/sorting
- Extend XState machine with filter states
- Add query parameters to `/api/todos`
- No schema changes needed!

### Move XState to Web Worker
- Create `worker.js` with XState machine
- Communicate via postMessage
- Keep UI thread free for rendering

## Why This Stack is AI-Friendly

1. **Clear contracts**: Protobuf schema documents the API
2. **Type safety**: Prevents common bugs
3. **Minimal code**: ~300 lines total
4. **Separation of concerns**: 
   - `todo.proto` = API contract
   - `main.py` = Backend logic
   - `app.js` = Frontend state
   - `styles.css` = Presentation
5. **No build tools**: Everything is straightforward
6. **Future-proof**: Easy to add features without breaking changes

## Performance Notes

- **Protobuf payloads**: 60-70% smaller than JSON
- **DuckDB**: Single-file, zero-config, fast queries
- **XState5**: Predictable state transitions
- **No bundler**: Instant browser refresh during development

## Next Steps

- Add authentication (JWT in protobuf headers)
- Add real-time sync (WebSocket + protobuf streaming)
- Add offline support (IndexedDB + sync queue)
- Add undo/redo (XState history states)
- Move to Web Worker for heavy operations