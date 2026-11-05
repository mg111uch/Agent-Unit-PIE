// Customer portal: the token in the URL is the credential. No money moves here;
// accepting issues an invoice, and an operator records the bank/UPI payment.
const token = location.pathname.split("/").filter(Boolean).pop();
const $ = (id) => document.getElementById(id);

function render(p) {
  $("status").textContent = p.status;
  $("title").textContent = p.title || "Proposal";
  $("customer").textContent = p.customer || "";
  $("price").textContent = `${p.currency === "INR" ? "₹" : ""}${Number(p.price).toLocaleString()}`;
  const actions = $("actions");
  actions.innerHTML = "";

  if (p.status === "sent") {
    const b = document.createElement("button");
    b.textContent = "Accept proposal";
    b.onclick = accept;
    actions.appendChild(b);
    return;
  }
  if (p.invoice_id) {
    $("invoice").hidden = false;
    $("invoice").innerHTML = `<strong>Invoice ${p.invoice_id}</strong>
      <p class="meta">${p.payment_instructions || "Pay by bank/UPI against the invoice number."}</p>`;
  }
  if (p.download_available) {
    const a = document.createElement("a");
    a.href = `/api/portal/${encodeURIComponent(token)}/download`;
    a.textContent = "Download deliverable";
    actions.appendChild(a);
  } else {
    $("msg").textContent = p.status === "paid"
      ? "Payment recorded. The deliverable will appear here once assembled."
      : "Deliverable is being assembled; this page will show it when ready.";
  }
}

async function accept() {
  $("msg").textContent = "Accepting…";
  const res = await fetch(`/api/portal/${encodeURIComponent(token)}/accept`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    $("msg").className = "err";
    $("msg").textContent = body.detail || `HTTP ${res.status}`;
    return;
  }
  $("msg").className = "ok";
  $("msg").textContent = "Accepted. Invoice issued — pay by bank/UPI.";
  render(body.proposal);
}

fetch(`/api/portal/${encodeURIComponent(token)}`)
  .then(async (res) => {
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
    return body;
  })
  .then((p) => {
    $("msg").textContent = "";
    render(p);
  })
  .catch((e) => {
    $("status").textContent = "unavailable";
    $("msg").className = "err";
    $("msg").textContent = e.message;
  });
