(function () {
    "use strict";

    const SIGNS = [
        { name: "Aries", color: "#a04a6e" },
        { name: "Taurus", color: "#b08a3e" },
        { name: "Gemini", color: "#5f8fd3" },
        { name: "Cancer", color: "#7fb3b8" },
        { name: "Leo", color: "#f7c948" },
        { name: "Virgo", color: "#5f8fd3" },
        { name: "Libra", color: "#b08a3e" },
        { name: "Scorpio", color: "#a04a6e" },
        { name: "Sagittarius", color: "#4f9e84" },
        { name: "Capricorn", color: "#5a6ab0" },
        { name: "Aquarius", color: "#5a6ab0" },
        { name: "Pisces", color: "#4f9e84" },
    ];

    // Planet metadata; real geocentric lon is computed live; frac fixes radial band.
    const PLANETS = [
        { name: "Moon", body: "Moon", label: "Mo", color: "#c9d1d9", frac: 0.30 },
        { name: "Mercury", body: "Mercury", label: "Me", color: "#d7a95f", frac: 0.38 },
        { name: "Venus", body: "Venus", label: "Ve", color: "#e6c07b", frac: 0.45 },
        { name: "Sun", body: "Sun", label: "Su", color: "#f0c060", frac: 0.50 },
        { name: "Mars", body: "Mars", label: "Ma", color: "#e06c5f", frac: 0.58 },
        { name: "Jupiter", body: "Jupiter", label: "Ju", color: "#d3b25f", frac: 0.66 },
        { name: "Saturn", body: "Saturn", label: "Sa", color: "#d9c88a", frac: 0.74 },
        { name: "Uranus", body: "Uranus", label: "Ur", color: "#8fd3d9", frac: 0.82 },
        { name: "Neptune", body: "Neptune", label: "Ne", color: "#5f8fd3", frac: 0.90 },
        { name: "Pluto", body: "Pluto", label: "Pl", color: "#b48bd6", frac: 0.97 },
    ];

    const ROT_DEG = 15; // clockwise rotation of the whole chart; add +N for N° clockwise
    const SUBS = ["A", "B", "C", "D"]; // concentric bands, center -> outer
    const subsections = {}; // cell key "1A" -> color; unset falls back to sector color

    const NAKSHATRAS = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
    ];

    const cv = document.getElementById("chart");
    const ctx = cv.getContext("2d");
    const tooltip = document.getElementById("tooltip");
    const readout = document.getElementById("readout");

    let cx = 0, cy = 0, R = 0, planetPts = [], positions = [];
let showKundali = true;
let showNakshatraNames = true;
let dragMode = false;
let dragging = null;

    // Fallback sample positions (realistic geocentric values) if CDN library is unreachable.
    const FALLBACK_POSITIONS = [
        { lon: 215, au: 0.0026 }, { lon: 118, au: 1.04 }, { lon: 182, au: 0.74 },
        { lon: 136, au: 1.01 }, { lon: 88, au: 1.97 }, { lon: 129, au: 6.29 },
        { lon: 15, au: 8.88 }, { lon: 65, au: 19.76 }, { lon: 4, au: 29.2 }, { lon: 304, au: 34.6 },
    ];

    function computePositions() {
        const now = new Date();
        if (typeof Astronomy === "undefined") {
            positions = PLANETS.map((p, i) => ({ ...p, ...FALLBACK_POSITIONS[i] }));
            readout.textContent = "CDN unavailable \u2014 showing static sample positions";
            return;
        }
        positions = PLANETS.map((p, i) => {
            try {
                const vec = Astronomy.GeoVector(Astronomy.Body[p.body], now, true);
                const ecl = Astronomy.Ecliptic(vec);
                const au = Math.hypot(vec.x, vec.y, vec.z);
                return { ...p, lon: ((ecl.elon % 360) + 360) % 360, au };
            } catch (e) {
                return { ...p, ...FALLBACK_POSITIONS[i] };
            }
        });
        readout.textContent = "Positions for " + now.toUTCString();
    }

    function polar(lonDeg, radiusFrac) {
        const rad = (270 + ROT_DEG - lonDeg) * Math.PI / 180;
        return { x: cx + radiusFrac * Math.cos(rad), y: cy + radiusFrac * Math.sin(rad) };
    }

    function draw() {
        const dpr = window.devicePixelRatio || 1;
        const size = cv.parentElement.clientWidth;
        cv.width = size * dpr;
        cv.height = size * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, size, size);

        cx = size / 2;
        cy = size / 2;
        R = size / 2 - 44;

        drawSectors();
        drawRings();
        drawNakshatras();
        if (showKundali) drawKundali();
        drawEarth();
        drawPlanets();
    }

    function drawSectors() {
        for (let i = 0; i < 12; i++) {
            const s0 = (270 + ROT_DEG - (i + 1) * 30) * Math.PI / 180;
            const s1 = (270 + ROT_DEG - i * 30) * Math.PI / 180;
            for (let j = 0; j < 4; j++) {
                const r0 = R * j / 4;
                const r1 = R * (j + 1) / 4;
                const key = (i + 1) + SUBS[j];
                ctx.beginPath();
                ctx.arc(cx, cy, r1, s0, s1);
                ctx.arc(cx, cy, r0, s1, s0, true);
                ctx.closePath();
                ctx.fillStyle = subsections[key] || SIGNS[i].color;
                ctx.globalAlpha = 0.18;
                ctx.fill();
                ctx.globalAlpha = 1;
                ctx.strokeStyle = "#2f3540";
                ctx.lineWidth = 1;
                ctx.stroke();
            }

            const mid = (270 + ROT_DEG - (i + 0.5) * 30) * Math.PI / 180;
            ctx.fillStyle = SIGNS[i].color;
            ctx.font = "12px 'Segoe UI', Arial";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(SIGNS[i].name, cx + (R - 30) * Math.cos(mid), cy + (R - 30) * Math.sin(mid));
        }
    }

    function drawRings() {
        for (let i = 1; i <= 4; i++) {
            ctx.beginPath();
            ctx.arc(cx, cy, R * i / 4, 0, Math.PI * 2);
            ctx.strokeStyle = "#21262d";
            ctx.lineWidth = 1;
            ctx.stroke();
        }
        ctx.beginPath();
        ctx.arc(cx, cy, R * 0.82, 0, Math.PI * 2);
        ctx.strokeStyle = "#2f3540";
        ctx.lineWidth = 1;
        ctx.stroke();
    }

    function drawNakshatras() {
        const r0 = R * 0.84;
        const r1 = R * 0.99;
        const tickR = R * 1.0;
        const span = 360 / NAKSHATRAS.length;
        for (let k = 0; k < NAKSHATRAS.length; k++) {
            const lon0 = k * span;
            const midLon = (k + 0.5) * span;
            const p0 = polar(lon0, r0 / R);
            const p1 = polar(lon0, r1 / R);
            ctx.beginPath();
            ctx.moveTo(p0.x, p0.y);
            ctx.lineTo(p1.x, p1.y);
            ctx.strokeStyle = "#2f3540";
            ctx.lineWidth = 1;
            ctx.stroke();

            const pt0 = polar(lon0, (r1 - 2) / R);
            const pt1 = polar(lon0, tickR / R);
            ctx.beginPath();
            ctx.moveTo(pt0.x, pt0.y);
            ctx.lineTo(pt1.x, pt1.y);
            ctx.strokeStyle = "#e6edf3";
            ctx.lineWidth = 1.5;
            ctx.stroke();

            const ang = (270 + ROT_DEG - midLon) * Math.PI / 180;
            const midR = (r0 + r1) / 2;
            if (showNakshatraNames) {
                ctx.save();
                ctx.translate(cx, cy);
                ctx.rotate(ang);
                ctx.fillStyle = "#c9d1d9";
                ctx.font = "9px 'Segoe UI', Arial";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                if (Math.cos(ang) < 0) {
                    ctx.rotate(Math.PI);
                    ctx.fillText(NAKSHATRAS[k], -midR, 0);
                } else {
                    ctx.fillText(NAKSHATRAS[k], midR, 0);
                }
                ctx.restore();
            }
        }
    }

    function drawKundali() {
        // Square corners (bounding box of circle) — reserve canvas margin for outside labels.
        const sw = R; // square half-width, circle inscribed
        const A = { x: cx - sw, y: cy - sw };
        const B = { x: cx + sw, y: cy - sw };
        const C = { x: cx + sw, y: cy + sw };
        const D = { x: cx - sw, y: cy + sw };
        // Diamond corners (edge midpoints of the square).
        const E = { x: cx, y: cy - sw };
        const F = { x: cx + sw, y: cy };
        const G = { x: cx, y: cy + sw };
        const H = { x: cx - sw, y: cy };

        ctx.strokeStyle = "#5a6572";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(A.x, A.y);
        ctx.lineTo(B.x, B.y);
        ctx.lineTo(C.x, C.y);
        ctx.lineTo(D.x, D.y);
        ctx.closePath();
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(A.x, A.y);
        ctx.lineTo(C.x, C.y);
        ctx.moveTo(B.x, B.y);
        ctx.lineTo(D.x, D.y);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(E.x, E.y);
        ctx.lineTo(F.x, F.y);
        ctx.lineTo(G.x, G.y);
        ctx.lineTo(H.x, H.y);
        ctx.closePath();
        ctx.stroke();

        ctx.fillStyle = "#ffffff";
        ctx.font = "13px 'Segoe UI', Arial";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        const off = 22;
        const sq = [
            { label: "A", x: A.x - off, y: A.y - off },
            { label: "B", x: B.x + off, y: B.y - off },
            { label: "C", x: C.x + off, y: C.y + off },
            { label: "D", x: D.x - off, y: D.y + off },
        ];
        for (const c of sq) ctx.fillText(c.label, c.x, c.y);
        const dm = [
            { label: "E", x: E.x, y: E.y - off },
            { label: "F", x: F.x + off, y: F.y },
            { label: "G", x: G.x, y: G.y + off },
            { label: "H", x: H.x - off, y: H.y },
        ];
        for (const c of dm) ctx.fillText(c.label, c.x, c.y);
    }

    function drawEarth() {
        ctx.beginPath();
        ctx.arc(cx, cy, 7, 0, Math.PI * 2);
        ctx.fillStyle = "#58a6ff";
        ctx.fill();
        ctx.strokeStyle = "#0d1117";
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.fillStyle = "#e6edf3";
        ctx.font = "11px 'Segoe UI', Arial";
        ctx.textAlign = "center";
        ctx.fillText("Earth", cx, cy + 20);
    }

    function drawPlanets() {
        planetPts = [];
        for (const p of positions) {
            const pt = polar(p.lon, p.frac * R);
            planetPts.push({ x: pt.x, y: pt.y, p });

            ctx.beginPath();
            ctx.arc(pt.x, pt.y, 10, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.globalAlpha = 0.25;
            ctx.fill();
            ctx.globalAlpha = 1;

            ctx.beginPath();
            ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.fill();
            ctx.strokeStyle = "#0d1117";
            ctx.lineWidth = 1;
            ctx.stroke();

            ctx.fillStyle = p.color;
            ctx.font = "11px 'Segoe UI', Arial";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(p.label, pt.x, pt.y + 18);

            const degInSign = ((p.lon % 30) + 30) % 30;
            ctx.font = "10px 'Segoe UI', Arial";
            ctx.fillStyle = "#8b949e";
            ctx.fillText(degInSign.toFixed(1) + "\u00B0", pt.x, pt.y - 16);
        }
    }

    function signOf(lonDeg) {
        return SIGNS[Math.floor(((lonDeg % 360) + 360) % 360 / 30)].name;
    }

    function validKey(k) {
        return /^([1-9]|10|11|12)[A-D]$/.test(k);
    }

    function saveSubsections() {
        fetch("/api/subsections", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ subsections }),
        }).catch((e) => {});
    }

    function fillSubsection(key, color) {
        if (!validKey(key)) throw new Error("Invalid cell key (expected e.g. 1A .. 12D): " + key);
        subsections[key] = color;
        draw();
        saveSubsections();
        return "filled " + key + " with " + color;
    }

    function resetSubsection(key) {
        if (!validKey(key)) throw new Error("Invalid cell key (expected e.g. 1A .. 12D): " + key);
        delete subsections[key];
        draw();
        saveSubsections();
        return "reset " + key;
    }

    function setSubsections(obj, redraw) {
        for (const k of Object.keys(obj)) if (!validKey(k)) throw new Error("Invalid cell key: " + k);
        for (const k of Object.keys(obj)) subsections[k] = obj[k];
        if (redraw !== false) draw();
        saveSubsections();
        return "set " + Object.keys(obj).length + " cells";
    }

    async function hydrateSubsections() {
        try {
            const res = await fetch("/api/subsections");
            if (!res.ok) return;
            const data = await res.json();
            if (data && data.subsections) {
                for (const [k, v] of Object.entries(data.subsections)) {
                    if (validKey(k)) subsections[k] = v;
                }
                draw();
            }
        } catch (e) { /* keep defaults */ }
    }

    window.fillSubsection = fillSubsection;
    window.resetSubsection = resetSubsection;
    window.setSubsections = setSubsections;

    function lonFromXY(mx, my) {
        const rad = Math.atan2(my - cy, mx - cx);
        const lon = 270 + ROT_DEG - rad * 180 / Math.PI;
        return ((lon % 360) + 360) % 360;
    }

    function onMouseDown(ev) {
        if (!dragMode) return;
        const rect = cv.getBoundingClientRect();
        const mx = ev.clientX - rect.left;
        const my = ev.clientY - rect.top;
        const found = planetPts.find(({ x, y }) => Math.hypot(mx - x, my - y) < 22);
        if (found) dragging = positions.find((q) => q === found.p);
    }

    function onMouseMove(ev) {
        const rect = cv.getBoundingClientRect();
        const mx = ev.clientX - rect.left;
        const my = ev.clientY - rect.top;
        if (dragging) {
            dragging.lon = lonFromXY(mx, my);
            readout.textContent = dragging.name + " \u2014 " + signOf(dragging.lon) + ", " + dragging.lon.toFixed(1) + "\u00B0 (dragged)";
            draw();
            return;
        }
        if (!dragMode) {
            readout.textContent = "Hover a planet";
            return;
        }
        const hovered = planetPts.find(({ x, y }) => Math.hypot(mx - x, my - y) < 22);
        readout.textContent = hovered ? hovered.p.name + " \u2014 " + signOf(hovered.p.lon) + ", " + hovered.p.lon.toFixed(1) + "\u00B0" : "Hover a planet";
    }

    function onMouseUp() {
        dragging = null;
        readout.textContent = "Hover a planet";
    }

    function onMouseLeave() {
        dragging = null;
        tooltip.hidden = true;
        readout.textContent = "Hover a planet";
    }

    function initPanel() {
        const selSector = document.getElementById("sel-sector");
        const selBand = document.getElementById("sel-band");
        const selColor = document.getElementById("sel-color");
        const panelStatus = document.getElementById("panel-status");
        for (let i = 0; i < 12; i++) {
            const opt = new Option(SIGNS[i].name + " (" + (i + 1) + ")", String(i + 1));
            selSector.add(opt);
        }
        for (const s of SUBS) selBand.add(new Option(s, s));
        selSector.value = "1";
        selBand.value = "A";

        document.getElementById("btn-fill").addEventListener("click", () => {
            const key = selSector.value + selBand.value;
            panelStatus.textContent = fillSubsection(key, selColor.value);
        });
        document.getElementById("btn-reset").addEventListener("click", () => {
            const key = selSector.value + selBand.value;
            panelStatus.textContent = resetSubsection(key);
        });
        document.getElementById("chk-kundali").addEventListener("change", (e) => {
            showKundali = e.target.checked;
            draw();
        });
        document.getElementById("chk-nakshatra").addEventListener("change", (e) => {
            showNakshatraNames = e.target.checked;
            draw();
        });
        document.getElementById("chk-drag").addEventListener("change", (e) => {
            dragMode = e.target.checked;
            draw();
        });
    }

    cv.addEventListener("mousedown", onMouseDown);
    cv.addEventListener("mousemove", onMouseMove);
    cv.addEventListener("mouseup", onMouseUp);
    cv.addEventListener("mouseleave", onMouseLeave);
    window.addEventListener("resize", draw);
    initPanel();
    computePositions();
    draw();
    hydrateSubsections();
})();
