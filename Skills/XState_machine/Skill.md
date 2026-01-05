---
name: XState State Machine
description: Implement frontend state management using XState5 for user journeys, process flows, API orchestration, and real-time UI updates. Handles all state transitions predictably.
dependencies: xstate>=5.0, protobufjs>=7.0
---

# XState State Machine Skill

## Overview

This skill implements predictable frontend state management using XState5 (v5.x) for:
- User journey and workflow orchestration
- API call lifecycle management (loading, success, error states)
- Real-time WebSocket event handling
- UI state synchronization
- Filter, sort, and view mode management

XState provides explicit state machines that make application behavior predictable and debuggable.

## When to Use This Skill

**Use this skill when:**
- Building interactive web applications with complex state
- Need predictable API call handling with loading/error states
- Implementing real-time features with WebSocket
- Managing multi-step user workflows
- State transitions need to be explicit and auditable

**Do NOT use when:**
- Simple static pages with no interactivity
- State can be managed with simple React useState
- No API calls or real-time updates needed

## Architecture Pattern

```
┌─────────────────────────────────────────────────────────┐
│                    XState Machine                        │
│                                                          │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐         │
│  │  loading │────▶│   idle   │────▶│  working │         │
│  └──────────┘     └────┬─────┘     └────┬─────┘         │
│       ▲                │                 │               │
│       │                ▼                 │               │
│       │          ┌──────────┐            │               │
│       └──────────│  error   │◀───────────┘               │
│                  └──────────┘                            │
└─────────────────────────────────────────────────────────┘
         │                    ▲
         │ API Calls          │ Responses
         ▼                    │
┌─────────────────────────────────────────────────────────┐
│                    API Client                            │
│  - Protobuf encoding/decoding                           │
│  - Fetch with proper headers                            │
│  - WebSocket connection                                  │
└─────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Define State Context

```javascript
const initialContext = {
    // Data state
    items: [],
    selectedItem: null,
    
    // UI state
    filter: 'all',
    sortBy: 'createdAt',
    sortOrder: 'desc',
    
    // Aggregates
    stats: { total: 0, active: 0, completed: 0 },
    
    // Error handling
    error: null
};
```

### Step 2: Design State Chart

Map user journeys to states:

| User Action | Current State | Target State | Side Effect |
|-------------|---------------|--------------|-------------|
| Page load | `init` | `loading` | Fetch initial data |
| Data loaded | `loading` | `idle` | Store in context |
| Create item | `idle` | `creating` | POST to API |
| Update item | `idle` | `updating` | PUT to API |
| Delete item | `idle` | `deleting` | DELETE to API |
| API error | any working | `error` | Store error message |
| WebSocket event | any | same | Update context |

### Step 3: Create Machine Definition

```javascript
import { createMachine, createActor, assign, fromPromise } from 'xstate';

