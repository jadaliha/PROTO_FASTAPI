# FastAPI + Protobuf + XState5 Boilerplate Skill

A reusable skill for rapidly building POCs with type-safe binary communication, efficient state management, and minimal code complexity.

## 🎯 When to Use This Boilerplate

**Perfect for:**
- CRUD applications with real-time updates
- POCs requiring type-safe frontend-backend communication
- Applications that need efficient binary protocols
- Projects where AI-assisted development is important
- Rapid prototyping with production-ready patterns

**Not ideal for:**
- Simple static sites (overkill)
- Complex enterprise systems (needs more structure)
- Mobile-first apps (web-optimized)

## 🏗️ Architecture Overview

```
┌─────────────────┐    protobuf     ┌─────────────────┐
│   XState5       │◄──────────────► │   FastAPI       │
│   (Frontend)    │                 │   (Backend)     │
└─────────────────┘                 └─────────────────┘
         │                                   │
         │                                   ▼
         │                          ┌─────────────────┐
         │                          │   DuckDB        │
         │                          │   (Database)    │
         │                          └─────────────────┘
         │
         ▼
┌─────────────────┐
│   HTML/CSS      │
│   (Presentation)│
└─────────────────┘
```

### Key Components

1. **Protobuf Schema** (`protos/*.proto`) - Single source of truth for data contracts
2. **FastAPI Backend** (`main.py`) - Type-safe endpoints with automatic serialization
3. **XState5 Frontend** (`static/app.js`) - Predictable state management
4. **Protobuf Utils** (`protobuf_utils.py`) - Reusable serialization layer
5. **DuckDB Database** - Zero-config, file-based storage

## 🚀 Quick Start Prompts

### 1. Initial Setup
```bash
# Use this prompt to create a new POC from scratch
Create a [DOMAIN] management app using the FastAPI + Protobuf + XState5 boilerplate pattern.

Domain: [Your specific domain, e.g., "task", "note", "contact"]
Key entities: [List main entities, e.g., "tasks with due dates and priorities"]
Features: [CRUD + any special features, e.g., "real-time collaboration, filtering"]

Follow the exact file structure and patterns from the boilerplate.
```

### 2. Domain Modeling
```bash
# Define your protobuf schema
Create a protobuf schema for [DOMAIN] with these messages:
- [Entity] (main entity with id, name, timestamps)
- [Entity]List (collection)
- Create[Entity]Request (creation payload)
- Update[Entity]Request (updates)
- [Entity]Stats (statistics)
- [Entity]Event (real-time events)

Use the same patterns as todo.proto but adapted for [DOMAIN].
```

### 3. Backend Implementation
```bash
# Generate the FastAPI endpoints
Implement the FastAPI backend for [DOMAIN] with:
- Database table matching protobuf schema
- CRUD endpoints using @proto decorators
- WebSocket support for real-time updates
- Proper error handling and validation

Follow the exact patterns from main.py, just replace "todo" with "[domain]".
```

### 4. Frontend State Machine
```bash
# Create the XState5 frontend
Implement the XState5 frontend for [DOMAIN] with:
- State machine with loading, idle, adding, updating, deleting states
- WebSocket integration for real-time updates
- API client using protobuf encoding/decoding
- Clean, minimal UI following the todo app pattern

Use the same structure as app.js, adapted for [DOMAIN].
```

## 📁 File Modification Patterns

### 1. Protobuf Schema (`protos/[domain].proto`)

**Replace pattern:**
```protobuf
// Change package name
package todo; → package [domain];

// Rename messages
message Todo → message [Entity];
message TodoList → message [Entity]List;
message CreateTodoRequest → message Create[Entity]Request;
// etc.

// Update fields based on your domain
message Todo {
  int32 id = 1;
  string title = 2;           // → string name = 2;
  bool completed = 3;          // → string status = 3;
  int64 created_at = 4;
  // Add domain-specific fields
  // string priority = 5;
}
```

### 2. Backend (`main.py`)

**Find and replace patterns:**
```python
# Import changes
import protos.todo_pb2 as todo_pb → import protos.[domain]_pb2 as [domain]_pb

# Type aliases
CreateTodoBody → Create[Entity]Body
UpdateTodoBody → Update[Entity]Body

# Database changes
todos table → [entities] table
todo_id_seq → [entity]_id_seq

# Function names
row_to_todo_proto → row_to_[entity]_proto
get_todos_proto → get_[entities]_proto
create_todo_proto → create_[entity]_proto
# etc.

# Endpoint paths
/api/todos → /api/[entities]
/ws/todos → /ws/[entities]
```

### 3. Frontend (`static/app.js`)

