function apiBase() {
  if (window.__SOUKLY_ENV__?.apiBase) return window.__SOUKLY_ENV__.apiBase.replace(/\/$/, "");
  const h = location.hostname;
  if (h === "localhost" || h === "127.0.0.1") return "http://127.0.0.1:8787/api";
  return location.origin + "/api";
}
const API = apiBase();
const tokenKey = "soukly_agent_token";
const userKey = "soukly_agent_user";

const $ = (s) => document.querySelector(s);

function authHeaders() {
  const t = localStorage.getItem(tokenKey);
  return t ? { Authorization: `Bearer ${t}`, "Content-Type": "application/json" } : { "Content-Type": "application/json" };
}

async function api(path, opts = {}) {
  const res = await fetch(API + path, { ...opts, headers: { ...authHeaders(), ...(opts.headers || {}) } });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(data.error || res.status), { status: res.status, data });
  return data;
}

function showLogin() {
  $("#login-view").classList.remove("hidden");
  $("#dash-view").classList.add("hidden");
}

function showDash(user) {
  $("#login-view").classList.add("hidden");
  $("#dash-view").classList.remove("hidden");
  $("#user-label").textContent = `${user.name} · ${user.role}`;
}

async function boot() {
  const token = localStorage.getItem(tokenKey);
  if (!token) return showLogin();
  try {
    const me = await api("/me");
    if (!["agent", "admin"].includes(me.role)) {
      localStorage.removeItem(tokenKey);
      return showLogin();
    }
    localStorage.setItem(userKey, JSON.stringify(me));
    showDash(me);
    await loadRequests();
  } catch {
    showLogin();
  }
}

$("#login-btn").onclick = async () => {
  $("#login-err").classList.add("hidden");
  try {
    const data = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ identifier: $("#login-id").value, password: $("#login-pw").value }),
    });
    if (!["agent", "admin"].includes(data.user.role)) {
      $("#login-err").textContent = "This account is not an agent.";
      $("#login-err").classList.remove("hidden");
      return;
    }
    localStorage.setItem(tokenKey, data.token);
    localStorage.setItem(userKey, JSON.stringify(data.user));
    showDash(data.user);
    await loadRequests();
  } catch (e) {
    $("#login-err").textContent = e.data?.error || "Sign in failed";
    $("#login-err").classList.remove("hidden");
  }
};

$("#logout").onclick = async () => {
  try { await api("/auth/logout", { method: "POST", body: "{}" }); } catch {}
  localStorage.removeItem(tokenKey);
  showLogin();
};

async function loadRequests() {
  const list = await api("/agent-requests");
  const el = $("#req-list");
  if (!list.length) {
    el.innerHTML = `<p class="text-slate-500 text-sm">No requests yet. Customer agent requests will appear here.</p>`;
    return;
  }
  el.innerHTML = list.map((r) => `
    <button data-id="${r.id}" class="req-row w-full text-left bg-white rounded-xl border border-slate-200 p-4 hover:border-emerald-300 transition">
      <div class="flex justify-between items-start">
        <div>
          <p class="font-semibold text-emerald-700 text-sm">${r.id}</p>
          <p class="text-sm text-slate-700 mt-0.5">${r.customerName || "Customer"} · ${r.selectedListingIds?.length || 0} properties</p>
          <p class="text-xs text-slate-400 mt-1">${r.createdAt || ""}</p>
        </div>
        <span class="text-[10px] font-bold uppercase tracking-wide bg-emerald-50 text-emerald-800 px-2 py-1 rounded-full">${(r.status || "").replace(/_/g, " ")}</span>
      </div>
    </button>
  `).join("");
  el.querySelectorAll(".req-row").forEach((btn) => {
    btn.onclick = () => openDetail(btn.dataset.id);
  });
}

async function openDetail(id) {
  const r = await api(`/agent-requests/${id}`);
  const detail = $("#req-detail");
  detail.classList.remove("hidden");
  const req = r.requirements || {};
  const reqLines = [
    req.propertyType && `Type: ${req.propertyType}`,
    req.transaction && `Transaction: ${req.transaction}`,
    req.city && `City: ${req.city}`,
    req.neighborhood && `Area: ${req.neighborhood}`,
    req.bedrooms != null && `Bedrooms: ${req.bedrooms}`,
    req.budgetMax && `Budget max: ${req.budgetMax} MAD`,
  ].filter(Boolean);

  const actions = [
    ["OWNER_CONTACTED", "Contact owner"],
    ["AVAILABILITY_CONFIRMED", "Confirm availability"],
    ["VERIFICATION_PENDING", "Verification pending"],
    ["VERIFIED", "Mark verified"],
    ["VIEWING_REQUESTED", "Request viewing"],
    ["VIEWING_CONFIRMED", "Confirm viewing"],
    ["COMPLETED", "Complete request"],
    ["CANCELLED", "Cancel request"],
  ];

  detail.innerHTML = `
    <div class="flex justify-between items-start mb-4">
      <div>
        <p class="text-sm font-semibold text-emerald-700">${r.id}</p>
        <h2 class="text-xl font-bold">${r.customerName || "Customer"}</h2>
        ${r.customerPhone ? `<p class="text-sm text-slate-600">${r.customerPhone}</p>` : ""}
      </div>
      <span class="text-xs font-bold uppercase bg-slate-100 px-2 py-1 rounded-full">${(r.status || "").replace(/_/g, " ")}</span>
    </div>
    <div class="grid md:grid-cols-2 gap-4 mb-4">
      <div class="bg-slate-50 rounded-xl p-3">
        <h3 class="text-xs font-semibold uppercase text-slate-500 mb-2">Requirements</h3>
        <ul class="text-sm space-y-1">${reqLines.map((l) => `<li>${l}</li>`).join("") || "<li class='text-slate-400'>No structured requirements</li>"}</ul>
      </div>
      <div class="bg-slate-50 rounded-xl p-3">
        <h3 class="text-xs font-semibold uppercase text-slate-500 mb-2">Selected properties</h3>
        <ul class="text-sm space-y-1">${(r.selectedListingIds || []).map((id) => `<li><code>${id}</code></li>`).join("")}</ul>
      </div>
    </div>
    <div class="mb-4">
      <h3 class="text-xs font-semibold uppercase text-slate-500 mb-2">Timeline</h3>
      <ol class="space-y-2 border-l-2 border-emerald-200 pl-4">
        ${(r.timeline || []).map((t) => `
          <li>
            <p class="text-sm font-medium">${(t.status || "").replace(/_/g, " ")}</p>
            <p class="text-xs text-slate-500">${t.note || ""} · ${t.at || ""}</p>
          </li>
        `).join("")}
      </ol>
    </div>
    <div class="flex flex-wrap gap-2">
      ${actions.map(([st, label]) => `
        <button class="act px-3 py-2 text-sm font-medium rounded-lg border border-slate-200 bg-white hover:bg-emerald-50"
          data-status="${st}" data-id="${r.id}">${label}</button>
      `).join("")}
    </div>
  `;
  detail.querySelectorAll(".act").forEach((btn) => {
    btn.onclick = async () => {
      await api(`/agent-requests/${btn.dataset.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: btn.dataset.status, note: btn.textContent.trim() }),
      });
      await loadRequests();
      await openDetail(btn.dataset.id);
    };
  });
  detail.scrollIntoView({ behavior: "smooth" });
}

boot();
