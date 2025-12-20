# Development Workflow Guide

A structured, phase-based approach to building applications with this boilerplate. Follow these steps sequentially for optimal results.

---

## Phase 1: Domain Modeling & Data Contracts

**Goal**: Define the data structures that represent your domain before writing any logic.

### 1.1 Define Protobuf Messages

Start in `protos/your_domain.proto`:

```protobuf
syntax = "proto3";
package your_domain;

// 1. Core domain entities (nouns)
message User {
  int32 id = 1;
  string email = 2;
  string name = 3;
  int64 created_at = 4;
}

// 2. Request/Response wrappers
message CreateUserRequest {
  string email = 1;
  string name = 2;
}

// 3. Collection types
message UserList {
  repeated User users = 1;
}

// 4. Event types for real-time updates
enum EventType {
  CREATED = 0;
  UPDATED = 1;
  DELETED = 2;
}

message DomainEvent {
  EventType type = 1;
  User user = 2;
  int32 deleted_id = 3;
}
```

### 1.2 Design Principles

- **Start minimal**: Only add fields you need now. Protobuf allows backward-compatible additions later.
- **Use `int64` for timestamps**: Unix timestamps are universally compatible.
- **Separate concerns**: Request messages ≠ Entity messages ≠ Response messages.
- **Plan for events**: If real-time updates are possible, define event messages early.

### 1.3 Generate Code

```bash
python -m grpc_tools.protoc -I./protos --python_out=./protos --pyi_out=./protos ./protos/your_domain.proto
cp protos/your_domain.proto static/your_domain.proto
```

---

## Phase 2: Database Schema Design

**Goal**: Translate protobuf messages into persistent storage.

### 2.1 Create Database Tables

In `main.py` or a dedicated `db.py`:

```python
def init_db():
    conn = duckdb.connect(DB_PATH)
    
    # Always use sequences for auto-increment IDs
    conn.execute("CREATE SEQUENCE IF NOT EXISTS user_id_seq")
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY DEFAULT nextval('user_id_seq'),
            email VARCHAR NOT NULL UNIQUE,
            name VARCHAR NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add indexes for frequently queried columns
    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    
    conn.close()
```

### 2.2 Design Principles

- **Mirror protobuf structure**: Database columns should align with protobuf fields.
- **Use constraints**: `NOT NULL`, `UNIQUE`, `FOREIGN KEY` where appropriate.
- **Plan for queries**: Add indexes for columns used in `WHERE` clauses.
- **Timestamps**: Always use `TIMESTAMP` type, convert to Unix in the mapping layer.

### 2.3 Create Row-to-Proto Mapper

```python
def row_to_user_proto(row) -> user_pb.User:
    """Single point of conversion between database and protobuf"""
    return user_pb.User(
        id=row[0],
        email=row[1],
        name=row[2],
        created_at=int(row[3].timestamp()) if row[3] else int(time.time())
    )
```

---

## Phase 3: API Architecture Decision

**Goal**: Determine communication patterns before implementing endpoints.

### 3.1 Choose Your Pattern

| Pattern | Use When | Implementation |
|---------|----------|----------------|
| **REST-like (one-way)** | CRUD operations, form submissions | `@proto.get/post/put/delete` |
| **WebSocket (bidirectional)** | Real-time collaboration, live updates | `@app.websocket` + broadcast |
| **Hybrid** | Initial load + live updates | REST for mutations, WebSocket for sync |

### 3.2 Decision Framework

Ask yourself:
1. **Do multiple clients need to see changes instantly?** → Add WebSocket
2. **Is data mostly read or write?** → Read-heavy can cache, write-heavy needs transactions
3. **Is there a natural "room" or "channel"?** → Design connection manager accordingly

### 3.3 Endpoint Organization

```python
# Group related endpoints
# ============================================================
# User Management
# ============================================================
@proto.get("/api/users")
async def list_users(): ...

@proto.post("/api/users")
async def create_user(req: CreateUserBody): ...

@proto.get("/api/users/{user_id}")
async def get_user(user_id: int): ...

# ============================================================
# User Preferences (separate concern)
# ============================================================
@proto.get("/api/users/{user_id}/preferences")
async def get_preferences(user_id: int): ...
```

---

## Phase 4: State Management Architecture

**Goal**: Design state flows before implementing logic.

### 4.1 Identify State Sources

| State Type | Location | Example |
|------------|----------|---------|
| **Persistent** | DuckDB tables | User records, settings |
| **Session** | Server memory | Active WebSocket connections |
| **UI** | XState context | Filter selection, loading states |
| **Derived** | Computed | Statistics, filtered lists |

### 4.2 Server-Side State Considerations

