import { createMachine, createActor, assign, fromPromise } from 'xstate';
import protobuf from 'protobufjs';

// Protobuf message definitions
let protoRoot = null;
let TodoProto = null;
let CreateTodoRequest = null;
let UpdateTodoRequest = null;
let ApiResponse = null;
let actor = null;

// Initialize protobuf
async function initProtobuf() {
    try {
        const response = await fetch('/static/todo.proto');
        const protoText = await response.text();
        protoRoot = protobuf.parse(protoText).root;

        TodoProto = protoRoot.lookupType('todo.Todo');
        CreateTodoRequest = protoRoot.lookupType('todo.CreateTodoRequest');
        UpdateTodoRequest = protoRoot.lookupType('todo.UpdateTodoRequest');
        ApiResponse = protoRoot.lookupType('todo.ApiResponse');
    } catch (err) {
        console.error('Failed to initialize protobuf:', err);
        throw err;
    }
}

// API helper functions using protobuf
const api = {
    async getTodos() {
        const response = await fetch('/api/todos');
        const buffer = await response.arrayBuffer();
        const TodoList = protoRoot.lookupType('todo.TodoList');
        const message = TodoList.decode(new Uint8Array(buffer));
        const todoList = TodoList.toObject(message, { defaults: true, longs: Number });
        return todoList.todos || [];
    },

    async createTodo(title) {
        const request = CreateTodoRequest.create({ title });
        const buffer = CreateTodoRequest.encode(request).finish();

        const response = await fetch('/api/todos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-protobuf' },
            body: buffer
        });

        const resBuffer = await response.arrayBuffer();
        const apiResponse = ApiResponse.toObject(ApiResponse.decode(new Uint8Array(resBuffer)), {
            defaults: true,
            longs: Number,
            oneofs: true
        });
        return apiResponse.todo;
    },

    async toggleTodo(id, completed) {
        const request = UpdateTodoRequest.create({ id, completed });
        const buffer = UpdateTodoRequest.encode(request).finish();

        const response = await fetch(`/api/todos/${id}/toggle`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/x-protobuf' },
            body: buffer
        });

        const resBuffer = await response.arrayBuffer();
        const apiResponse = ApiResponse.toObject(ApiResponse.decode(new Uint8Array(resBuffer)), {
            defaults: true,
            longs: Number,
            oneofs: true
        });
        return apiResponse.todo;
    },

    async deleteTodo(id) {
        const response = await fetch(`/api/todos/${id}`, {
            method: 'DELETE'
        });

        const resBuffer = await response.arrayBuffer();
        const apiResponse = ApiResponse.toObject(ApiResponse.decode(new Uint8Array(resBuffer)), {
            defaults: true,
            longs: Number,
            oneofs: true
        });
        return apiResponse.success;
    },

    async getStats() {
        const response = await fetch('/api/stats');
        const resBuffer = await response.arrayBuffer();
        const apiResponse = ApiResponse.toObject(ApiResponse.decode(new Uint8Array(resBuffer)), {
            defaults: true,
            longs: Number,
            oneofs: true
        });
        return apiResponse.stats;
    }
};

