import {
    state, view, svg, labelEditor, PALETTE, swatchBox, applyView, toWorld, toScreen,
    setStatus, nodeById, edgeById, gesture, drawing, setGesture, setDrawing,
} from './core.js';
import { hitNode, hitResize, hitEdge, edgeMid } from './geometry.js';
import { render, renderOverlay } from './render.js';
import { pushUndo, undo, redo, deleteSel, clearAll, addNode, addEdge, setFill } from './mutations.js';
import { updateSelectionUI } from './selection.js';

// ---------- tool selection ----------
export function setTool(tool) {
    if (tool !== 'edge' && drawing) { setDrawing(null); render(); }
    state.tool = tool;
    document.querySelectorAll('#tools .tool').forEach((b) => b.classList.toggle('active', b.dataset.tool === tool));
    const names = { select: 'Select', pan: 'Pan', rect: 'Square', diamond: 'Diamond', ellipse: 'Oval', edge: 'Edge' };
    setStatus(names[tool] + ' tool active');
}

document.querySelectorAll('#tools .tool').forEach((b) => b.addEventListener('click', () => setTool(b.dataset.tool)));

// ---------- label editing ----------
export function openLabelEditor(type, id) {
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

export function commitLabel() {
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

// ---------- mouse interaction ----------
svg.addEventListener('mousedown', (e) => {
    if (state.editing) return;

    if (e.button === 1 || state.tool === 'pan') {
        e.preventDefault();
        setGesture({ mode: 'pan', sx: e.clientX, sy: e.clientY, ox: view.x, oy: view.y });
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
        setGesture({ mode: 'resize', node: rs, sx: w.x, sy: w.y, ow: rs.w, oh: rs.h });
        pushUndo();
        return;
    }

    if (node) {
        state.sel = { type: 'node', id: node.id };
        setGesture({ mode: 'drag', node, sx: w.x, sy: w.y });
        pushUndo();
        updateSelectionUI();
        return;
    }

    const edge = hitEdge(w.x, w.y);
    if (edge) {
        state.sel = { type: 'edge', id: edge.id };
        setGesture({ mode: 'select-edge', sx: e.clientX, sy: e.clientY, moved: false });
        updateSelectionUI();
        return;
    }

    state.sel = null;
    setGesture({ mode: 'pan', sx: e.clientX, sy: e.clientY, ox: view.x, oy: view.y });
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
    setGesture(null);
    svg.classList.remove('panning');
});

svg.addEventListener('click', (e) => {
    if (state.tool !== 'edge' || state.editing) return;
    const w = toWorld(e.clientX, e.clientY);
    const node = hitNode(w.x, w.y);
    if (!drawing) {
        if (!node) return;
        setDrawing({ from: node.id, points: [], cursor: w });
        state.sel = { type: 'node', id: node.id };
        render();
        setStatus('Edge drawing: click canvas to add points, click a node to finish, Esc to cancel');
    } else if (node) {
        addEdge(drawing.from, node.id, drawing.points);
        setDrawing(null);
        render();
    } else {
        drawing.points.push({ x: w.x, y: w.y });
        render();
    }
});

svg.addEventListener('contextmenu', (e) => {
    if (!drawing) return;
    e.preventDefault();
    setDrawing(null);
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
    if (e.key === 'Escape' && drawing) { setDrawing(null); render(); setStatus('Edge drawing cancelled'); return; }
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

// ---------- color swatches ----------
PALETTE.forEach((c) => {
    const d = document.createElement('div');
    d.className = 'swatch';
    d.dataset.color = c;
    d.style.background = c;
    d.title = c;
    d.addEventListener('click', () => setFill(c));
    swatchBox.appendChild(d);
});
document.querySelectorAll('.swatch').forEach((s) => s.classList.toggle('active', s.dataset.color === '#ffffff'));