# Unified State Machine Todo

**One machine definition. Two runtimes. Native expressions.**

## Quick Start

```bash
./setup.sh
python3 server.py
# Open http://localhost:8000
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  todo.machine.yaml                          │
│                                                             │
│  actions:                                                   │
│    createItem:                                              │
│      update:                                                │
│        items:                                               │
│          py: "[*items, {'id': next_id, ...}]"              │
│          js: "[...items, {id: next_id, ...}]"              │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
   Python: eval(py)                  JS: eval(js)
     (Server)                         (Client)
```

## Native Expression Syntax

Each expression has both Python and JavaScript versions:

```yaml
actions:
  createItem:
    update:
      items:
        py: "[*items, {'id': next_id, 'title': event['title'], 'completed': False}]"
        js: "[...items, {id: next_id, title: event.title, completed: false}]"
  
  toggleItem:
    update:
      items:
        py: "[{**i, 'completed': event['completed']} if i['id'] == event['id'] else i for i in items]"
        js: "items.map(i => i.id === event.id ? {...i, completed: event.completed} : i)"
  
  deleteItem:
    update:
      items:
        py: "[i for i in items if i['id'] != event['id']]"
        js: "items.filter(i => i.id !== event.id)"

guards:
  validTitle:
    condition:
      py: "0 < len(event['title']) < 200"
      js: "event.title.length > 0 && event.title.length < 200"
```

## File Structure

| File | Lines | Purpose |
|------|-------|---------|
| `protos/app.proto` | 61 | Types |
| `machines/todo.machine.yaml` | 64 | Logic (py + js) |
| `runtime.py` | 63 | Python eval |
| `server.py` | 114 | FastAPI + WS |
| `static/runtime.js` | 115 | JS sync |
| `static/app.js` | 102 | UI |
| `static/styles.css` | 176 | Styling |
| `templates/index.html` | 45 | HTML |
| **Total** | **740** | Full app |

## YAML Gotcha

⚠️ Always quote `"on"`:

```yaml
states:
  ready:
    "on":  # NOT 'on' (becomes boolean True)
      CREATE: ...
```