// Initialize the application
async function initApp() {
    await initProtobuf();

    // Define the state machine
    const todoMachine = createMachine({
        id: 'todoApp',
        initial: 'loading',
        context: {
            todos: [],
            stats: { total: 0, active: 0, completed: 0 },
            filter: 'all',
            error: null
        },
        states: {
            loading: {
                invoke: {
                    src: 'loadTodos',
                    onDone: {
                        target: 'idle',
                        actions: assign({
                            todos: ({ event }) => event.output.todos,
                            stats: ({ event }) => event.output.stats
                        })
                    },
                    onError: {
                        target: 'error',
                        actions: assign({
                            error: ({ event }) => event.error
                        })
                    }
                }
            },
            idle: {
                on: {
                    ADD_TODO: 'adding',
                    TOGGLE_TODO: 'updating',
                    DELETE_TODO: 'deleting',
                    REFRESH: 'loading',
                    CHANGE_FILTER: {
                        actions: assign({
                            filter: ({ event }) => event.value
                        })
                    }
                }
            },
            adding: {
                invoke: {
                    src: 'createTodo',
                    input: ({ event }) => ({ title: event.title }),
                    onDone: {
                        target: 'refreshing',
                        actions: assign({
                            todos: ({ context, event }) => [event.output, ...context.todos]
                        })
                    },
                    onError: {
                        target: 'idle',
                        actions: assign({ error: ({ event }) => event.error })
                    }
                }
            },
            updating: {
                invoke: {
                    src: 'updateTodo',
                    input: ({ event }) => ({ id: event.id, completed: event.completed }),
                    onDone: {
                        target: 'refreshing',
                        actions: assign({
                            todos: ({ context, event }) =>
                                context.todos.map(t => t.id === event.output.id ? event.output : t)
                        })
                    },
                    onError: {
                        target: 'idle',
                        actions: assign({ error: ({ event }) => event.error })
                    }
                }
            },
            deleting: {
                invoke: {
                    src: 'deleteTodo',
                    input: ({ event }) => ({ id: event.id }),
                    onDone: {
                        target: 'refreshing',
                        actions: assign({
                            todos: ({ context, event }) =>
                                context.todos.filter(t => t.id !== event.output)
                        })
                    },
                    onError: {
                        target: 'idle',
                        actions: assign({ error: ({ event }) => event.error })
                    }
                }
            },
            refreshing: {
                invoke: {
                    src: 'loadTodos',
                    onDone: {
                        target: 'idle',
                        actions: assign({
                            todos: ({ event }) => event.output.todos,
                            stats: ({ event }) => event.output.stats
                        })
                    }
                }
            },
            error: {
                on: {
                    RETRY: 'loading'
                }
            }
        }
    });

    // Create machine with actors
    const machine = todoMachine.provide({
        actors: {
            loadTodos: fromPromise(async () => {
                const [todos, stats] = await Promise.all([
                    api.getTodos(),
                    api.getStats()
                ]);
                return { todos, stats };
            }),
            createTodo: fromPromise(async ({ input }) => {
                return await api.createTodo(input.title);
            }),
            updateTodo: fromPromise(async ({ input }) => {
                return await api.toggleTodo(input.id, input.completed);
            }),
            deleteTodo: fromPromise(async ({ input }) => {
                await api.deleteTodo(input.id);
                return input.id;
            })
        }
    });

    // Create actor
    actor = createActor(machine);

    actor.start();

    // Subscribe to state changes and update UI
    actor.subscribe((state) => {
        renderUI(state);
    });

    // Set up event listeners
    setupEventListeners();
}

// Render UI based on state
function renderUI(state) {
    const { todos, stats, filter } = state.context;

    // Update todos list
    const todoList = document.getElementById('todo-list');
    if (!todoList) return;

    const filteredTodos = todos.filter(todo => {
        if (filter === 'active') return !todo.completed;
        if (filter === 'completed') return todo.completed;
        return true;
    });

    todoList.innerHTML = filteredTodos.length > 0
        ? filteredTodos.map(todo => `
        <li class="todo-item ${todo.completed ? 'completed' : ''}" data-id="${todo.id}">
          <input type="checkbox" ${todo.completed ? 'checked' : ''} 
                 onchange="window.toggleTodo(${todo.id}, this.checked)">
          <span class="todo-title">${escapeHtml(todo.title)}</span>
          <button class="delete-btn" onclick="window.deleteTodo(${todo.id})">×</button>
        </li>
      `).join('')
        : '<li class="empty-state">No todos yet. Add one above!</li>';

    // Update stats
    const statsDiv = document.getElementById('stats');
    if (statsDiv) {
        statsDiv.innerHTML = `
        <div class="stats">
            <span><strong>${stats.total}</strong> total</span>
            <span><strong>${stats.active}</strong> active</span>
            <span><strong>${stats.completed}</strong> completed</span>
        </div>
        `;
    }

    // Update loading states
    document.body.classList.remove('state-loading', 'state-idle', 'state-adding', 'state-updating', 'state-deleting');
    document.body.classList.add(`state-${state.value}`);
}

// Set up event listeners
function setupEventListeners() {
    const form = document.getElementById('todo-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = form.querySelector('input[name="title"]');
        const title = input.value.trim();

        if (title) {
            actor.send({ type: 'ADD_TODO', title });
            input.value = '';
        }
    });
}

// Global functions for inline event handlers
window.toggleTodo = (id, completed) => {
    actor.send({ type: 'TOGGLE_TODO', id, completed });
};

window.deleteTodo = (id) => {
    if (confirm('Delete this todo?')) {
        actor.send({ type: 'DELETE_TODO', id });
    }
};

window.changeFilter = (filter) => {
    actor.send({ type: 'CHANGE_FILTER', value: filter });
};

// Utility function
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize when the module loads
initApp().catch(err => {
    console.error('App initialization failed:', err);
    if (document.getElementById('todo-list')) {
        document.getElementById('todo-list').innerHTML =
            `<li class="error-state">Failed to load application: ${err.message}</li>`;
    }
});

// Export for debugging
window.todoActor = () => actor;