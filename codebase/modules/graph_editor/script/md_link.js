import { state, nodeById, setStatus, mdFileInput, mdSectionInput, btnOpenMd, btnClearMd } from './core.js';
import { pushUndo } from './mutations.js';
import { render } from './render.js';

let mdHeadingsCache = {}; // file -> headings[]
let mdFilesLoaded = false;

function slugify(s) {
    return String(s).trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function parseMdRef(mdRef) {
    if (!mdRef) return { file: '', slug: '' };
    const [f, a] = String(mdRef).split('#');
    return { file: f.trim(), slug: (a || '').trim() };
}

function buildMdRef(file, slug) {
    if (!file) return '';
    return slug ? `${file}#${slug}` : file;
}

async function fetchMdFiles() {
    try {
        const r = await fetch('/api/md_files');
        const j = await r.json();
        if (!j.ok) throw new Error(j.error || 'failed');
        for (const f of (j.files || [])) {
            const opt = document.createElement('option');
            opt.value = f;
            opt.textContent = f;
            mdFileInput.appendChild(opt);
        }
        mdFilesLoaded = true;
    } catch {}
}

async function fetchHeadings(file) {
    if (!file) return [];
    if (mdHeadingsCache[file]) return mdHeadingsCache[file];
    try {
        const r = await fetch('/api/md_sections?path=' + encodeURIComponent(file));
        const j = await r.json();
        if (!j.ok) throw new Error(j.error);
        mdHeadingsCache[file] = j.headings || [];
        return mdHeadingsCache[file];
    } catch { return []; }
}

async function populateSections(file, selectedSlug) {
    mdSectionInput.innerHTML = '<option value="">— section —</option>';
    if (!file) return;
    const headings = await fetchHeadings(file);
    for (const h of headings) {
        const opt = document.createElement('option');
        opt.value = h.slug;
        opt.textContent = `${'#'.repeat(h.level)} ${h.text}`;
        opt.title = h.text;
        mdSectionInput.appendChild(opt);
    }
    // ensure selected slug present even if heading not found (legacy)
    if (selectedSlug && ![...mdSectionInput.options].some(o => o.value === selectedSlug)) {
        const opt = document.createElement('option');
        opt.value = selectedSlug;
        opt.textContent = selectedSlug;
        mdSectionInput.appendChild(opt);
    }
    mdSectionInput.value = selectedSlug || '';
}

export async function updateMdUI() {
    const n = state.sel && state.sel.type === 'node' ? nodeById(state.sel.id) : null;
    if (!n) {
        mdFileInput.value = '';
        mdSectionInput.innerHTML = '<option value="">— section —</option>';
        btnOpenMd.disabled = true;
        btnClearMd.disabled = true;
        return;
    }
    const { file, slug } = parseMdRef(n.mdRef || '');
    // ensure file option exists if mdRef points to a file not in list
    if (file && ![...mdFileInput.options].some(o => o.value === file)) {
        const opt = document.createElement('option');
        opt.value = file;
        opt.textContent = file;
        mdFileInput.appendChild(opt);
    }
    mdFileInput.value = file || '';
    await populateSections(file, slug);
    const has = !!n.mdRef;
    btnOpenMd.disabled = !has;
    btnClearMd.disabled = !has;
}

async function onFileChange() {
    const n = state.sel && state.sel.type === 'node' ? nodeById(state.sel.id) : null;
    if (!n) return;
    const file = mdFileInput.value.trim();
    // reset slug when file changes
    const newRef = buildMdRef(file, '');
    if (n.mdRef === newRef) {
        await populateSections(file, '');
        return;
    }
    pushUndo();
    n.mdRef = newRef;
    await populateSections(file, '');
    render();
    setStatus(file ? 'Docs file set to ' + file : 'Docs link removed');
    btnOpenMd.disabled = !n.mdRef;
    btnClearMd.disabled = !n.mdRef;
}

async function onSectionChange() {
    const n = state.sel && state.sel.type === 'node' ? nodeById(state.sel.id) : null;
    if (!n) return;
    const file = mdFileInput.value.trim();
    if (!file) { setStatus('Pick a file first'); mdSectionInput.value=''; return; }
    const slug = mdSectionInput.value.trim();
    const newRef = buildMdRef(file, slug);
    if (n.mdRef === newRef) return;
    pushUndo();
    n.mdRef = newRef;
    render();
    setStatus(n.mdRef ? 'Docs section linked: ' + n.mdRef : 'Docs section cleared');
    btnOpenMd.disabled = !n.mdRef;
    btnClearMd.disabled = !n.mdRef;
}

function clearMd() {
    const n = state.sel && state.sel.type === 'node' ? nodeById(state.sel.id) : null;
    if (!n || !n.mdRef) return;
    pushUndo();
    n.mdRef = '';
    mdFileInput.value = '';
    mdSectionInput.innerHTML = '<option value="">— section —</option>';
    render();
    setStatus('Docs link cleared');
    btnOpenMd.disabled = true;
    btnClearMd.disabled = true;
}

async function openMd() {
    const n = state.sel && state.sel.type === 'node' ? nodeById(state.sel.id) : null;
    const target = n ? (n.mdRef || '') : '';
    if (!target) { setStatus('No docs link on this node'); return; }
    try {
        const r = await fetch('/api/md_content?path=' + encodeURIComponent(target));
        const j = await r.json();
        if (!j.ok) throw new Error(j.error);
        const modal = document.getElementById('modal');
        const title = document.getElementById('modal-title');
        const text = document.getElementById('modal-text');
        title.textContent = j.file + (j.anchor ? ' #' + j.anchor : '');
        text.readOnly = true;
        text.value = j.content || '';
        document.getElementById('modal-copy').style.display = '';
        document.getElementById('modal-download').style.display = '';
        document.getElementById('modal-import').style.display = 'none';
        modal.hidden = false;
        text.focus();
        setStatus('Opened ' + target);
    } catch (e) {
        setStatus('Open failed: ' + e.message);
    }
}

// init
fetchMdFiles();
mdFileInput.addEventListener('change', onFileChange);
mdSectionInput.addEventListener('change', onSectionChange);
btnOpenMd.addEventListener('click', openMd);
btnClearMd.addEventListener('click', clearMd);
