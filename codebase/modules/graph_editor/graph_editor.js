const SVG_NS = 'http://www.w3.org/2000/svg';
const LS_KEY = 'graph_editor_state';
const PALETTE = ['#ffffff', '#e0e0ff', '#d4f0c0', '#ffe0b0', '#f0c0c0', '#ffd866', '#9cc9ff', '#ff9ecf'];

const state = {
    nodes: [],
    edges: [],
    sel: null,
    tool: 'select',
    fill: '#ffffff',
    seq: 1,
    seqEdge: 0,
    editing: null,
};

const view = { x: 0, y: 0, k: 1 };
const undoStack = [];
const redoStack = [];

const svg = document.getElementById('canvas');
const vp = document.getElementById('viewport');
const edgesG = document.getElementById('edges');
const nodesG = document.getElementById('nodes');
const overlay = document.getElementById('overlay');
const statusEl = document.getElementById('status');
const labelEditor = document.getElementById('label-editor');

let gesture = null;
let drawing = null;

// ---------- helpers ----------
const esc = (s) => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const nodeById = (id) => state.nodes.find((n) => n.id === id);
const edgeById = (id) => state.edges.find((e) => e.id === id);
const isSel = (type, id) => state.sel && state.sel.type === type && state.sel.id === id;

function nextId() {
    while (state.nodes.some((n) => n.id === 'n' + state.seq)) state.seq++;
    return 'n' + state.seq++;
}

function toWorld(sx, sy) {
    const r = svg.getBoundingClientRect();
    return { x: (sx - r.left - view.x) / view.k, y: (sy - r.top - view.y) / view.k };
}

function toScreen(wx, wy) {
    const r = svg.getBoundingClientRect();
    return { x: r.left + view.x + wx * view.k, y: r.top + view.y + wy * view.k };
}

function applyView() {
    vp.setAttribute('transform', `translate(${view.x},${view.y}) scale(${view.k})`);
}

function setStatus(msg) {
    statusEl.textContent = msg;
}

function snapshot() {
    return JSON.stringify({ nodes: state.nodes, edges: state.edges });
}

function pushUndo() {
    undoStack.push(snapshot());
    if (undoStack.length > 60) undoStack.shift();
    redoStack.length = 0;
}

function undo() {
    if (!undoStack.length) return;
    redoStack.push(snapshot());
    restore(JSON.parse(undoStack.pop()));
}

function redo() {
    if (!redoStack.length) return;
    undoStack.push(snapshot());
    restore(JSON.parse(redoStack.pop()));
}

function restore(data) {
    state.nodes = data.nodes;
    state.edges = data.edges;
    state.sel = null;
    render();
}

function save() {
    try { localStorage.setItem(LS_KEY, snapshot()); } catch (e) { /* ignore */ }
}

// ---------- geometry ----------
function boundaryPoint(n, tx, ty) {
    const dx = tx - n.x, dy = ty - n.y;
    const d = Math.hypot(dx, dy) || 1;
    const ux = dx / d, uy = dy / d;
    const rx = n.w / 2, ry = n.h / 2;
    if (n.shape === 'rect') {
        const t = Math.min(rx / Math.abs(ux || 1e-6), ry / Math.abs(uy || 1e-6));
        return { x: n.x + ux * t, y: n.y + uy * t };
    }
    if (n.shape === 'ellipse') {
        const t = 1 / Math.sqrt((ux / rx) ** 2 + (uy / ry) ** 2);
        return { x: n.x + ux * t, y: n.y + uy * t };
    }
    const t = 1 / (Math.abs(ux) / rx + Math.abs(uy) / ry);
    return { x: n.x + ux * t, y: n.y + uy * t };
}

function edgePolyline(a, b, waypoints) {
    const wps = waypoints || [];
    if (a.id === b.id && !wps.length) {
        const rx = a.w / 2, top = a.y - a.h / 2;
        return [
            { x: a.x + rx, y: a.y },
            { x: a.x + rx + 50, y: top - 40 },
            { x: a.x - 30, y: top - 10 },
            { x: a.x, y: top },
        ];
    }
    if (wps.length) {
        const pts = [boundaryPoint(a, wps[0].x, wps[0].y)];
        for (const p of wps) pts.push(p);
        pts.push(boundaryPoint(b, wps[wps.length - 1].x, wps[wps.length - 1].y));
        return pts;
    }
    return [boundaryPoint(a, b.x, b.y), boundaryPoint(b, a.x, a.y)];
}

