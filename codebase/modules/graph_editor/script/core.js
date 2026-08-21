export const SVG_NS = 'http://www.w3.org/2000/svg';
export const LS_KEY = 'graph_editor_state';
export const PALETTE = ['#e0e0ff', '#d4f0c0', '#ffe0b0', '#f0c0c0', '#ffd866', '#9cc9ff'];

export const state = {
    nodes: [],
    edges: [],
    sel: null,
    tool: 'select',
    fill: '#ffffff',
    seq: 1,
    seqEdge: 0,
    editing: null,
};

export const view = { x: 0, y: 0, k: 1 };
export const undoStack = [];
export const redoStack = [];

export const svg = document.getElementById('canvas');
export const vp = document.getElementById('viewport');
export const edgesG = document.getElementById('edges');
export const nodesG = document.getElementById('nodes');
export const overlay = document.getElementById('overlay');
export const statusEl = document.getElementById('status');
export const labelEditor = document.getElementById('label-editor');
export const modal = document.getElementById('modal');
export const modalText = document.getElementById('modal-text');
export const modalTitle = document.getElementById('modal-title');
export const swatchBox = document.getElementById('swatches');
export const refInput = document.getElementById('node-ref');
export const btnOpenRef = document.getElementById('btn-open-ref');
export const btnNavBack = document.getElementById('btn-nav-back');
export const mdFileInput = document.getElementById('node-md-file');
export const mdSectionInput = document.getElementById('node-md-section');
export const btnOpenMd = document.getElementById('btn-open-md');
export const btnClearMd = document.getElementById('btn-clear-md');
export const saveDirtyEl = document.getElementById('save-dirty');

export let gesture = null;
export let drawing = null;
export let currentFile = null;
export const navStack = [];
export let dirty = false;

export function setGesture(v) { gesture = v; }
export function setDrawing(v) { drawing = v; }
export function setCurrentFile(v) { currentFile = v; }

export const esc = (s) => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
export const nodeById = (id) => state.nodes.find((n) => n.id === id);
export const edgeById = (id) => state.edges.find((e) => e.id === id);
export const isSel = (type, id) => state.sel && state.sel.type === type && state.sel.id === id;

export function nextId() {
    while (state.nodes.some((n) => n.id === 'n' + state.seq)) state.seq++;
    return 'n' + state.seq++;
}

export function toWorld(sx, sy) {
    const r = svg.getBoundingClientRect();
    return { x: (sx - r.left - view.x) / view.k, y: (sy - r.top - view.y) / view.k };
}

export function toScreen(wx, wy) {
    const r = svg.getBoundingClientRect();
    return { x: r.left + view.x + wx * view.k, y: r.top + view.y + wy * view.k };
}

export function applyView() {
    vp.setAttribute('transform', `translate(${view.x},${view.y}) scale(${view.k})`);
}

export function setStatus(msg) {
    statusEl.textContent = msg;
}

export function setDirty(v) {
    dirty = v;
    if (saveDirtyEl) saveDirtyEl.hidden = !v;
}