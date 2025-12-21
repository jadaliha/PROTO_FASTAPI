/**
 * Todo App - Minimal UI
 * All logic is in the machine, this just renders and sends events
 */
import { createMachine } from './runtime.js';

let machine = null;

async function init() {
    machine = await createMachine('/protos/app.proto', '/machines/todo.machine.yaml');
    machine.subscribe(render);
    machine.connect();
    setupEvents();
}

// ═══════════════════════════════════════════════════════════════
// RENDER - Pure function from state → DOM
// ═══════════════════════════════════════════════════════════════

function render({ state, context }) {
    const { items, filter } = context;

    // Filter items
    const filtered = items.filter(i =>
        filter === 'all' ? true :
        filter === 'active' ? !i.completed :
        i.completed
    );

    // Stats
    const total = items.length;
    const completed = items.filter(i => i.completed).length;
    const active = total - completed;

    document.getElementById('stats').innerHTML = `
        <span><b>${total}</b> total</span>
        <span><b>${active}</b> active</span>
        <span><b>${completed}</b> done</span>
    `;

    // Items
    document.getElementById('items').innerHTML = filtered.length
        ? filtered.map(i => `
            <li class="${i.completed ? 'done' : ''}" data-id="${i.id}">
                <input type="checkbox" ${i.completed ? 'checked' : ''}>
                <span>${esc(i.title)}</span>
                <button class="del">×</button>
            </li>
        `).join('')
        : '<li class="empty">No items</li>';

    // Filter tabs
    document.querySelectorAll('[data-filter]').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.filter === filter);
    });
}

// ═══════════════════════════════════════════════════════════════
// EVENTS - Send to machine, it handles the rest
// ═══════════════════════════════════════════════════════════════

function setupEvents() {
    // Create
    document.getElementById('form').addEventListener('submit', e => {
        e.preventDefault();
        const input = e.target.title;
        if (input.value.trim()) {
            machine.send('CREATE', { title: input.value.trim() });
            input.value = '';
        }
    });

    // Toggle & Delete (delegated)
    document.getElementById('items').addEventListener('click', e => {
        const li = e.target.closest('li');
        if (!li?.dataset.id) return;
        const id = +li.dataset.id;

        if (e.target.matches('input[type="checkbox"]')) {
            machine.send('TOGGLE', { id, completed: e.target.checked });
        }
        if (e.target.matches('.del')) {
            machine.send('DELETE', { id });
        }
    });

    // Filter
    document.querySelectorAll('[data-filter]').forEach(btn => {
        btn.addEventListener('click', () => {
            machine.send('FILTER', { filter: btn.dataset.filter });
        });
    });
}

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

init();