function polylineD(pts) {
    return 'M ' + pts.map((p) => `${p.x},${p.y}`).join(' L ');
}

function polylineMid(pts) {
    if (!pts.length) return { x: 0, y: 0 };
    const segs = [];
    let total = 0;
    for (let i = 1; i < pts.length; i++) {
        const L = Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y);
        segs.push(L);
        total += L;
    }
    if (!segs.length) return pts[0];
    let target = total / 2;
    for (let i = 0; i < segs.length; i++) {
        if (target <= segs[i] || i === segs.length - 1) {
            const t = segs[i] ? target / segs[i] : 0;
            return { x: pts[i].x + (pts[i + 1].x - pts[i].x) * t, y: pts[i].y + (pts[i + 1].y - pts[i].y) * t };
        }
        target -= segs[i];
    }
    return pts[0];
}

function edgeMid(a, b, points) {
    if (a.id === b.id) return { x: a.x, y: a.y - a.h / 2 - 20 };
    return polylineMid(edgePolyline(a, b, points));
}

function hitNode(x, y) {
    for (let i = state.nodes.length - 1; i >= 0; i--) {
        const n = state.nodes[i];
        const rx = n.w / 2, ry = n.h / 2;
        const dx = x - n.x, dy = y - n.y;
        let hit = false;
        if (n.shape === 'rect') hit = Math.abs(dx) <= rx && Math.abs(dy) <= ry;
        else if (n.shape === 'ellipse') hit = (dx / rx) ** 2 + (dy / ry) ** 2 <= 1;
        else hit = Math.abs(dx) / rx + Math.abs(dy) / ry <= 1;
        if (hit) return n;
    }
    return null;
}

function hitResize(x, y) {
    const n = nodeById(state.sel && state.sel.type === 'node' ? state.sel.id : '');
    if (!n) return null;
    const rx = n.w / 2, ry = n.h / 2;
    return x >= n.x + rx - 8 && x <= n.x + rx + 2 && y >= n.y + ry - 8 && y <= n.y + ry + 2 ? n : null;
}

function hitEdge(x, y) {
    const paths = edgesG.querySelectorAll('.edge-hit');
    const pt = new DOMPoint(x, y);
    for (let i = paths.length - 1; i >= 0; i--) {
        if (paths[i].isPointInStroke(pt)) {
            return edgeById(paths[i].closest('.edge').dataset.id);
        }
    }
    return null;
}

// ---------- rendering ----------
function labelTspans(text, lineH) {
    const lines = String(text).split('\n');
    return lines.map((ln, i) =>
        `<tspan x="0" dy="${i === 0 ? -(lines.length - 1) * lineH / 2 : lineH}" dominant-baseline="middle" text-anchor="middle">${esc(ln) || ' '}</tspan>`
    ).join('');
}

function render() {
    nodesG.innerHTML = state.nodes.map((n) => {
        const rx = n.w / 2, ry = n.h / 2;
        let body;
        if (n.shape === 'rect') body = `<rect x="${-rx}" y="${-ry}" width="${n.w}" height="${n.h}" rx="5" fill="${n.color}"/>`;
        else if (n.shape === 'ellipse') body = `<ellipse cx="0" cy="0" rx="${rx}" ry="${ry}" fill="${n.color}"/>`;
        else body = `<polygon points="0,${-ry} ${rx},0 0,${ry} ${-rx},0" fill="${n.color}"/>`;
        const hasLabel = String(n.label ?? '').trim() !== '';
        const label = hasLabel ? `<text class="label">${labelTspans(n.label, 12)}</text>` : '';
        const sel = isSel('node', n.id);
        const handle = sel ? `<rect class="resize" x="${rx - 7}" y="${ry - 7}" width="10" height="10"/>` : '';
        return `<g class="node${sel ? ' selected' : ''}" data-id="${n.id}" data-shape="${n.shape}" transform="translate(${n.x},${n.y})">${body}${label}${handle}</g>`;
    }).join('');

    edgesG.innerHTML = state.edges.map((e) => {
        const a = nodeById(e.from), b = nodeById(e.to);
        if (!a || !b) return '';
        const pts = edgePolyline(a, b, e.points);
        const d = polylineD(pts);
        const mid = edgeMid(a, b, e.points);
        const sel = isSel('edge', e.id);
        const label = e.label ? `<g class="elabel" transform="translate(${mid.x},${mid.y})"><text>${labelTspans(e.label, 11)}</text></g>` : '';
        return `<g class="edge${sel ? ' selected' : ''}" data-id="${e.id}">
            <path class="edge-hit" d="${d}"/>
            <path class="edge-path" d="${d}" marker-end="url(#arrow)" stroke="${sel ? '#ffd866' : '#ccc'}"/>
            ${label}</g>`;
    }).join('');

    renderOverlay();
    save();
}

