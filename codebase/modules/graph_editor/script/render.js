import { state, nodesG, edgesG, overlay, nodeById, isSel, drawing, esc } from './core.js';
import { edgePolyline, polylineD, edgeMid, boundaryPoint } from './geometry.js';
import { updateRefUI } from './selection.js';
import { updateMdUI } from './md_link.js';

export function labelTspans(text, lineH) {
    const lines = String(text).split('\n');
    return lines.map((ln, i) =>
        `<tspan x="0" dy="${i === 0 ? -(lines.length - 1) * lineH / 2 : lineH}" dominant-baseline="middle" text-anchor="middle">${esc(ln) || ' '}</tspan>`
    ).join('');
}

export function nodeText(n) {
    const base = n.label ? String(n.label).split('\n') : [];
    const withRef = n.ref ? base.concat([n.ref]) : base;
    let mdLines = [];
    if (n.mdRef) {
        const raw = String(n.mdRef);
        const hashIdx = raw.indexOf('#');
        if (hashIdx === -1) {
            mdLines = ['\uD83D\uDCC4 ' + raw];
        } else {
            const filePart = raw.slice(0, hashIdx);
            const slugPart = raw.slice(hashIdx + 1);
            const fileName = filePart.split('/').pop() || filePart;
            mdLines.push('\uD83D\uDCC4 ' + fileName);
            if (slugPart) mdLines.push('#' + slugPart);
        }
    }
    const all = mdLines.length ? withRef.concat(mdLines) : withRef;
    const hasRef = !!n.ref;
    const hasMd = mdLines.length > 0;
    const mdStart = withRef.length;
    return all.map((ln, i) => {
        const total = all.length;
        const dy = i === 0 ? -(total - 1) * 12 / 2 : 12;
        let cls = '';
        if (hasMd && i >= mdStart) cls = ' class="md-caption"';
        else if (hasRef && i === mdStart - 1) cls = ' class="ref-caption"';
        return `<tspan x="0" dy="${dy}" dominant-baseline="middle" text-anchor="middle"${cls}>${esc(ln) || ' '}</tspan>`;
    }).join('');
}

export function render() {
    nodesG.innerHTML = state.nodes.map((n) => {
        const rx = n.w / 2, ry = n.h / 2;
        let body;
        if (n.shape === 'rect') body = `<rect x="${-rx}" y="${-ry}" width="${n.w}" height="${n.h}" rx="5" fill="${n.color}"/>`;
        else if (n.shape === 'ellipse') body = `<ellipse cx="0" cy="0" rx="${rx}" ry="${ry}" fill="${n.color}"/>`;
        else body = `<polygon points="0,${-ry} ${rx},0 0,${ry} ${-rx},0" fill="${n.color}"/>`;
        const hasLabel = String(n.label ?? '').trim() !== '' || !!n.ref || !!n.mdRef;
        const label = hasLabel ? `<text class="label">${nodeText(n)}</text>` : '';
        const sel = isSel('node', n.id);
        const handle = sel ? `<rect class="resize" x="${rx - 7}" y="${ry - 7}" width="10" height="10"/>` : '';
        const refMark = n.ref ? (n.shape === 'rect' ? `<rect class="ref-ring" x="${-rx + 3}" y="${-ry + 3}" width="${n.w - 6}" height="${n.h - 6}" rx="4"/>`
            : n.shape === 'ellipse' ? `<ellipse class="ref-ring" cx="0" cy="0" rx="${rx - 3}" ry="${ry - 3}"/>`
            : `<polygon class="ref-ring" points="${-(rx - 4)},0 0,${-(ry - 4)} ${rx - 4},0 0,${ry - 4}"/>`) : '';
        const mdMark = !n.ref && n.mdRef ? (n.shape === 'rect' ? `<rect class="md-ring" x="${-rx + 3}" y="${-ry + 3}" width="${n.w - 6}" height="${n.h - 6}" rx="4"/>`
            : n.shape === 'ellipse' ? `<ellipse class="md-ring" cx="0" cy="0" rx="${rx - 3}" ry="${ry - 3}"/>`
            : `<polygon class="md-ring" points="${-(rx - 4)},0 0,${-(ry - 4)} ${rx - 4},0 0,${ry - 4}"/>`) : '';
        const bothMark = (n.ref && n.mdRef) ? `<circle class="md-ring" cx="${rx - 8}" cy="${-ry + 8}" r="6" fill="#0d1117"/>` : '';
        return `<g class="node${sel ? ' selected' : ''}" data-id="${n.id}" data-shape="${n.shape}" transform="translate(${n.x},${n.y})">${body}${refMark}${mdMark}${bothMark}${label}${handle}</g>`;
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
    updateRefUI();
    updateMdUI();
}

export function renderOverlay() {
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