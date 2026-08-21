import { state, undoStack, redoStack, navStack, nodeById, nextId, setCurrentFile, setStatus, setDirty } from './core.js';
import { render } from './render.js';

export function snapshot() {
    return JSON.stringify({ nodes: state.nodes, edges: state.edges });
}

export function pushUndo() {
    undoStack.push(snapshot());
    if (undoStack.length > 60) undoStack.shift();
    redoStack.length = 0;
    setDirty(true);
}

export function undo() {
    if (!undoStack.length) return;
    redoStack.push(snapshot());
    restore(JSON.parse(undoStack.pop()));
}

export function redo() {
    if (!redoStack.length) return;
    undoStack.push(snapshot());
    restore(JSON.parse(redoStack.pop()));
}

export function restore(data) {
    state.nodes = data.nodes;
    state.edges = data.edges;
    state.sel = null;
    render();
}

export function addNode(shape, x, y) {
    const dims = { rect: [150, 70], diamond: [120, 80], ellipse: [150, 70] };
    pushUndo();
    const n = { id: nextId(), label: '', shape, color: state.fill, x, y, w: dims[shape][0], h: dims[shape][1], ref: '', mdRef: '' };
    state.nodes.push(n);
    state.sel = { type: 'node', id: n.id };
    render();
    setStatus('Node added — double-click it to type text');
}

export function addEdge(fromId, toId, points) {
    pushUndo();
    state.edges.push({
        id: 'e' + state.seqEdge++,
        from: fromId,
        to: toId,
        label: '',
        points: (points || []).map((p) => ({ x: Math.round(p.x), y: Math.round(p.y) })),
    });
    state.sel = { type: 'edge', id: state.edges[state.edges.length - 1].id };
    render();
    setStatus('Edge added — double-click the line to label it');
}

export function deleteSel() {
    if (!state.sel) return;
    pushUndo();
    if (state.sel.type === 'node') {
        const id = state.sel.id;
        state.nodes = state.nodes.filter((n) => n.id !== id);
        state.edges = state.edges.filter((e) => e.from !== id && e.to !== id);
    } else {
        state.edges = state.edges.filter((e) => e.id !== state.sel.id);
    }
    state.sel = null;
    render();
}

export function clearAll() {
    if (!confirm('Clear the entire canvas?')) return;
    undoStack.length = 0;
    redoStack.length = 0;
    setCurrentFile(null);
    navStack.length = 0;
    state.nodes = [];
    state.edges = [];
    state.sel = null;
    setDirty(false);
    render();
    setStatus('Canvas cleared');
}

export function setFill(color) {
    state.fill = color;
    if (state.sel && state.sel.type === 'node') {
        pushUndo();
        nodeById(state.sel.id).color = color;
        render();
    }
    document.querySelectorAll('.swatch').forEach((s) => s.classList.toggle('active', s.dataset.color === color));
}