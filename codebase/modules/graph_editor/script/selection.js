import { state, nodesG, edgesG, nodeById, isSel, SVG_NS, refInput, btnOpenRef, btnNavBack, navStack } from './core.js';

export function updateSelectionUI() {
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
    updateRefUI();
}

export function updateRefUI() {
    const n = state.sel && state.sel.type === 'node' ? nodeById(state.sel.id) : null;
    if (n && n.ref && ![...refInput.options].some((o) => o.value === n.ref)) {
        const opt = document.createElement('option');
        opt.value = n.ref;
        opt.textContent = n.ref;
        refInput.appendChild(opt);
    }
    refInput.value = n ? (n.ref || '') : '';
    btnOpenRef.disabled = !n || !n.ref;
    btnNavBack.disabled = !navStack.length;
}