function renderOverlay() {
    overlay.innerHTML = '';
    if (!drawing) return;
    const a = nodeById(drawing.from);
    if (!a) return;
    const c = drawing.cursor || { x: a.x, y: a.y };
    const pts = [];
    if (drawing.points.length) {
        pts.push(boundaryPoint(a, drawing.points[0].x, drawing.points[0].y));
        for (const p of drawing.points) pts.push(p);
    } else {
        pts.push(boundaryPoint(a, c.x, c.y));
    }
    overlay.innerHTML = `<path class="edge-preview" d="${polylineD(pts)} L ${c.x},${c.y}"/>`;
}

// ---------- mutations ----------
function addNode(shape, x, y) {
    const dims = { rect: [150, 70], diamond: [120, 80], ellipse: [150, 70] };
    pushUndo();
    const n = { id: nextId(), label: '', shape, color: state.fill, x, y, w: dims[shape][0], h: dims[shape][1] };
    state.nodes.push(n);
    state.sel = { type: 'node', id: n.id };
    render();
    setStatus('Node added — double-click it to type text');
}

function addEdge(fromId, toId, points) {
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

function deleteSel() {
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

function clearAll() {
    if (!confirm('Clear the entire canvas?')) return;
    undoStack.length = 0;
    redoStack.length = 0;
    state.nodes = [];
    state.edges = [];
    state.sel = null;
    render();
    setStatus('Canvas cleared');
}

function setFill(color) {
    state.fill = color;
    document.getElementById('fill-input').value = color;
    if (state.sel && state.sel.type === 'node') {
        pushUndo();
        nodeById(state.sel.id).color = color;
        render();
    }
    document.querySelectorAll('.swatch').forEach((s) => s.classList.toggle('active', s.dataset.color === color));
}

function updateSelectionUI() {
    nodesG.querySelectorAll('.node').forEach((g) => {
        const sel = isSel('node', g.dataset.id);
        g.classList.toggle('selected', sel);
        let handle = g.querySelector('.resize');
        if (sel) {
            const n = nodeById(g.dataset.id);
            const rx = n.w / 2, ry = n.h / 2;
            if (!handle) {
                handle = document.createElementNS(SVG_NS, 'rect');
                handle.setAttribute('class', 'resize');
                handle.setAttribute('x', rx - 7);
                handle.setAttribute('y', ry - 7);
                handle.setAttribute('width', 10);
                handle.setAttribute('height', 10);
                g.appendChild(handle);
            }
        } else if (handle) {
            handle.remove();
        }
    });
    edgesG.querySelectorAll('.edge').forEach((g) => {
        const sel = isSel('edge', g.dataset.id);
        g.classList.toggle('selected', sel);
        const p = g.querySelector('.edge-path');
        if (p) p.setAttribute('stroke', sel ? '#ffd866' : '#ccc');
    });
}

// ---------- label editing ----------
function openLabelEditor(type, id) {
    const obj = type === 'node' ? nodeById(id) : edgeById(id);
    if (!obj) return;
    let wx, wy, w;
    if (type === 'node') {
        wx = obj.x; wy = obj.y; w = Math.max(80, obj.w * view.k);
    } else {
        const a = nodeById(obj.from), b = nodeById(obj.to);
        const mid = edgeMid(a, b, obj.points);
        wx = mid.x; wy = mid.y; w = 160;
    }
    const p = toScreen(wx, wy);
    const r = svg.getBoundingClientRect();
    labelEditor.value = obj.label || '';
    labelEditor.style.width = w + 'px';
    labelEditor.style.left = (p.x - r.left - w / 2) + 'px';
    labelEditor.style.top = (p.y - r.top - 16) + 'px';
    labelEditor.style.display = 'block';
    state.editing = { type, id };
    labelEditor.focus();
    labelEditor.select();
}

function commitLabel() {
    if (!state.editing) return;
    const obj = state.editing.type === 'node' ? nodeById(state.editing.id) : edgeById(state.editing.id);
    if (obj) {
        pushUndo();
        obj.label = labelEditor.value;
    }
    state.editing = null;
    labelEditor.style.display = 'none';
    render();
}

labelEditor.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); commitLabel(); }
    else if (e.key === 'Escape') { state.editing = null; labelEditor.style.display = 'none'; }
    e.stopPropagation();
});
labelEditor.addEventListener('blur', commitLabel);

