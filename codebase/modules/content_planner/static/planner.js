async function post(url, data) {
  const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: new URLSearchParams(data) });
  if (!r.ok) alert("save failed"); location.reload();
}

// one editor box per topic: click item to load, act via bar below box
function wireTopic(sec) {
  if (sec._wired) return;
  sec._wired = 1;
  const tid = sec.dataset.topic;
  const ta = sec.querySelector(".addinput");
  const c = sec.querySelector(".count");
  const bar = sec.querySelector(".ibar");
  const sel = bar.querySelector(".sel");
  const btns = Object.fromEntries([...bar.querySelectorAll("[data-ib]")].map(b => [b.dataset.ib, b]));
  let cur = null; // {id, status}

  const setSel = (id, status) => {
    cur = id ? { id, status } : null;
    sec.querySelectorAll(".it.sel").forEach(x => x.classList.remove("sel"));
    if (cur) sec.querySelector(`.it[data-id="${id}"]`)?.classList.add("sel");
    ["save", "del", "flip", "clear"].forEach(k => btns[k].disabled = !cur);
    sel.textContent = cur ? `#${cur.id} (${cur.status})` : "";
  };
  const loadItem = li => {
    ta.value = li.querySelector(".body").textContent;
    c.textContent = ta.value.length;
    setSel(li.dataset.id, li.closest(".lst").dataset.status);
    ta.focus();
  };
  sec.addEventListener("click", e => {
    if (e.target.closest("button") || e.target.closest("textarea") || e.target.closest("input")) return;
    const li = e.target.closest(".it");
    if (li) loadItem(li);
  });
  ta.addEventListener("input", () => {
    c.textContent = ta.value.length;
    if (!ta.value.trim()) setSel(null);
  });
  ta.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const v = ta.value.trim(); if (!v) return;
      if (cur) post(`/items/${cur.id}/edit`, { body: v });
      else post("/items", { topic_id: tid, body: v, status: "planned" });
    }
    if (e.key === "Escape") { ta.value = ""; c.textContent = "0"; setSel(null); }
  });
  bar.addEventListener("click", e => {
    const b = e.target.closest("[data-ib]"); if (!b || b.disabled) return;
    const v = ta.value.trim();
    if (b.dataset.ib === "add" && v) post("/items", { topic_id: tid, body: v, status: "planned" });
    if (b.dataset.ib === "save" && cur && v) post(`/items/${cur.id}/edit`, { body: v });
    if (b.dataset.ib === "del" && cur && confirm("delete?")) post(`/items/${cur.id}/delete`, {});
    if (b.dataset.ib === "flip" && cur) { const to = cur.status === "planned" ? "done" : "planned"; forceOpen(tid, to); post(`/items/${cur.id}/move`, { status: to }); }
    if (b.dataset.ib === "clear") { ta.value = ""; c.textContent = "0"; setSel(null); ta.focus(); }
  });
}

// shared topic box: click a topic title to load it, act via buttons beside Add
const nt = document.getElementById("newtopic");
const ntInput = nt.name;
const ntSel = nt.querySelector(".tsel");
const ntBtns = Object.fromEntries([...nt.querySelectorAll("[data-tt]")].map(b => [b.dataset.tt, b]));
let curTopic = null; // topic id
const setTopicSel = id => {
  curTopic = id || null;
  document.querySelectorAll(".topic.tsel").forEach(x => x.classList.remove("tsel"));
  if (curTopic) document.querySelector(`.topic[data-topic="${curTopic}"]`)?.classList.add("tsel");
  ["save", "del", "clear"].forEach(k => ntBtns[k].disabled = !curTopic);
  ntSel.textContent = curTopic ? `#${curTopic}` : "";
};
document.querySelectorAll(".topic > .tsum").forEach(sum => {
  sum.addEventListener("click", () => {
    const sec = sum.closest(".topic");
    ntInput.value = sec.querySelector(".tname").textContent;
    setTopicSel(sec.dataset.topic);
    ntInput.focus();
  });
});
ntInput.addEventListener("input", () => { if (!ntInput.value.trim()) setTopicSel(null); });
nt.addEventListener("submit", e => {
  e.preventDefault();
  const v = ntInput.value.trim(); if (!v) return;
  if (curTopic) post(`/topics/${curTopic}/rename`, { name: v }); // Enter saves loaded topic
  else post("/topics", { name: v });
});
nt.addEventListener("click", e => {
  const b = e.target.closest("[data-tt]"); if (!b || b.disabled) return;
  const v = ntInput.value.trim();
  if (b.dataset.tt === "save" && curTopic && v) post(`/topics/${curTopic}/rename`, { name: v });
  if (b.dataset.tt === "del" && curTopic && confirm("delete topic?")) post(`/topics/${curTopic}/delete`, {});
  if (b.dataset.tt === "clear") { ntInput.value = ""; setTopicSel(null); ntInput.focus(); }
});

// keep Planned/Done/topic collapse state across reloads
const LS = "planner_open";
const openState = JSON.parse(localStorage.getItem(LS) || "{}");
const saveOpen = () => localStorage.setItem(LS, JSON.stringify(openState));
function forceOpen(tid, sec) { openState[`t:${tid}:${sec}`] = true; saveOpen(); }
const applySecState = sec => sec.querySelectorAll("details[data-sec]").forEach(d => {
  const k = `t:${sec.dataset.topic}:` + d.dataset.sec;
  if (k in openState) d.open = openState[k];
});