```python
# For stateful servers (WebSocket, sessions)
class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}  # room_id -> connections
    
    async def join(self, room_id: str, ws: WebSocket): ...
    async def leave(self, room_id: str, ws: WebSocket): ...
    async def broadcast(self, room_id: str, event): ...
```

### 4.3 Client-Side State Design

Plan your XState machine states:

```
┌─────────┐     LOAD      ┌─────────┐
│  init   │──────────────▶│ loading │
└─────────┘               └────┬────┘
                               │ onDone
                               ▼
┌─────────┐     ERROR     ┌─────────┐
│  error  │◀──────────────│  idle   │◀───────┐
└─────────┘               └────┬────┘        │
                               │ ACTION      │
                               ▼             │
                          ┌─────────┐        │
                          │ working │────────┘
                          └─────────┘  onDone
```

---

## Phase 5: Backend Implementation

**Goal**: Implement and test API endpoints before touching frontend.

### 5.1 Implementation Order

1. **Database layer**: `init_db()`, row mappers
2. **Read endpoints**: `GET` operations first (easier to test)
3. **Write endpoints**: `POST`, `PUT`, `DELETE`
4. **Real-time layer**: WebSocket connections and broadcasts
5. **Error handling**: HTTPException for expected errors

### 5.2 Create Test Endpoints

Use `curl` or a simple test script:

```bash
# Test GET
curl -s http://localhost:8080/api/users | protoc --decode=user.UserList protos/user.proto

# Test POST (requires binary encoding)
# Create a test script instead
python tests/test_api.py
```

### 5.3 Test Script Template

```python
# tests/test_api.py
import requests
from protos import user_pb2 as user_pb

BASE = "http://localhost:8080"

def test_create_and_list():
    # Create
    req = user_pb.CreateUserRequest(email="test@example.com", name="Test")
    res = requests.post(f"{BASE}/api/users", data=req.SerializeToString(),
                       headers={"Content-Type": "application/x-protobuf"})
    assert res.status_code == 200
    
    # List
    res = requests.get(f"{BASE}/api/users")
    users = user_pb.UserList()
    users.ParseFromString(res.content)
    assert len(users.users) > 0

if __name__ == "__main__":
    test_create_and_list()
    print("✓ All tests passed")
```

---

## Phase 6: Frontend State Machine

**Goal**: Implement XState machine and API communication before UI.

### 6.1 Define the Machine

```javascript
const appMachine = createMachine({
    id: 'app',
    initial: 'loading',
    context: {
        items: [],
        error: null,
        filter: 'all'
    },
    // Root-level events (handled in any state)
    on: {
        WS_EVENT: { actions: 'handleWebSocketEvent' },
        FILTER: { actions: assign({ filter: ({ event }) => event.value }) }
    },
    states: {
        loading: {
            invoke: {
                src: 'loadData',
                onDone: { target: 'idle', actions: 'setData' },
                onError: { target: 'error', actions: 'setError' }
            }
        },
        idle: {
            on: {
                CREATE: 'creating',
                UPDATE: 'updating',
                DELETE: 'deleting'
            }
        },
        creating: { /* invoke createItem */ },
        updating: { /* invoke updateItem */ },
        deleting: { /* invoke deleteItem */ },
        error: {
            on: { RETRY: 'loading' }
        }
    }
});
```

### 6.2 Test Without UI

```javascript
// In browser console or Node.js test
const actor = createActor(appMachine);
actor.subscribe(state => console.log('State:', state.value, state.context));
actor.start();

// Manually send events
actor.send({ type: 'CREATE', title: 'Test item' });
```

### 6.3 WebSocket Integration

```javascript
function connectWebSocket() {
    const ws = new WebSocket(`ws://${location.host}/ws/channel`);
    
    ws.onmessage = async (event) => {
        const buffer = await event.data.arrayBuffer();
        const decoded = decodeProto('DomainEvent', buffer);
        actor.send({ type: 'WS_EVENT', payload: decoded });
    };
    
    ws.onclose = () => setTimeout(connectWebSocket, 1000);
}
```

---

## Phase 7: Minimal Functional UI

**Goal**: Create the simplest UI that proves all features work.

### 7.1 Start with Structure Only

```html
<div id="app">
    <header>
        <h1>App Name</h1>
        <div id="stats"><!-- Stats render here --></div>
    </header>
    
    <main>
        <form id="create-form">
            <input type="text" name="title" required>
            <button type="submit">Create</button>
        </form>
        
        <div id="filters"><!-- Filter buttons --></div>
        <ul id="item-list"><!-- Items render here --></ul>
    </main>
    
    <footer id="status"><!-- Connection status --></footer>
