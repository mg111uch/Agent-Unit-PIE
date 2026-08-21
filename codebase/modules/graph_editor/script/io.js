import { state, modal, modalText, modalTitle, statusEl, currentFile, setCurrentFile, setStatus, setDirty, esc, LS_KEY } from './core.js';
import { snapshot, pushUndo } from './mutations.js';
import { render } from './render.js';

export function exportData() {
    return {
        nodes: state.nodes.map((n) => {
            const t = [n.id, n.label, n.shape, n.color, Math.round(n.x), Math.round(n.y), Math.round(n.w), Math.round(n.h)];
            if (n.ref || n.mdRef) t.push(n.ref || '');
            if (n.mdRef) t.push(n.mdRef);
            return t;
        }),
        edges: state.edges.map((e) => [e.from, e.to, e.label, (e.points || []).map((p) => [Math.round(p.x), Math.round(p.y)])]),
    };
}

export function showModal(mode) {
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

export function hideModal() { modal.hidden = true; }

export function importData(text) {
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
        const [id, label = '', shape = 'rect', color = '#ffffff', x = gridCol, y = gridRow, w = 150, h = 70, ref = '', mdRef = ''] = t;
        state.nodes.push({ id: String(id), label, shape, color, x, y, w, h, ref: String(ref || ''), mdRef: String(mdRef || '') });
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

export function save() {
    try { localStorage.setItem(LS_KEY, snapshot()); } catch (e) { /* ignore */ }
}

export async function saveCurrentFile() {
    if (!currentFile) return;
    save();
    try {
        const res = await fetch('/api/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: currentFile, data: exportData() }),
        });
        const out = await res.json();
        if (out.ok) { setStatus('Saved to ' + currentFile); setDirty(false); }
        else setStatus('Save failed: ' + (out.error || 'unknown error'));
    } catch (err) {
        setStatus('Save failed: ' + err.message);
    }
}

document.getElementById('btn-export').addEventListener('click', () => showModal('export'));
document.getElementById('btn-paste').addEventListener('click', () => showModal('import'));
document.getElementById('modal-close').addEventListener('click', hideModal);
modal.addEventListener('click', (e) => { if (e.target === modal) hideModal(); });
document.getElementById('modal-import').addEventListener('click', () => { importData(modalText.value); setCurrentFile(null); hideModal(); });
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
    setCurrentFile(file.name);
    const reader = new FileReader();
    reader.onload = () => {
        importData(reader.result);
        statusEl.innerHTML = esc(currentFile) + '<br>' + state.nodes.length + ' nodes, ' + state.edges.length + ' edges';
    };
    reader.readAsText(file);
    e.target.value = '';
});
document.getElementById('btn-save').addEventListener('click', saveCurrentFile);