const appMachine = createMachine({
    id: 'app',
    initial: 'loading',
    context: initialContext,
    
    // Root-level events (handled in ANY state)
    on: {
        // WebSocket events
        WS_CREATED: { actions: 'handleCreated' },
        WS_UPDATED: { actions: 'handleUpdated' },
        WS_DELETED: { actions: 'handleDeleted' },
        
        // UI events that don't change state
        FILTER: { actions: assign({ filter: ({ event }) => event.value }) },
        SORT: { actions: assign({ 
            sortBy: ({ event }) => event.field,
            sortOrder: ({ event }) => event.order 
        })}
    },
    
    states: {
        loading: {
            invoke: {
                src: 'loadData',
                onDone: { 
                    target: 'idle', 
                    actions: assign({
                        items: ({ event }) => event.output.items,
                        stats: ({ event }) => event.output.stats
                    })
                },
                onError: { 
                    target: 'error',
                    actions: assign({ error: ({ event }) => event.error.message })
                }
            }
        },
        
        idle: {
            on: {
                CREATE: 'creating',
                UPDATE: 'updating',
                DELETE: 'deleting',
                RETRY: 'loading'
            }
        },
        
        creating: {
            invoke: {
                src: 'createItem',
                input: ({ event }) => ({ data: event.data }),
                onDone: { target: 'idle' },
                onError: { target: 'error', actions: 'setError' }
            }
        },
        
        updating: {
            invoke: {
                src: 'updateItem',
                input: ({ event }) => ({ id: event.id, data: event.data }),
                onDone: { target: 'idle' },
                onError: { target: 'error', actions: 'setError' }
            }
        },
        
        deleting: {
            invoke: {
                src: 'deleteItem',
                input: ({ event }) => ({ id: event.id }),
                onDone: { target: 'idle' },
                onError: { target: 'error', actions: 'setError' }
            }
        },
        
        error: {
            on: {
                RETRY: 'loading',
                DISMISS: { target: 'idle', actions: assign({ error: null }) }
            }
        }
    }
});
```

### Step 4: Implement Actor Services

```javascript
const machineWithServices = appMachine.provide({
    actors: {
        loadData: fromPromise(async () => ({
            items: await api.getItems(),
            stats: await api.getStats()
        })),
        
        createItem: fromPromise(async ({ input }) => {
            return await api.createItem(input.data);
        }),
        
        updateItem: fromPromise(async ({ input }) => {
            return await api.updateItem(input.id, input.data);
        }),
        
        deleteItem: fromPromise(async ({ input }) => {
            return await api.deleteItem(input.id);
        })
    },
    
    actions: {
        handleCreated: assign({
            items: ({ context, event }) => [event.item, ...context.items],
            stats: ({ event }) => event.stats
        }),
        
        handleUpdated: assign({
            items: ({ context, event }) => 
                context.items.map(i => i.id === event.item.id ? event.item : i),
            stats: ({ event }) => event.stats
        }),
        
        handleDeleted: assign({
            items: ({ context, event }) => 
                context.items.filter(i => i.id !== event.deletedId),
            stats: ({ event }) => event.stats
        }),
        
        setError: assign({
            error: ({ event }) => event.error?.message || 'Unknown error'
        })
    }
});
```

### Step 5: API Client with Protobuf

```javascript
let types = {};  // Loaded protobuf types

const api = {
    async call(url, method, reqType, data, resType) {
        const options = { method };
        
        if (reqType && data) {
            const T = types[reqType];
            options.body = T.encode(T.create(data)).finish();
            options.headers = { 'Content-Type': 'application/x-protobuf' };
        }
        
        const res = await fetch(url, options);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        
        const buffer = await res.arrayBuffer();
        const T_res = types[resType];
        return T_res.toObject(
            T_res.decode(new Uint8Array(buffer)), 
            { defaults: true, longs: Number }
        );
    },
    
    getItems: () => api.call('/api/items', 'GET', null, null, 'ItemList')
        .then(r => r.items || []),
    
    createItem: (data) => api.call('/api/items', 'POST', 'CreateItemRequest', data, 'ApiResponse')
        .then(r => r.item),
    
    updateItem: (id, data) => api.call(`/api/items/${id}`, 'PUT', 'UpdateItemRequest', 
        { id, ...data }, 'ApiResponse').then(r => r.item),
    
    deleteItem: (id) => api.call(`/api/items/${id}`, 'DELETE', null, null, 'ApiResponse')
        .then(r => r.success)
};
```

### Step 6: WebSocket Integration

```javascript
function connectWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${location.host}/ws/items`);
    
    ws.onmessage = async (event) => {
        const buffer = await event.data.arrayBuffer();
        const EventType = types['DomainEvent'];
        const decoded = EventType.toObject(
            EventType.decode(new Uint8Array(buffer)),
            { defaults: true, longs: Number }
        );
        
        const eventMap = {
            0: 'WS_CREATED',  // CREATED enum value
            1: 'WS_UPDATED',  // UPDATED enum value
            2: 'WS_DELETED'   // DELETED enum value
        };
        
        const eventType = eventMap[decoded.type];
        if (eventType) {
            actor.send({
                type: eventType,
                item: decoded.item,
                deletedId: decoded.deletedId,
                stats: decoded.stats
            });
        }
    };
    
    ws.onclose = () => setTimeout(connectWebSocket, 1000);
    ws.onerror = () => ws.close();
    
    return ws;
}
```

### Step 7: Render Function