// bodies live only for the open topic; closed ones are fetched on demand and dropped on close
async function ensureBody(sec) {
  if (sec.querySelector(".tbody") || sec._loading) return;
  sec._loading = 1;
  try {
    sec.insertAdjacentHTML("beforeend", await (await fetch(`/api/topic/${sec.dataset.topic}`)).text());
    applySecState(sec);
    wireTopic(sec);
    hookListsIn(sec);
  } catch (e) { console.warn("topic load failed", e); }
  finally { sec._loading = 0; }
}

function dropBody(sec) {
  const b = sec.querySelector(".tbody");
  if (!b) return;
  b.querySelectorAll(".lst").forEach(ul => RO && RO.unobserve(ul));
  b.remove();
}

const setUrl = (v) => {
  const u = new URL(location.href);
  if (v) u.searchParams.set("topic", v); else u.searchParams.delete("topic");
  history.replaceState(null, "", u);
};

const RO = window.ResizeObserver ? new ResizeObserver(es => es.forEach(e => warm(e.target))) : null;

{ // open the topic the last visit used; server already rendered ?topic (or the first one)
  const all = [...document.querySelectorAll(".topic")];
  const shown = all.find(s => s.querySelector(".tbody"));
  if (shown) wireTopic(shown);
  const want = all.find(s => openState["t:" + s.dataset.topic]);
  if (want && want !== shown) { if (shown) shown.open = false; want.open = true; }
  all.forEach(sec => { applySecState(sec); if (!sec.open) dropBody(sec); });
  saveOpen();
}
document.addEventListener("toggle", e => {
  const d = e.target;
  if (!(d instanceof HTMLDetailsElement)) return;
  if (d.classList.contains("topic")) {
    openState["t:" + d.dataset.topic] = d.open;
    if (d.open) {
      ensureBody(d);
      document.querySelectorAll(".topic").forEach(o => { // accordion: one topic at a time
        if (o !== d && o.open) { o.open = false; openState["t:" + o.dataset.topic] = false; }
      });
      setUrl(d.dataset.topic);
    } else {
      dropBody(d);
      if (!document.querySelector(".topic[open]")) setUrl(null);
    }
  }
  else if (d.dataset.sec) openState[`t:${d.closest(".topic").dataset.topic}:` + d.dataset.sec] = d.open;
  else return;
  saveOpen();
}, true);

// ---- scroll viewport + lazy loading: PAGE rows visible, rest fetched on scroll ----
const PAGE = 5;

const mkItem = it => {
  const li = document.createElement("li");
  li.className = "it"; li.dataset.id = it.id; li.title = "click to load in editor";
  const b = document.createElement("span");
  b.className = "body"; b.textContent = it.body;   // textContent: no HTML injection
  li.append(b);
  return li;
};

function lockViewport(ul) {                 // height = first PAGE rows only, so it never grows when more load
  if (ul._locked || +ul.dataset.total <= PAGE || !ul.offsetHeight) return;
  const rows = [...ul.children].slice(0, PAGE);
  if (rows.length < PAGE || rows.some(r => !r.getBoundingClientRect().height)) return;
  const cs = getComputedStyle(ul);
  const h = rows.reduce((a, r) => a + r.getBoundingClientRect().height, 0)
    + parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom)
    + parseFloat(cs.borderTopWidth) + parseFloat(cs.borderBottomWidth);
  ul.classList.add("scroll");
  ul.style.maxHeight = h + "px";
  ul._locked = 1;
}

const relock = () => document.querySelectorAll(".lst").forEach(ul => {
  if (!ul._locked) return;
  ul._locked = 0; lockViewport(ul);
});

function syncMore(ul) {
  const m = ul.nextElementSibling;
  if (!(m && m.classList.contains("more"))) return;
  const left = Math.max(0, +ul.dataset.total - +ul.dataset.offset);
  if (!left) { m.style.display = "none"; return; }
  m.style.display = "";
  m.textContent = ul.dataset.busy ? "loading…" : `scroll (or click) for more · ${left} left`;
}

async function loadMore(ul) {
  const off = +ul.dataset.offset;
  if (ul.dataset.busy || off >= +ul.dataset.total) return;
  ul.dataset.busy = "1"; syncMore(ul);
  try {
    const q = new URLSearchParams({ topic: ul.dataset.topic, status: ul.dataset.status, offset: off, limit: PAGE });
    const d = await (await fetch(`/api/items?${q}`)).json();
    const frag = document.createDocumentFragment();
    (d.items || []).forEach(it => frag.append(mkItem(it)));
    ul.append(frag);                       // loaded rows are always a prefix, so drag index stays correct
    ul.dataset.offset = off + (d.items || []).length;
    ul.dataset.total = Math.max(+ul.dataset.total, d.total || 0);
  } catch (e) { console.warn("lazy load failed", e); }
  finally { delete ul.dataset.busy; syncMore(ul); }
}

// seed one extra slice so the 5-row box actually overflows -> scroll has something to scroll
function warm(ul) {
  if (ul._warmed || !ul.offsetHeight) return;
  ul._warmed = 1;
  lockViewport(ul);
  if (+ul.dataset.offset < +ul.dataset.total) loadMore(ul);
}

function hookListsIn(root) {
  root.querySelectorAll(".lst").forEach(ul => {
    if (ul._hooked) return;
    ul._hooked = 1;
    syncMore(ul);
    ul.addEventListener("scroll", () => {
      if (ul.scrollTop + ul.clientHeight >= ul.scrollHeight - 8) loadMore(ul);
    }, { passive: true });
    const m = ul.nextElementSibling;
    if (m && m.classList.contains("more")) m.addEventListener("click", () => loadMore(ul));
    if (RO) RO.observe(ul);
    warm(ul);
  });
}

hookListsIn(document);
window.addEventListener("resize", relock);
document.fonts?.ready.then(relock).catch(() => {});
