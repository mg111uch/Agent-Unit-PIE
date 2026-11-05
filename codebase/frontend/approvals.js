// Approval inbox UI. Token comes from localStorage or the input box; in dev
// (AGENT_SKIP_AUTH=true) an empty token is enough.
const $ = (id) => document.getElementById(id);
const key = () => localStorage.getItem("pie_jwt") || $("jwt").value.trim();

async function api(path, opts = {}) {
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  const token = key();
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(path, { ...opts, headers });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
  return body;
}

function card(item) {
  const el = document.createElement("div");
  el.className = `card tier${item.tier}`;
  const amount = item.amount_paise ? `₹${(item.amount_paise / 100).toFixed(2)}` : "—";
  el.innerHTML = `
    <strong>${item.title || item.action}</strong>
    <div class="meta">tier ${item.tier} · ${item.action} · ${amount} · by ${item.requested_by}
      · due ${item.due_at || "—"}</div>
    <div class="meta">${item.approvals?.length ? "approved by " + item.approvals.join(", ") : "no approvals yet"}</div>
    <div class="row">
      <input placeholder="reason (optional)" size="28">
      <button class="ok">Approve</button>
      <button class="no">Reject</button>
    </div>`;
  const reason = el.querySelector("input");
  const decide = async (decision) => {
    try {
      await api(`/api/economy/approvals/${item.item_id}/decide`, {
        method: "POST",
        body: JSON.stringify({ decision, reason: reason.value.trim() }),
      });
      $("msg").textContent = `${decision}d ${item.item_id}`;
      load();
    } catch (e) {
      $("msg").textContent = e.message;
    }
  };
  el.querySelector(".ok").onclick = () => decide("approve");
  el.querySelector(".no").onclick = () => decide("reject");
  return el;
}

async function load() {
  $("list").textContent = "Loading…";
  try {
    const out = await api("/api/economy/approvals");
    $("who").textContent = out.actor ? `signed in as ${out.actor}` : "";
    $("list").innerHTML = "";
    if (!out.items.length) {
      $("list").innerHTML = '<p class="meta">Nothing waiting. Queue an action via POST /api/economy/approvals.</p>';
      return;
    }
    out.items.forEach((i) => $("list").appendChild(card(i)));
  } catch (e) {
    $("list").innerHTML = `<p class="meta">${e.message}</p>`;
  }
}

$("save").onclick = () => {
  localStorage.setItem("pie_jwt", $("jwt").value.trim());
  load();
};
$("refresh").onclick = load;
$("jwt").value = localStorage.getItem("pie_jwt") || "";
load();