</div>
```

### 7.2 Render Function

```javascript
function render(state) {
    const { items, filter, error } = state.context;
    
    // Filter items
    const filtered = items.filter(item => /* filter logic */);
    
    // Render list
    document.getElementById('item-list').innerHTML = filtered
        .map(item => `<li data-id="${item.id}">${item.title}</li>`)
        .join('');
    
    // Update UI state classes
    document.getElementById('app').className = `state-${state.value}`;
}

actor.subscribe(render);
```

### 7.3 Event Handlers

```javascript
// Form submission
document.getElementById('create-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const title = e.target.title.value.trim();
    if (title) {
        actor.send({ type: 'CREATE', title });
        e.target.reset();
    }
});

// Delegated event handling for dynamic elements
document.getElementById('item-list').addEventListener('click', (e) => {
    const li = e.target.closest('li');
    if (!li) return;
    
    if (e.target.matches('.delete-btn')) {
        actor.send({ type: 'DELETE', id: +li.dataset.id });
    }
});
```

---

## Phase 8: Server-Side Rendering (HTMX)

**Goal**: Leverage SSR for initial load and progressively enhance with JavaScript.

### 8.1 Dual-Purpose Templates

Create templates that work for both SSR and client-side rendering:

```html
<!-- templates/partials/item.html -->
<li class="item {{ 'completed' if item.completed else '' }}" data-id="{{ item.id }}">
    <span class="item-title">{{ item.title }}</span>
    <button class="delete-btn" aria-label="Delete">×</button>
</li>
```

### 8.2 Template as JavaScript Function

```javascript
// Mirror the template logic in JS for client-side updates
function renderItem(item) {
    return `
        <li class="item ${item.completed ? 'completed' : ''}" data-id="${item.id}">
            <span class="item-title">${escapeHtml(item.title)}</span>
            <button class="delete-btn" aria-label="Delete">×</button>
        </li>
    `;
}
```

### 8.3 HTMX for Progressive Enhancement

```html
<!-- Initial load uses SSR, subsequent updates use JS -->
<div id="system-info" 
     hx-get="/system-info" 
     hx-trigger="load, every 30s"
     hx-swap="innerHTML">
    Loading...
</div>
```

---

## Phase 9: Styling & Visual Design

**Goal**: Apply styles only after functionality is complete.

### 9.1 CSS Custom Properties

```css
:root {
    /* Colors */
    --color-primary: #667eea;
    --color-primary-dark: #5568d3;
    --color-danger: #ff6b6b;
    --color-text: #333;
    --color-text-muted: #888;
    --color-bg: #f5f5f5;
    --color-surface: #fff;
    --color-border: #e0e0e0;
    
    /* Spacing */
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 16px;
    --space-lg: 24px;
    --space-xl: 32px;
    
    /* Typography */
    --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --font-size-sm: 14px;
    --font-size-md: 16px;
    --font-size-lg: 20px;
    
    /* Transitions */
    --transition-fast: 150ms ease;
    --transition-normal: 200ms ease;
}
```

### 9.2 Hierarchical & Nested Styles

```css
/* Component-scoped styles using nesting */
.todo-item {
    display: flex;
    align-items: center;
    padding: var(--space-md);
    border-bottom: 1px solid var(--color-border);
    transition: background var(--transition-fast);
    
    &:hover {
        background: var(--color-bg);
    }
    
    &.completed {
        .todo-title {
            text-decoration: line-through;
            opacity: 0.5;
        }
    }
    
    .todo-title {
        flex: 1;
        font-size: var(--font-size-md);
    }
    
    .delete-btn {
        /* ... */
    }
}
```

### 9.3 State-Based Styling

```css
/* Loading states */
.state-loading,
.state-creating,
.state-updating,
.state-deleting {
    pointer-events: none;
    
    &::after {
        content: '';
        position: fixed;
        inset: 0;
        background: rgba(255, 255, 255, 0.7);
        z-index: 100;
    }
}