// ---------- tool selection ----------
function setTool(tool) {
    if (tool !== 'edge' && drawing) { drawing = null; render(); }
    state.tool = tool;
    document.querySelectorAll('#tools .tool').forEach((b) => b.classList.toggle('active', b.dataset.tool === tool));
    const names = { select: 'Select', pan: 'Pan', rect: 'Square', diamond: 'Diamond', ellipse: 'Oval', edge: 'Edge' };
    setStatus(names[tool] + ' tool active');
}

document.querySelectorAll('#tools .tool').forEach((b) => b.addEventListener('click', () => setTool(b.dataset.tool)));

// ---------- mouse interaction ----------
svg.addEventListener('mousedown', (e) => {
    if (state.editing) return;

    if (e.button === 1 || state.tool === 'pan') {
        e.preventDefault();
        gesture = { mode: 'pan', sx: e.clientX, sy: e.clientY, ox: view.x, oy: view.y };
        svg.classList.add('panning');
        return;
    }

    if (e.button !== 0) return;
    const w = toWorld(e.clientX, e.clientY);
    const node = hitNode(w.x, w.y);

    if (state.tool === 'edge') return;

    if (state.tool !== 'select') {
        if (!node) addNode(state.tool, w.x, w.y);
        return;
    }

    const rs = hitResize(w.x, w.y);
    if (rs) {
        gesture = { mode: 'resize', node: rs, sx: w.x, sy: w.y, ow: rs.w, oh: rs.h };
        pushUndo();
        return;
    }

    if (node) {
        state.sel = { type: 'node', id: node.id };
        gesture = { mode: 'drag', node, sx: w.x, sy: w.y };
        pushUndo();
        updateSelectionUI();
        return;
    }

    const edge = hitEdge(w.x, w.y);
    if (edge) {
        state.sel = { type: 'edge', id: edge.id };
        gesture = { mode: 'select-edge', sx: e.clientX, sy: e.clientY, moved: false };
        updateSelectionUI();
        return;
    }

    state.sel = null;
    gesture = { mode: 'pan', sx: e.clientX, sy: e.clientY, ox: view.x, oy: view.y };
    svg.classList.add('panning');
    updateSelectionUI();
});

svg.addEventListener('mousemove', (e) => {
    if (drawing) {
        drawing.cursor = toWorld(e.clientX, e.clientY);
        renderOverlay();
    }
    if (!gesture) {
        const w = toWorld(e.clientX, e.clientY);
        const overResize = hitResize(w.x, w.y);
        const overNode = hitNode(w.x, w.y);
        const overEdge = hitEdge(w.x, w.y);
        svg.style.cursor = state.tool === 'pan' ? 'grab'
            : state.tool === 'select' && overResize ? 'nwse-resize'
            : state.tool === 'select' && overNode ? 'move'
            : state.tool === 'select' && overEdge ? 'pointer'
            : state.tool !== 'select' ? 'crosshair'
            : 'default';
        return;
    }
    const w = toWorld(e.clientX, e.clientY);
    if (gesture.mode === 'drag') {
        gesture.node.x = w.x;
        gesture.node.y = w.y;
        render();
    } else if (gesture.mode === 'resize') {
        const rx = Math.abs(w.x - gesture.sx), ry = Math.abs(w.y - gesture.sy);
        gesture.node.w = Math.max(40, gesture.ow + rx * 2);
        gesture.node.h = Math.max(30, gesture.oh + ry * 2);
        render();
    } else if (gesture.mode === 'select-edge') {
        const d = Math.hypot(e.clientX - gesture.sx, e.clientY - gesture.sy);
        if (d > 4) { gesture.moved = true; setTool('select'); }
    } else if (gesture.mode === 'pan') {
        view.x = gesture.ox + (e.clientX - gesture.sx);
        view.y = gesture.oy + (e.clientY - gesture.sy);
        applyView();
    }
});

window.addEventListener('mouseup', () => {
    gesture = null;
    svg.classList.remove('panning');
});