**Find and replace patterns:**
```javascript
// API calls
getTodos → get[Entities]
createTodo → create[Entity]
toggleTodo → update[Entity]  // or specific action
deleteTodo → delete[Entity]

// State machine context
todos → [entities]
todoMachine → [entity]Machine

// WebSocket handling
WS_CREATED, WS_UPDATED, WS_DELETED → keep same pattern
/ws/todos → /ws/[entities]

// Proto type names
'Todo' → '[Entity]'
'TodoList' → '[Entity]List'
// etc.
```

## 🎨 UI Customization Patterns

### 1. CSS Custom Properties (`static/styles.css`)

**Update brand colors:**
```css
:root {
    --color-primary: #667eea;        /* Change to brand color */
    --color-primary-dark: #5568d3;   /* Darker variant */
    --color-danger: #ff6b6b;          /* Error/delete color */
    /* Add more brand colors as needed */
}
```

### 2. Component Styling

**Adapt component classes:**
```css
.todo-item → .[entity]-item
.todo-title → .[entity]-title
.delete-btn → .delete-btn  /* Keep consistent */
```

### 3. Layout Adjustments

**Modify layout in `templates/index.html`:**
```html
<!-- Update headers and labels -->
<h1>Todo App</h1> → <h1>[Domain] App</h1>
<placeholder for="new todo"> → <placeholder for="new [entity]">
```

## 🔧 Common Customization Tasks

### 1. Adding New Fields to Entities

**Step 1: Update protobuf**
```protobuf
message [Entity] {
  // existing fields...
  string new_field = 5;  // Add new field with next number
}
```

**Step 2: Update database**
```python
# Add column to table
conn.execute("""
    ALTER TABLE [entities] 
    ADD COLUMN new_field VARCHAR DEFAULT ''
""")
```

**Step 3: Update frontend**
```javascript
// Add to render function
<li class="[entity]-item" data-id="${t.id}">
    <!-- existing fields -->
    <span class="new-field">${escapeHtml(t.new_field)}</span>
</li>
```

### 2. Adding New Actions

**Step 1: Add to protobuf**
```protobuf
enum ActionType {
  TOGGLE = 0;
  ARCHIVE = 1;  // New action
}

message Update[Entity]Request {
  int32 id = 1;
  ActionType action = 2;  // Replace boolean with enum
}
```

**Step 2: Add endpoint**
```python
@proto.put("/api/[entities]/{id}/archive")
async def archive_[entity]([entity]_id: int):
    # Implementation
```

**Step 3: Add to state machine**
```javascript
// Add new state or action
ARCHIVE: 'archiving',
// Add archived state with invoke
```

### 3. Adding Filtering/Search

**Step 1: Update protobuf**
```protobuf
message Get[Entities]Request {
  string filter = 1;      // 'all', 'active', 'completed'
  string search = 2;      // Text search
}
```

**Step 2: Update backend**
```python
@proto.get("/api/[entities]")
async def get_[entities]_proto(req: Get[Entities]Body):
    # Add WHERE clauses for filter/search
```

**Step 3: Update frontend**
```javascript
// Add search input and filter controls
// Update API call to include parameters
```

## 🧪 Testing Patterns

### 1. Backend Testing

**Create `tests/test_api.py`:**
```python
import requests
from protos import [domain]_pb2 as [domain]_pb

BASE = "http://localhost:8080"

def test_crud():
    # Create
    req = [domain]_pb.Create[Entity]Request(name="Test")
    res = requests.post(f"{BASE}/api/[entities]", 
                        data=req.SerializeToString(),
                        headers={"Content-Type": "application/x-protobuf"})
    assert res.status_code == 200
    
    # List
    res = requests.get(f"{BASE}/api/[entities]")
    entities = [domain]_pb.[Entity]List()
    entities.ParseFromString(res.content)
    assert len(entities.[entities]) > 0
```

### 2. Frontend Testing

**Test in browser console:**
```javascript
// Test state machine
const actor = createActor([entity]Machine);
actor.subscribe(state => console.log(state));
actor.start();

// Test API calls
api.get[Entities]().then(console.log);
api.create[Entity]("Test").then(console.log);
```

## 📊 Performance Optimization Patterns

### 1. Database Indexing
```python
# Add indexes for frequently queried columns
conn.execute("CREATE INDEX IF NOT EXISTS idx_[entities]_status ON [entities](status)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_[entities]_created ON [entities](created_at)")
```

### 2. Frontend Optimization
```javascript
// Debounce rapid events
const debounce = (fn, delay) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
};

// Virtual scrolling for long lists
// Implement in render() function
```

