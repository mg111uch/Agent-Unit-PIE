import { state, currentFile, navStack, refInput, btnOpenRef, btnNavBack, nodeById, setCurrentFile, setStatus } from './core.js';
import { importData } from './io.js';
import { pushUndo } from './mutations.js';
import { render } from './render.js';
import { updateRefUI } from './selection.js';

fetch('/api/graphs')
    .then((r) => r.json())
    .then((res) => {
        if (!res || res.ok === false) throw new Error((res && res.error) || 'Failed to list graphs');
        (res.graphs || []).forEach((f) => {
            const opt = document.createElement('option');
            opt.value = f;
            opt.textContent = f;
            refInput.appendChild(opt);
        });
        render();
    })
    .catch(() => { /* keep just the none option */ });

refInput.addEventListener('change', () => {
    const n = state.sel && state.sel.type === 'node' ? nodeById(state.sel.id) : null;
    if (!n) return;
    pushUndo();
    n.ref = refInput.value.trim();
    render();
    setStatus(n.ref ? 'Node linked to ' + n.ref : 'Node link removed');
});

export async function importFromUrl(path) {
    const res = await fetch('/api/graph?path=' + encodeURIComponent(path));
    const data = await res.json();
    if (!data || data.ok === false) throw new Error((data && data.error) || 'Failed to load graph');
    if (!Array.isArray(data.nodes) || !Array.isArray(data.edges)) throw new Error('Expected {"nodes":[...],"edges":[...]}');
    importData(JSON.stringify(data));
}

export async function openRefNode() {
    const n = state.sel && state.sel.type === 'node' ? nodeById(state.sel.id) : null;
    if (!n || !n.ref) return;
    if (n.ref === (currentFile || '')) { setStatus('Already viewing ' + n.ref); return; }
    const parent = currentFile;
    try {
        await importFromUrl(n.ref);
        if (parent) navStack.push({ file: parent });
        setCurrentFile(n.ref);
        setStatus('Opened subgraph ' + n.ref + ' — ' + state.nodes.length + ' nodes, ' + state.edges.length + ' edges');
        updateRefUI();
    } catch (err) {
        setStatus('Open failed: ' + err.message);
    }
}

export async function goBack() {
    const prev = navStack.pop();
    if (!prev) return;
    try {
        await importFromUrl(prev.file);
        setCurrentFile(prev.file);
        setStatus('Back to ' + (prev.file || '(unsaved)'));
    } catch (err) {
        setStatus('Back failed: ' + err.message);
    }
}

btnOpenRef.addEventListener('click', openRefNode);
btnNavBack.addEventListener('click', goBack);