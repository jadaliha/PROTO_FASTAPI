import { createMachine, createActor, assign, fromPromise } from 'xstate';
import protobuf from 'protobufjs';

let types = {};
let protoRoot = null;
let actor = null;
let ws = null;

const api = {
    async call(url, method, reqType, data, resType) {
        const options = { method };
        if (reqType && data) {
            const T = types[reqType];
            options.body = T.encode(T.create(data)).finish();
            options.headers = { 'Content-Type': 'application/x-protobuf' };
        }
        const res = await fetch(url, options);
        const buffer = await res.arrayBuffer();
        const T_res = types[resType];
        return T_res.toObject(T_res.decode(new Uint8Array(buffer)), { defaults: true, longs: Number });
    },
    getTodos: () => api.call('/api/todos', 'GET', null, null, 'TodoList').then(r => r.todos || []),
    getStats: () => api.call('/api/stats', 'GET', null, null, 'ApiResponse').then(r => r.stats),
    createTodo: (title) => api.call('/api/todos', 'POST', 'CreateTodoRequest', { title }, 'ApiResponse').then(r => r.todo),
    toggleTodo: (id, completed) => api.call(`/api/todos/${id}/toggle`, 'PUT', 'UpdateTodoRequest', { id, completed }, 'ApiResponse').then(r => r.todo),
    deleteTodo: (id) => api.call(`/api/todos/${id}`, 'DELETE', null, null, 'ApiResponse').then(r => r.success)
};

// Event types from proto enum
const EventType = { CREATED: 0, UPDATED: 1, DELETED: 2 };

const todoMachine = createMachine({
    id: 'todo',
    initial: 'loading',
    context: { todos: [], stats: { total: 0, active: 0, completed: 0 }, filter: 'all' },
    // Handle WebSocket events in ALL states (root level)
    on: {
        WS_CREATED: { actions: assign({
            todos: ({ context, event }) => [event.todo, ...context.todos],
            stats: ({ event }) => event.stats
        })},
        WS_UPDATED: { actions: assign({
            todos: ({ context, event }) => context.todos.map(t => t.id === event.todo.id ? event.todo : t),
            stats: ({ event }) => event.stats
        })},
        WS_DELETED: { actions: assign({
            todos: ({ context, event }) => context.todos.filter(t => t.id !== event.deletedId),
            stats: ({ event }) => event.stats
        })},
        FILTER: { actions: assign({ filter: ({ event }) => event.value }) }
    },
    states: {
        loading: {
            invoke: {
                src: 'loadData',
                onDone: { target: 'idle', actions: assign({ todos: ({ event }) => event.output.todos, stats: ({ event }) => event.output.stats }) }
            }
        },
        idle: {
            on: {
                ADD: 'adding',
                TOGGLE: 'toggling',
                DELETE: 'deleting'
            }
        },
        adding: {
            invoke: {
                src: 'addTodo',
                input: ({ event }) => ({ title: event.title }),
                onDone: { target: 'idle' }
            }
        },
        toggling: {
            invoke: {
                src: 'toggleTodo',
                input: ({ event }) => ({ id: event.id, completed: event.completed }),
                onDone: { target: 'idle' }
            }
        },
        deleting: {
            invoke: {
                src: 'deleteTodo',
                input: ({ event }) => ({ id: event.id }),
                onDone: { target: 'idle' }
            }
        }
    }
});

function connectWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${location.host}/ws/todos`);
    
    ws.onmessage = async (event) => {
        const buffer = await event.data.arrayBuffer();
        const TodoEvent = types['TodoEvent'];
        const decoded = TodoEvent.toObject(TodoEvent.decode(new Uint8Array(buffer)), { defaults: true, longs: Number });
        
        const stats = decoded.stats || { total: 0, active: 0, completed: 0 };
        
        switch (decoded.type) {
            case EventType.CREATED:
                actor.send({ type: 'WS_CREATED', todo: decoded.todo, stats });
                break;
            case EventType.UPDATED:
                actor.send({ type: 'WS_UPDATED', todo: decoded.todo, stats });
                break;
            case EventType.DELETED:
                actor.send({ type: 'WS_DELETED', deletedId: decoded.deletedId, stats });
                break;
        }
    };
    
    ws.onclose = () => setTimeout(connectWebSocket, 1000);  // Reconnect on disconnect
    ws.onerror = () => ws.close();
}

async function init() {
    const protoText = await (await fetch('/protos/todo.proto')).text();
    protoRoot = protobuf.parse(protoText).root;
    ['Todo', 'CreateTodoRequest', 'UpdateTodoRequest', 'ApiResponse', 'TodoList', 'TodoStats', 'TodoEvent'].forEach(t => {
        types[t] = protoRoot.lookupType(`todo.${t}`);
    });

    actor = createActor(todoMachine.provide({
        actors: {
            loadData: fromPromise(async () => ({ todos: await api.getTodos(), stats: await api.getStats() })),
            addTodo: fromPromise(async ({ input }) => api.createTodo(input.title)),
            toggleTodo: fromPromise(async ({ input }) => api.toggleTodo(input.id, input.completed)),
            deleteTodo: fromPromise(async ({ input }) => api.deleteTodo(input.id))
        }
    }));

    actor.subscribe(render);
    actor.start();
    setupEvents();
    connectWebSocket();
}

function render(state) {
    const { todos, stats, filter } = state.context;
    const list = document.getElementById('todo-list');
    if (!list) return;

    const filtered = todos.filter(t => filter === 'all' || (filter === 'active' ? !t.completed : t.completed));
    list.innerHTML = filtered.length > 0 ? filtered.map(t => `
        <li class="todo-item ${t.completed ? 'completed' : ''}" data-id="${t.id}">
            <input type="checkbox" ${t.completed ? 'checked' : ''} onchange="window.toggleTodo(${t.id}, this.checked)">
            <span class="todo-title">${escapeHtml(t.title)}</span>
            <button class="delete-btn" hx-disable onclick="window.deleteTodo(event, ${t.id})">×</button>
        </li>
    `).join('') : '<li class="empty-state">No items.</li>';

    const statsDiv = document.getElementById('stats');
    if (statsDiv) statsDiv.innerHTML = `
        <div class="stats">
            <span><strong>${stats.total}</strong> total</span>
            <span><strong>${stats.active}</strong> active</span>
            <span><strong>${stats.completed}</strong> completed</span>
        </div>
    `;

    document.querySelectorAll('.filter-tab').forEach(btn => {
        const btnFilter = btn.getAttribute('onclick').match(/'([^']+)'/)[1];
        btn.classList.toggle('active', btnFilter === filter);
    });
}

function setupEvents() {
    const form = document.getElementById('todo-form');
    form?.addEventListener('submit', (e) => {
        e.preventDefault();
        const input = form.querySelector('input');
        if (input.value.trim()) {
            actor.send({ type: 'ADD', title: input.value.trim() });
            input.value = '';
        }
    });
}

window.toggleTodo = (id, completed) => actor.send({ type: 'TOGGLE', id, completed });

let pendingDeleteId = null;

window.deleteTodo = (event, id) => {
    event.stopPropagation();
    event.preventDefault();
    pendingDeleteId = id;
    document.getElementById('confirm-modal').classList.add('show');
};

window.confirmDelete = () => {
    if (pendingDeleteId !== null) {
        actor.send({ type: 'DELETE', id: pendingDeleteId });
        pendingDeleteId = null;
    }
    document.getElementById('confirm-modal').classList.remove('show');
};

window.cancelDelete = () => {
    pendingDeleteId = null;
    document.getElementById('confirm-modal').classList.remove('show');
};

window.changeFilter = (value) => actor.send({ type: 'FILTER', value });

function escapeHtml(t) {
    const d = document.createElement('div');
    d.textContent = t;
    return d.innerHTML;
}

init().catch(console.error);
