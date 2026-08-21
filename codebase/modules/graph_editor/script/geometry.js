import { state, nodeById, edgeById, edgesG } from './core.js';

export function boundaryPoint(n, tx, ty) {
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

export function edgePolyline(a, b, waypoints) {
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

export function polylineD(pts) {
    return 'M ' + pts.map((p) => `${p.x},${p.y}`).join(' L ');
}

export function polylineMid(pts) {
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

export function edgeMid(a, b, points) {
    if (a.id === b.id) return { x: a.x, y: a.y - a.h / 2 - 20 };
    return polylineMid(edgePolyline(a, b, points));
}

export function hitNode(x, y) {
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

export function hitResize(x, y) {
    const n = nodeById(state.sel && state.sel.type === 'node' ? state.sel.id : '');
    if (!n) return null;
    const rx = n.w / 2, ry = n.h / 2;
    return x >= n.x + rx - 8 && x <= n.x + rx + 2 && y >= n.y + ry - 8 && y <= n.y + ry + 2 ? n : null;
}

export function hitEdge(x, y) {
    const paths = edgesG.querySelectorAll('.edge-hit');
    const pt = new DOMPoint(x, y);
    for (let i = paths.length - 1; i >= 0; i--) {
        if (paths[i].isPointInStroke(pt)) {
            return edgeById(paths[i].closest('.edge').dataset.id);
        }
    }
    return null;
}