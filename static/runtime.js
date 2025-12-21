/**
 * Unified State Machine - JavaScript Runtime
 */
import protobuf from 'protobufjs';
import jsyaml from 'js-yaml';

export class UnifiedMachine {
    constructor(config, types) {
        this.config = config;
        this.types = types;
        this.state = config.initial;
        this.context = JSON.parse(JSON.stringify(config.context || {}));
        this.version = 0;
        this.listeners = new Set();
        this.ws = null;
    }

    subscribe(fn) {
        this.listeners.add(fn);
        fn(this.snapshot());
        return () => this.listeners.delete(fn);
    }

    snapshot() {
        return { state: this.state, context: this.context, version: this.version };
    }

    notify() {
        this.listeners.forEach(fn => fn(this.snapshot()));
    }

    // WebSocket sync
    connect() {
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${protocol}//${location.host}/ws`);

        this.ws.onmessage = async (e) => {
            const buffer = await e.data.arrayBuffer();
            const SyncMessage = this.types['SyncMessage'];
            const msg = SyncMessage.toObject(SyncMessage.decode(new Uint8Array(buffer)), { defaults: true });

            if (msg.snapshot || msg.update) {
                const st = msg.snapshot || msg.update;
                this.state = st.state;
                this.context = this._protoContextToJS(st.context);
                this.version = st.version;
                this.notify();
            }
            if (msg.error) {
                console.error('Server rejected:', msg.error);
            }
        };

        this.ws.onclose = () => setTimeout(() => this.connect(), 1000);
        this.ws.onerror = () => this.ws.close();
    }

    send(eventType, payload) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

        const payloadBytes = this._encodePayload(eventType, payload);
        const MachineEvent = this.types['MachineEvent'];
        const SyncMessage = this.types['SyncMessage'];

        const event = MachineEvent.create({
            type: eventType,
            payload: payloadBytes,
            clientVersion: this.version
        });

        const msg = SyncMessage.create({ event });
        this.ws.send(SyncMessage.encode(msg).finish());
    }

    _encodePayload(eventType, payload) {
        const typeMap = {
            'CREATE': 'CreatePayload',
            'TOGGLE': 'TogglePayload',
            'DELETE': 'DeletePayload',
            'FILTER': 'FilterPayload'
        };
        const typeName = typeMap[eventType];
        if (!typeName) return new Uint8Array();

        const T = this.types[typeName];
        return T.encode(T.create(payload)).finish();
    }

    _protoContextToJS(ctx) {
        return {
            items: (ctx.items || []).map(i => ({
                id: i.id,
                title: i.title,
                completed: i.completed
            })),
            filter: ctx.filter || 'all',
            next_id: ctx.nextId || 1
        };
    }
}

export async function createMachine(protoPath, machinePath) {
    const protoText = await (await fetch(protoPath)).text();
    const root = protobuf.parse(protoText).root;
    const types = {};
    ['Todo', 'TodoList', 'AppContext', 'MachineState', 'MachineEvent', 'SyncMessage',
     'CreatePayload', 'TogglePayload', 'DeletePayload', 'FilterPayload'].forEach(t => {
        types[t] = root.lookupType(`app.${t}`);
    });

    const yamlText = await (await fetch(machinePath)).text();
    const config = jsyaml.load(yamlText);

    return new UnifiedMachine(config, types);
}
