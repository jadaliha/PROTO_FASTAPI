# Complete Todo App Creation Prompt

Create a full-stack todo list application with the following exact specifications:

## Tech Stack Requirements
- **Backend**: FastAPI with Python
- **Database**: DuckDB with local file storage
- **API Protocol**: Protocol Buffers (protobuf) for all API communication
- **Frontend State Management**: XState5 for managing application state
- **Frontend**: Vanilla JavaScript, HTML, CSS (no build tools)
- **Server-Side Rendering**: Jinja2 templates for initial page load
- **Optional Enhancement**: HTMX for fallback HTML endpoints

## Architecture Constraints
1. **Minimize lines of code** - prioritize readability and AI-debuggability
2. **No build tools** - everything should work with simple file serving
3. **Clear separation of concerns** - distinct layers for proto schema, backend logic, frontend state, and presentation
4. **Type-safe communication** - protobuf ensures contract between frontend and backend

## Protobuf Integration Requirements
Create a custom FastAPI serialization layer with:
1. **ProtobufResponse class** - Custom response class that auto-serializes protobuf messages
   - Override `render()` method to call `SerializeToString()`
   - Set media_type to "application/x-protobuf"
   
2. **ProtobufBody dependency factory** - FastAPI dependency for auto-parsing requests
   - Create a function that returns an async dependency
   - Automatically parse request body into typed protobuf message
   - Use with `Depends(ProtobufBody(MessageType))`

This allows endpoints to look like:
```python
@app.post("/api/todos", response_class=ProtobufResponse)
async def create_todo(req: CreateTodoRequest = Depends(ProtobufBody(CreateTodoRequest))):
    # req is already parsed!
    return response  # automatically serialized!
```

## Protobuf Schema Design
Define these messages in `todo.proto`:
- `Todo` - id, title, completed, created_at (unix timestamp)
- `TodoList` - repeated todos
- `CreateTodoRequest` - title only
- `UpdateTodoRequest` - id, completed
- `DeleteTodoRequest` - id
- `TodoStats` - total, active, completed counts
- `ApiResponse` - success flag, message, oneof data (todo, todo_list, stats)

## API Endpoints
Create these protobuf endpoints:
- `GET /api/todos` - Returns TodoList
- `POST /api/todos` - Accepts CreateTodoRequest, returns ApiResponse with todo
- `PUT /api/todos/{id}/toggle` - Accepts UpdateTodoRequest, returns ApiResponse with updated todo
- `DELETE /api/todos/{id}` - Returns ApiResponse with success
- `GET /api/stats` - Returns ApiResponse with stats

Plus HTML endpoints:
- `GET /` - Initial page load with Jinja2 template
- `POST /todos` - HTMX fallback for creating todos (optional)

## Database Schema
DuckDB table:
```sql
CREATE TABLE todos (
    id INTEGER PRIMARY KEY,
    title VARCHAR NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## Frontend Architecture
1. **XState5 Machine** with states: loading, idle, adding, updating, deleting, error
2. **Context**: todos array, stats object, filter ('all'|'active'|'completed'), error
3. **Services** (invoked promises): loadTodos, createTodo, updateTodo, deleteTodo
4. **API wrapper**: Functions that encode/decode protobuf using protobuf.js library

Frontend should:
- Load protobuf schema from `/static/todo.proto`
- Initialize XState actor with services
- Subscribe to state changes and render UI
- Handle all CRUD operations through state machine

## File Structure
```
.
├── main.py                    # FastAPI app with protobuf endpoints
├── protobuf_utils.py          # ProtobufResponse + ProtobufBody
├── requirements.txt           # fastapi, uvicorn, jinja2, duckdb, protobuf, grpcio-tools
├── setup.sh                   # Bash script to setup and generate protobuf code
├── protos/
│   ├── todo.proto            # Schema definition
│   └── todo_pb2.py           # Generated (via grpcio-tools)
├── templates/
│   ├── index.html            # Main page
│   └── partials/             # Optional HTMX fragments
│       ├── todo_list.html
│       ├── todo_item.html
│       └── stats.html
└── static/
    ├── todo.proto            # Copy for frontend
    ├── app.js                # XState5 + protobuf client
    └── styles.css            # Clean, modern styling
```

## Setup Script Requirements
Create `setup.sh` that:
1. Creates directory structure
2. Installs Python dependencies
3. Generates Python protobuf code: `python -m grpc_tools.protoc -I./protos --python_out=./protos ./protos/todo.proto`
4. Copies proto file to static directory
5. Prints instructions to run the app

## UI Requirements
- Modern, clean design with good spacing
- Header with app title and live statistics
- Form to add new todos
- Filter tabs (All, Active, Completed)
- Todo list with checkboxes and delete buttons
- Visual feedback during state transitions (opacity, disabled states)
- Responsive layout, max-width 600px centered

## CSS Patterns
- Use CSS custom properties for colors
- Clean, minimal design with subtle shadows
- Smooth transitions for interactions
- State-based classes (state-loading, state-adding, etc.)
- Mobile-friendly with proper touch targets

## Key Implementation Details
1. **DuckDB connection**: Use `duckdb.connect(DB_PATH)` for each request, close after
2. **Timestamp conversion**: Convert DB timestamp to Unix timestamp for protobuf
3. **Error handling**: Try-catch around protobuf parsing, proper HTTP status codes
4. **Frontend loading**: Show loading state initially, handle errors gracefully
5. **Filter logic**: Filter todos client-side based on XState context
6. **Protobuf libraries**: 
   - Backend: `protobuf` and `grpcio-tools` for generation
   - Frontend: `protobufjs` from CDN (https://cdn.jsdelivr.net/npm/protobufjs@7.2.5/dist/protobuf.min.js)
   - XState: from CDN (https://unpkg.com/xstate@5/dist/xstate.iife.js)

## Documentation Requirements
Create comprehensive README.md explaining:
- Why this tech stack (minimal code, AI-friendly, future-proof)
- Setup instructions
- Project structure
- How protobuf integration works
- Benefits of custom serialization layer
- API endpoint documentation
- How to extend the application
- Performance comparison vs JSON

Also create PROTOBUF_GUIDE.md documenting:
- Architecture overview
- ProtobufResponse and ProtobufBody patterns
- Before/after code examples
- Testing examples
- How to add new endpoints

## Success Criteria
The application should:
- ✅ Run with `python main.py` after setup
- ✅ Have ~300 total lines of code across all files
- ✅ Work without any build/compile step (except protobuf generation)
- ✅ Provide full CRUD functionality
- ✅ Show real-time statistics
- ✅ Have smooth UX with state management
- ✅ Use binary protobuf for all API calls
- ✅ Be easily understood and modified by AI coding assistants
- ✅ Have no manual serialization code in endpoints
- ✅ Follow FastAPI best practices with dependency injection

Generate all files needed to run this application.