```javascript
function render(state) {
    const { items, stats, filter, error } = state.context;
    const currentState = state.value;
    
    // Apply filters
    const filtered = items.filter(item => {
        if (filter === 'all') return true;
        if (filter === 'active') return !item.completed;
        if (filter === 'completed') return item.completed;
        return true;
    });
    
    // Render items list
    const list = document.getElementById('item-list');
    list.innerHTML = filtered.map(item => `
        <li class="item ${item.completed ? 'completed' : ''}" data-id="${item.id}">
            <span class="item-title">${escapeHtml(item.title)}</span>
            <button class="delete-btn" onclick="handleDelete(${item.id})">×</button>
        </li>
    `).join('') || '<li class="empty-state">No items</li>';
    
    // Update stats
    document.getElementById('stats').innerHTML = `
        <span><strong>${stats.total}</strong> total</span>
        <span><strong>${stats.active}</strong> active</span>
    `;
    
    // Update app state class for CSS
    document.body.className = `state-${currentState}`;
    
    // Show error if present
    if (error) {
        document.getElementById('error-msg').textContent = error;
    }
}
```

### Step 8: Initialize Application

```javascript
import protobuf from 'protobufjs';

async function init() {
    // Load protobuf definitions
    const protoText = await (await fetch('/protos/domain.proto')).text();
    const protoRoot = protobuf.parse(protoText).root;
    
    // Register types
    ['Item', 'ItemList', 'CreateItemRequest', 'UpdateItemRequest', 
     'ApiResponse', 'DomainEvent', 'ItemStats'].forEach(t => {
        types[t] = protoRoot.lookupType(`domain.${t}`);
    });
    
    // Create and start actor
    const actor = createActor(machineWithServices);
    actor.subscribe(render);
    actor.start();
    
    // Setup event handlers
    setupEventHandlers(actor);
    
    // Connect WebSocket
    connectWebSocket();
}

init().catch(console.error);
```

## State Machine Patterns

### Pattern 1: Optimistic Updates

```javascript
// Update UI immediately, rollback on error
creating: {
    entry: assign({
        items: ({ context, event }) => [
            { id: 'temp', ...event.data }, 
            ...context.items
        ]
    }),
    invoke: {
        src: 'createItem',
        onDone: {
            target: 'idle',
            actions: assign({
                items: ({ context, event }) => 
                    context.items.map(i => 
                        i.id === 'temp' ? event.output : i
                    )
            })
        },
        onError: {
            target: 'error',
            actions: assign({
                items: ({ context }) => 
                    context.items.filter(i => i.id !== 'temp')
            })
        }
    }
}
```

### Pattern 2: Parallel States

```javascript
// Handle multiple concerns simultaneously
type: 'parallel',
states: {
    data: {
        initial: 'loading',
        states: { loading: {}, idle: {}, error: {} }
    },
    ui: {
        initial: 'collapsed',
        states: { collapsed: {}, expanded: {} }
    },
    connection: {
        initial: 'disconnected',
        states: { disconnected: {}, connected: {} }
    }
}
```

### Pattern 3: History States

```javascript
// Remember previous state on error
states: {
    idle: {},
    working: {
        initial: 'creating',
        states: {
            creating: {},
            updating: {},
            deleting: {}
        }
    },
    error: {
        on: {
            RETRY: { target: 'working.history' }  // Resume where left off
        }
    }
}
```

## Validation Checklist

Before finalizing the state machine:

- [ ] All user actions have corresponding events
- [ ] Every state has valid transitions defined
- [ ] Error states have recovery paths (RETRY, DISMISS)
- [ ] WebSocket events handled at root level
- [ ] Loading states show appropriate UI feedback
- [ ] Context updates are immutable (no direct mutations)
- [ ] API client uses protobuf encoding/decoding
- [ ] WebSocket reconnection is automatic

## File Structure

```
static/
├── app.js           # Main application with XState machine
├── styles.css       # State-based CSS (.state-loading, .state-error)
└── [domain].proto   # Copy of proto file for frontend
```

## Resources

- [XState v5 Documentation](https://stately.ai/docs/xstate)
- [XState Visualizer](https://stately.ai/viz)
- Reference implementation: `static/app.js` in this boilerplate