svg.addEventListener('click', (e) => {
    if (state.tool !== 'edge' || state.editing) return;
    const w = toWorld(e.clientX, e.clientY);
    const node = hitNode(w.x, w.y);
    if (!drawing) {
        if (!node) return;
        drawing = { from: node.id, points: [], cursor: w };
        state.sel = { type: 'node', id: node.id };
        render();
        setStatus('Edge drawing: click canvas to add points, click a node to finish, Esc to cancel');
    } else if (node) {
        addEdge(drawing.from, node.id, drawing.points);
        drawing = null;
        render();
    } else {
        drawing.points.push({ x: w.x, y: w.y });
        render();
    }
});

svg.addEventListener('contextmenu', (e) => {
    if (!drawing) return;
    e.preventDefault();
    drawing = null;
    render();
    setStatus('Edge drawing cancelled');
});

svg.addEventListener('dblclick', (e) => {
    if (state.tool === 'edge' || state.editing) return;
    const w = toWorld(e.clientX, e.clientY);
    const node = hitNode(w.x, w.y);
    if (node) { state.sel = { type: 'node', id: node.id }; render(); openLabelEditor('node', node.id); return; }
    const edge = hitEdge(w.x, w.y);
    if (edge) { state.sel = { type: 'edge', id: edge.id }; render(); openLabelEditor('edge', edge.id); }
});

svg.addEventListener('wheel', (e) => {
    e.preventDefault();
    const r = svg.getBoundingClientRect();
    const px = e.clientX - r.left, py = e.clientY - r.top;
    const wx = (px - view.x) / view.k, wy = (py - view.y) / view.k;
    const factor = e.deltaY < 0 ? 1.1 : 1 / 1.1;
    view.k = Math.max(0.15, Math.min(4, view.k * factor));
    view.x = px - wx * view.k;
    view.y = py - wy * view.k;
    applyView();
}, { passive: false });

// ---------- keyboard ----------
document.addEventListener('keydown', (e) => {
    if (state.editing) return;
    const tag = document.activeElement.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA') return;
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') { e.preventDefault(); e.shiftKey ? redo() : undo(); return; }
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'y') { e.preventDefault(); redo(); return; }
    if (e.key === 'Escape' && drawing) { drawing = null; render(); setStatus('Edge drawing cancelled'); return; }
    if (e.key === 'Delete' || e.key === 'Backspace') { e.preventDefault(); deleteSel(); return; }
    const map = { v: 'select', h: 'pan', r: 'rect', d: 'diamond', o: 'ellipse', e: 'edge' };
    if (map[e.key.toLowerCase()]) setTool(map[e.key.toLowerCase()]);
});

// ---------- zoom controls ----------
document.getElementById('zoom-in').addEventListener('click', () => { view.k *= 1.25; applyView(); });
document.getElementById('zoom-out').addEventListener('click', () => { view.k = Math.max(0.15, view.k / 1.25); applyView(); });
document.getElementById('zoom-fit').addEventListener('click', () => {
    if (!state.nodes.length) { view.x = 0; view.y = 0; view.k = 1; applyView(); return; }
    const r = svg.getBoundingClientRect();
    const xs = state.nodes.map((n) => [n.x - n.w / 2, n.x + n.w / 2]).flat();
    const ys = state.nodes.map((n) => [n.y - n.h / 2, n.y + n.h / 2]).flat();
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const k = Math.min(r.width / (maxX - minX + 120), r.height / (maxY - minY + 120));
    view.k = Math.max(0.15, Math.min(2, k));
    view.x = r.width / 2 - ((minX + maxX) / 2) * view.k;
    view.y = r.height / 2 - ((minY + maxY) / 2) * view.k;
    applyView();
});

// ---------- actions ----------
document.getElementById('btn-undo').addEventListener('click', undo);
document.getElementById('btn-redo').addEventListener('click', redo);
document.getElementById('btn-del').addEventListener('click', deleteSel);
document.getElementById('btn-new').addEventListener('click', clearAll);

// ---------- export / import ----------
const modal = document.getElementById('modal');
const modalText = document.getElementById('modal-text');
const modalTitle = document.getElementById('modal-title');

function exportData() {
    return {
        nodes: state.nodes.map((n) => [n.id, n.label, n.shape, n.color, Math.round(n.x), Math.round(n.y), Math.round(n.w), Math.round(n.h)]),
        edges: state.edges.map((e) => [e.from, e.to, e.label, (e.points || []).map((p) => [Math.round(p.x), Math.round(p.y)])]),
    };
}