### 3. Caching Patterns
```python
# Simple in-memory cache
_cache = {}

@app.get("/api/[entities]")
async def get_[entities]():
    if "entities" in _cache:
        return _cache["entities"]
    # Fetch and cache
```

## 🔄 Migration Patterns

### 1. From JSON to Protobuf
```python
# Old JSON endpoint
@app.get("/api/[entities]/json")
async def get_[entities]_json():
    # Return JSON

# New protobuf endpoint
@proto.get("/api/[entities]")
async def get_[entities]_proto():
    # Return protobuf
```

### 2. Adding WebSocket Later
```python
# Start with REST endpoints
# Add WebSocket support following the pattern:
@app.websocket("/ws/[entities]")
async def websocket_[entities](ws: WebSocket):
    # Implementation
```

## 🚀 Deployment Patterns

### 1. Single File Deployment
```bash
# All dependencies in requirements.txt
pip install -r requirements.txt
python main.py
```

### 2. Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python", "main.py"]
```

### 3. Production Considerations
- Add Gunicorn behind Nginx
- Use PostgreSQL instead of DuckDB
- Add authentication middleware
- Enable HTTPS/WSS

## 🎯 POC Success Checklist

Before considering your POC complete:

- [ ] **Protobuf schema** defined and generated
- [ ] **Database schema** matches protobuf structure  
- [ ] **CRUD endpoints** working with protobuf
- [ ] **WebSocket** broadcasting changes
- [ ] **XState machine** handling all states
- [ ] **UI rendering** all states correctly
- [ ] **Error handling** for network failures
- [ ] **Type safety** throughout the stack
- [ ] **Real-time updates** working across tabs
- [ ] **Clean code** under line count targets
- [ ] **No console errors** in browser

## 📚 Reference Documentation

- **Protobuf Guide**: `PROTOBUF_GUIDE.md` - Deep dive into protobuf integration
- **Development Workflow**: `DEVELOPMENT_WORKFLOW.md` - Step-by-step process
- **Main README**: `readme.md` - Overview and setup instructions

## 🤖 AI Assistant Prompts

Use these prompts with AI coding assistants:

### For Code Generation
```bash
Generate [COMPONENT] for [DOMAIN] following the FastAPI + Protobuf + XState5 pattern.
Use the exact same structure as the todo boilerplate.
Ensure type safety and follow the established naming conventions.
```

### For Debugging
```bash
Debug the [COMPONENT] issue in my [DOMAIN] app.
The problem is [DESCRIPTION].
Check for common issues: protobuf serialization, state machine transitions, WebSocket connections.
```

### For Refactoring
```bash
Refactor the [COMPONENT] to be more efficient while maintaining the protobuf contract.
Focus on [PERFORMANCE_GOAL] without breaking the existing API.
```

## 🎨 Customization Examples

### 1. Task Management App
- Add `due_date`, `priority`, `assignee` fields
- Implement filtering by status and assignee
- Add calendar view

### 2. Note Taking App  
- Add `content`, `tags`, `folder` fields
- Implement search and tag filtering
- Add markdown support

### 3. Contact Management
- Add `email`, `phone`, `company` fields
- Implement search by name or company
- Add import/export functionality

### 4. Inventory Management
- Add `quantity`, `price`, `category` fields
- Implement low-stock alerts
- Add reporting dashboard

## 🔍 Troubleshooting Guide

### Common Issues and Solutions

1. **Protobuf parsing errors**
   - Check that proto files are copied to static/
   - Verify field numbers match between frontend/backend
   - Ensure proper content-type headers

2. **WebSocket not connecting**
   - Check protocol (ws vs wss)
   - Verify endpoint path matches
   - Check for CORS issues

3. **State machine stuck**
   - Check event names match exactly
   - Verify all transitions are defined
   - Add error state for debugging

4. **Database errors**
   - Ensure DuckDB file permissions
   - Check SQL syntax
   - Verify table schema matches protobuf

## 📈 Scaling Considerations

When moving from POC to production:

1. **Database**: DuckDB → PostgreSQL
2. **Authentication**: Add JWT middleware
3. **File Storage**: Local → S3/blob storage
4. **Caching**: Add Redis layer
5. **Monitoring**: Add logging and metrics
6. **Testing**: Add comprehensive test suite

## 🎯 Final Tips

1. **Start minimal**: Add features only when needed
2. **Maintain patterns**: Follow established conventions
3. **Test early**: Verify protobuf contracts work
4. **Document decisions**: Keep README updated
5. **Iterate quickly**: Use the boilerplate for fast feedback

This skill provides a solid foundation for building type-safe, efficient web applications with minimal complexity. Perfect for POCs that need to demonstrate real value quickly while maintaining production-quality patterns.