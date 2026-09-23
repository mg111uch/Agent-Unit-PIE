async function post(url, data) {
  const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: new URLSearchParams(data) });
  if (!r.ok) alert("save failed"); location.reload();
}

// one editor box per topic: click item to load, act via bar below box
document.querySelectorAll(".topic").forEach(sec => {
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
});

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
document.querySelectorAll(".topic").forEach(sec => {
  const tid = sec.dataset.topic;
  const inner = sec.querySelectorAll("details[data-sec]");
  const map = [["t:" + tid, sec]];
  inner.forEach(d => map.push([`t:${tid}:` + d.dataset.sec, d]));
  map.forEach(([k, d]) => { if (k in openState) d.open = openState[k]; });
});
{ // accordion on load: keep first open topic only
  const open = [...document.querySelectorAll(".topic")].filter(s => s.open);
  open.slice(1).forEach(s => { s.open = false; openState["t:" + s.dataset.topic] = false; });
  saveOpen();
}
document.addEventListener("toggle", e => {
  const d = e.target;
  if (!(d instanceof HTMLDetailsElement)) return;
  if (d.classList.contains("topic")) {
    openState["t:" + d.dataset.topic] = d.open;
    if (d.open) document.querySelectorAll(".topic").forEach(o => { // accordion: one topic at a time
      if (o !== d && o.open) { o.open = false; openState["t:" + o.dataset.topic] = false; }
    });
  }
  else if (d.dataset.sec) openState[`t:${d.closest(".topic").dataset.topic}:` + d.dataset.sec] = d.open;
  else return;
  saveOpen();
}, true);

function hookSort() {
  document.querySelectorAll(".lst").forEach(el => {
    if (el._s) return; el._s = 1;
    new Sortable(el, { group: "planner", handle: ".grip", animation: 150,
      onEnd: async e => {
        await fetch("/api/move", { method: "PUT", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: +e.item.dataset.id, status: e.to.dataset.status, index: e.newIndex }) });
        location.reload();
      } });
  });
}
hookSort();