function showModal(mode) {
    const isExport = mode === 'export';
    modalTitle.textContent = isExport ? 'Export JSON' : 'Paste JSON to import';
    modalText.readOnly = isExport;
    modalText.value = isExport ? JSON.stringify(exportData(), null, 2) : '';
    document.getElementById('modal-copy').style.display = isExport ? '' : 'none';
    document.getElementById('modal-download').style.display = isExport ? '' : 'none';
    document.getElementById('modal-import').style.display = isExport ? 'none' : '';
    modal.hidden = false;
    modalText.focus();
    if (!isExport) modalText.select();
}

function hideModal() { modal.hidden = true; }

function importData(text) {
    let data;
    try { data = JSON.parse(text); } catch (err) { alert('Invalid JSON: ' + err.message); return; }
    if (!Array.isArray(data.nodes) || !Array.isArray(data.edges)) { alert('Expected {"nodes":[...],"edges":[...]}'); return; }
    pushUndo();
    state.nodes = [];
    state.edges = [];
    state.seq = 1;
    state.seqEdge = 0;
    let gridCol = 0, gridRow = 0;
    data.nodes.forEach((t) => {
        const [id, label = '', shape = 'rect', color = '#ffffff', x = gridCol, y = gridRow, w = 150, h = 70] = t;
        state.nodes.push({ id: String(id), label, shape, color, x, y, w, h });
        gridCol += w + 60;
        if (gridCol > 1600) { gridCol = 0; gridRow += h + 80; }
    });
    data.edges.forEach((t) => state.edges.push({
        id: 'e' + state.seqEdge++,
        from: String(t[0]),
        to: String(t[1]),
        label: t[2] || '',
        points: Array.isArray(t[3]) ? t[3].map((p) => ({ x: p[0], y: p[1] })) : [],
    }));
    state.sel = null;
    render();
    setStatus('Imported ' + state.nodes.length + ' nodes, ' + state.edges.length + ' edges');
}

document.getElementById('btn-export').addEventListener('click', () => showModal('export'));
document.getElementById('btn-paste').addEventListener('click', () => showModal('import'));
document.getElementById('modal-close').addEventListener('click', hideModal);
modal.addEventListener('click', (e) => { if (e.target === modal) hideModal(); });
document.getElementById('modal-import').addEventListener('click', () => { importData(modalText.value); hideModal(); });
document.getElementById('modal-copy').addEventListener('click', async () => {
    await navigator.clipboard.writeText(modalText.value);
    setStatus('Copied to clipboard');
});
document.getElementById('modal-download').addEventListener('click', () => {
    const blob = new Blob([modalText.value], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'graph.json';
    a.click();
    URL.revokeObjectURL(a.href);
});
document.getElementById('btn-import').addEventListener('click', () => document.getElementById('file-input').click());
document.getElementById('file-input').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => importData(reader.result);
    reader.readAsText(file);
    e.target.value = '';
});

// ---------- color swatches ----------
const swatchBox = document.getElementById('swatches');
PALETTE.forEach((c) => {
    const d = document.createElement('div');
    d.className = 'swatch';
    d.dataset.color = c;
    d.style.background = c;
    d.title = c;
    d.addEventListener('click', () => setFill(c));
    swatchBox.appendChild(d);
});
document.getElementById('fill-input').addEventListener('input', (e) => setFill(e.target.value));
document.querySelectorAll('.swatch').forEach((s) => s.classList.toggle('active', s.dataset.color === '#ffffff'));

// ---------- init ----------
function loadSaved() {
    try {
        const raw = localStorage.getItem(LS_KEY);
        if (!raw) return;
        const data = JSON.parse(raw);
        if (Array.isArray(data.nodes) && Array.isArray(data.edges)) {
            state.nodes = data.nodes;
            state.edges = data.edges;
            state.seq = state.nodes.reduce((m, n) => { const k = parseInt(n.id.slice(1), 10); return Number.isFinite(k) && k >= m ? k + 1 : m; }, 1);
            state.seqEdge = state.edges.reduce((m, e) => { const k = parseInt(e.id.slice(1), 10); return Number.isFinite(k) && k >= m ? k + 1 : m; }, 0);
        }
    } catch (e) { /* ignore */ }
}

loadSaved();
render();
setStatus('Ready — double-click a node/edge to edit text');
setTool('select');