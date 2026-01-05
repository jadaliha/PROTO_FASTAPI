---
name: Webapp Boilerplate Orchestrator
description: Orchestrate complete web application development using proto_data_structure, XState_machine, and FastAPI_backend skills. Breaks down tasks and coordinates implementation phases.
dependencies: python>=3.11
---

# Webapp Boilerplate Orchestrator Skill

## Overview

This skill serves as the master orchestrator for building complete web applications using the FastAPI + Protobuf + XState5 tech stack. It:
- Breaks down web application requirements into actionable tasks
- Coordinates the use of specialized skills in proper sequence
- Ensures consistent patterns across all components
- Validates the complete implementation

## When to Use This Skill

**Use this skill when:**
- Starting a new web application from scratch
- Need a complete CRUD application with real-time updates
- Want to leverage the full boilerplate stack
- Building POCs that need production-ready patterns

**Do NOT use when:**
- Only need a single component (use specific skill instead)
- Working on an existing application with different patterns
- Simple static sites (overkill)

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend State | XState5 | Predictable state management |
| Frontend UI | Vanilla JS + HTML | Minimal dependencies |
| Communication | Protocol Buffers | Type-safe binary serialization |
| Real-time | WebSocket | Bidirectional updates |
| Backend | FastAPI | Modern Python API framework |
| Database | DuckDB | Zero-config embedded database |

## Development Workflow

### Phase 0: Requirements Gathering

Before invoking any skill, gather:

```markdown
## Project Requirements Template

**Project Name**: [name]
**Domain**: [e.g., task management, inventory, contacts]

### Core Features
- [ ] Feature 1: [description]
- [ ] Feature 2: [description]
- [ ] Feature 3: [description]

### User Types
- [ ] User type 1: [role and permissions]
- [ ] User type 2: [role and permissions]

### Real-time Requirements
- [ ] Multiple users editing simultaneously?
- [ ] Live notifications needed?
- [ ] Collaboration features?

### Data Requirements
- [ ] Main entities: [list]
- [ ] Relationships: [describe]
- [ ] Special fields: [dates, money, files, etc.]
```

### Phase 1: Data Modeling (Use proto_data_structure skill)

**Invoke**: `proto_data_structure` skill

**Input**: Project requirements from Phase 0

**Output Expected**:
- `protos/[domain].proto` - Complete protobuf schema
- Entity relationship documentation
- Field type justifications

**Validation**:
- [ ] All entities have unique IDs
- [ ] Timestamps use int64
- [ ] Request/Response messages defined
- [ ] WebSocket event types included

### Phase 2: Backend Implementation (Use FastAPI_backend skill)

**Invoke**: `FastAPI_backend` skill

**Input**: 
- Protobuf schema from Phase 1
- CRUD requirements

**Output Expected**:
- `main.py` - Complete FastAPI application
- Database initialization with proper schema
- All CRUD endpoints with protobuf handling
- WebSocket endpoint for real-time updates

**Validation**:
- [ ] All endpoints use @proto decorators
- [ ] Database schema matches protobuf
- [ ] WebSocket broadcasts on mutations
- [ ] Error handling returns proper status codes

### Phase 3: Frontend State Machine (Use XState_machine skill)

**Invoke**: `XState_machine` skill

**Input**:
- Protobuf schema from Phase 1
- User journey requirements

**Output Expected**:
- `static/app.js` - XState machine with API client
- WebSocket integration
- Render function for all states

**Validation**:
- [ ] All user actions have state transitions
- [ ] API calls use protobuf encoding
- [ ] WebSocket events update context
- [ ] Error states have recovery paths

### Phase 4: UI Implementation

**No specific skill** - Implement based on patterns in boilerplate

**Create**:
- `templates/index.html` - Main page structure
- `static/styles.css` - Component styling
- `templates/partials/*.html` - Reusable fragments

**Validation**:
- [ ] State-based CSS classes work
- [ ] Forms submit to state machine
- [ ] Real-time updates render correctly

### Phase 5: Integration Testing

**Test Sequence**:

```bash
# 1. Start server
python main.py

# 2. Test API endpoints
curl -s http://localhost:8080/api/items | protoc --decode=domain.ItemList protos/domain.proto

# 3. Test WebSocket (open multiple browser tabs)

# 4. Verify real-time updates work across tabs
```

### Phase 6: Cleanup & Optimization

**Checklist**:
- [ ] Remove unused imports
- [ ] Delete commented-out code
- [ ] Verify line count targets:
  - main.py: ~150-200 lines
  - app.js: ~150-200 lines
  - styles.css: ~150-200 lines
- [ ] No console errors in browser
- [ ] All features working

## File Structure

After complete implementation:

```
project/
├── main.py                  # FastAPI backend (~150-200 lines)
├── protobuf_utils.py        # Reusable proto helpers (~75 lines)
├── protos/
│   ├── domain.proto         # Data contracts (~50 lines)
│   ├── domain_pb2.py        # Generated Python
│   └── domain_pb2.pyi       # Type hints
├── static/
│   ├── app.js               # XState frontend (~150-200 lines)
│   ├── styles.css           # Styling (~150-200 lines)
│   └── domain.proto         # Copy for frontend
├── templates/
│   ├── index.html           # Main page (~50-80 lines)
│   └── partials/
│       ├── item_list.html   # List component
│       └── stats.html       # Stats component
├── requirements.txt
└── README.md
```

## Quick Start Commands

### New Project Setup

```bash
# 1. Create directory structure
mkdir -p myproject/{protos,static,templates/partials}

# 2. Copy boilerplate files
cp boilerplate/protobuf_utils.py myproject/
cp boilerplate/requirements.txt myproject/

# 3. Install dependencies
cd myproject && pip install -r requirements.txt

# 4. Now invoke skills in sequence...
```

### Generate Protobuf Code

```bash
python -m grpc_tools.protoc -I./protos --python_out=./protos --pyi_out=./protos ./protos/domain.proto
cp protos/domain.proto static/domain.proto
```

### Run Development Server

```bash
python main.py
# Open http://localhost:8080
```

## Skill Composition Patterns

### Pattern 1: Sequential Invocation

```
User Request: "Build a task management app"

1. Invoke proto_data_structure:
   - Search for task management patterns
   - Generate task.proto with Task, Project, Label entities

2. Invoke FastAPI_backend:
   - Implement CRUD for all entities
   - Add WebSocket for real-time updates

3. Invoke XState_machine:
   - Create taskMachine with proper states
   - Implement API client and WebSocket handling

4. Complete UI manually following boilerplate patterns
```

### Pattern 2: Iterative Refinement

```
User Request: "Add filtering to existing app"

1. Update proto schema (add filter fields)
2. Invoke FastAPI_backend for query endpoint updates
3. Invoke XState_machine for filter state handling
4. Update UI for filter controls
```

### Pattern 3: Feature Addition

```
User Request: "Add comments to tasks"

1. Invoke proto_data_structure:
   - Add Comment message
   - Add comments field to Task

2. Invoke FastAPI_backend:
   - Add /api/tasks/{id}/comments endpoints
   - Update broadcast events

3. Invoke XState_machine:
   - Add comment-related states
   - Update render for comments
```

## Common Customizations

### Adding New Entity Type

1. **Proto** (proto_data_structure):
   ```protobuf
   message NewEntity {
     int32 id = 1;
     string name = 2;
     int64 created_at = 100;
   }
   ```

2. **Backend** (FastAPI_backend):
   ```python
   @proto.get("/api/newentities")
   async def get_newentities(): ...
   ```

3. **Frontend** (XState_machine):
   ```javascript
   const newEntityMachine = createMachine({...});
   ```

### Adding Authentication

1. **Proto**: Add User, LoginRequest, AuthToken messages
2. **Backend**: Add JWT middleware, login/logout endpoints
3. **Frontend**: Add auth state machine, token storage

### Adding File Uploads

1. **Proto**: Add FileMetadata message
2. **Backend**: Add multipart upload endpoint
3. **Frontend**: Add file input handling in state machine

## Validation Checklist (Final)

Before considering the app complete:

- [ ] **Proto schema** complete with all entities
- [ ] **Backend** implements all CRUD operations
- [ ] **WebSocket** broadcasts all changes
- [ ] **Frontend** handles all states gracefully
- [ ] **Real-time** updates work across browser tabs
- [ ] **Error handling** shows user-friendly messages
- [ ] **Loading states** provide visual feedback
- [ ] **No console errors** in browser
- [ ] **Code is clean** and under line count targets
- [ ] **Documentation** updated with any custom patterns

## Example Projects

Reference implementations for common domains:

| Domain | Key Entities | Special Features |
|--------|--------------|------------------|
| Todo App | Todo, TodoStats | Completion toggle, filters |
| Task Manager | Task, Project, Label | Priorities, due dates, assignments |
| Note Taking | Note, Folder, Tag | Rich text, search, tagging |
| Inventory | Product, Category, Stock | Quantities, alerts, reports |
| Contact Manager | Contact, Company, Tag | Import/export, search |

## Resources

- **proto_data_structure skill**: Entity identification and schema design
- **XState_machine skill**: Frontend state management
- **FastAPI_backend skill**: Backend API implementation
- **Boilerplate code**: Reference implementations in this repository
- [Agent Skills Specification](https://agentskills.io) - Cross-platform skill standards