/* Error states */
.state-error #error-banner {
    display: flex;
}
```

---

## Phase 10: Code Review & Cleanup

**Goal**: Remove dead code, simplify implementations.

### 10.1 Checklist

- [ ] **Unused imports**: Remove any unused Python/JS imports
- [ ] **Dead code paths**: Delete unreachable code, commented-out blocks
- [ ] **Duplicate logic**: Extract into shared functions
- [ ] **Over-engineering**: Remove abstractions that aren't used twice
- [ ] **Magic numbers**: Replace with named constants
- [ ] **Error handling**: Consistent patterns throughout

### 10.2 Simplification Questions

Ask yourself:
1. Can I achieve the same with fewer files?
2. Are there libraries I'm not fully utilizing?
3. Is there conditional logic that could be data-driven?
4. Can any function be replaced with a one-liner?

### 10.3 Line Count Target

Aim for approximately:
- `main.py`: ~150-200 lines
- `app.js`: ~150-200 lines
- `styles.css`: ~150-200 lines
- Total: **~500 lines for a full CRUD app**

---

## Phase 11: Performance Optimization

**Goal**: Optimize only after functionality is complete and correct.

### 11.1 Measurement First

```javascript
// Add timing to API calls
console.time('loadData');
const data = await api.getItems();
console.timeEnd('loadData');
```

### 11.2 Common Optimizations

| Area | Optimization |
|------|--------------|
| **Database** | Add indexes, use prepared statements |
| **API** | Enable gzip/brotli compression |
| **Frontend** | Debounce rapid events, virtual scrolling for long lists |
| **Rendering** | DOM diffing, avoid innerHTML for single updates |
| **Network** | Combine requests, use WebSocket instead of polling |

### 11.3 DuckDB Optimizations

```python
# Use transactions for bulk operations
with conn.begin():
    for item in items:
        conn.execute("INSERT INTO items VALUES (...)")

# Use COPY for large imports
conn.execute("COPY items FROM 'data.csv' (FORMAT CSV, HEADER)")
```

---

## Phase 12: PWA Configuration

**Goal**: Make the application installable and offline-capable.

### 12.1 Web App Manifest

Create `static/manifest.json`:

```json
{
    "name": "Your App Name",
    "short_name": "AppName",
    "description": "Brief description of your app",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#667eea",
    "icons": [
        {
            "src": "/static/icons/icon-192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "/static/icons/icon-512.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ]
}
```

### 12.2 HTML Head Updates

```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#667eea">
    <meta name="description" content="Your app description">
    
    <!-- PWA -->
    <link rel="manifest" href="/static/manifest.json">
    <link rel="apple-touch-icon" href="/static/icons/icon-192.png">
    
    <!-- Favicon -->
    <link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
    <link rel="icon" type="image/png" sizes="32x32" href="/static/favicon-32.png">
    
    <title>Your App</title>
</head>
```

### 12.3 Service Worker (Optional)

For offline support, add `static/sw.js`:

```javascript
const CACHE = 'v1';
const ASSETS = ['/', '/static/app.js', '/static/styles.css'];

self.addEventListener('install', (e) => {
    e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
});

self.addEventListener('fetch', (e) => {
    e.respondWith(
        caches.match(e.request).then(r => r || fetch(e.request))
    );
});
```

---

## Phase 13: Documentation & Handoff

**Goal**: Document decisions, not just code.

### 13.1 Update README

- **What** the app does (1-2 sentences)
- **How** to run it (copy-paste commands)
- **Why** key decisions were made

### 13.2 Code Comments

```python
# Explain WHY, not WHAT
# Good: "Using DuckDB sequence because SQLite-style rowid isn't reliable for references"
# Bad: "Create a sequence for IDs"
```

### 13.3 Architecture Decision Records

For significant decisions, document:
- **Context**: What problem were you solving?
- **Decision**: What did you choose?
- **Consequences**: What trade-offs did you accept?

---

## Quick Reference: File Responsibilities

| File | Purpose | Lines Target |
|------|---------|--------------|
| `protos/*.proto` | Data contracts, API schema | 30-60 |
| `main.py` | HTTP endpoints, DB queries, WebSocket | 150-200 |
| `protobuf_utils.py` | Serialization helpers (reusable) | 50-80 |
| `static/app.js` | State machine, API client, rendering | 150-200 |
| `static/styles.css` | Visual styling only | 150-200 |
| `templates/index.html` | Initial HTML structure | 40-60 |
| `templates/partials/*.html` | Reusable fragments | 10-20 each |

---

## Anti-Patterns to Avoid

1. **Premature optimization**: Get it working first, then profile
2. **Inline styles**: Always use CSS classes
3. **Business logic in templates**: Templates render, they don't decide
4. **Monolithic state**: Separate concerns into sub-contexts if needed
5. **Ignoring protobuf advantages**: Don't convert to JSON and back
6. **Over-abstraction**: If it's only used once, inline it
7. **Copy-paste programming**: If you paste, extract into a function

---

## Development Checklist

Before considering a feature complete:

- [ ] Protobuf messages defined and generated
- [ ] Database schema matches protobuf structure
- [ ] API endpoints tested with curl/script
- [ ] XState machine handles all states and events
- [ ] WebSocket broadcasts changes (if applicable)
- [ ] UI renders all states correctly
- [ ] Error states are handled gracefully
- [ ] No console errors or warnings
- [ ] Code is under line count targets
- [ ] No dead code or unused imports

