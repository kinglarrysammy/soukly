function apiBase() {
  if (window.__SOUKLY_ENV__?.apiBase) return window.__SOUKLY_ENV__.apiBase.replace(/\/$/, "");
  const h = location.hostname;
  if (h === "localhost" || h === "127.0.0.1") return "http://127.0.0.1:8787/api";
  return location.origin + "/api";
}
const API = apiBase();
const tokenKey = "soukly_biz_token";

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
  if (!localStorage.getItem(tokenKey)) return showLogin();
  try {
    const me = await api("/me");
    if (!["business", "admin"].includes(me.role)) {
      localStorage.removeItem(tokenKey);
      return showLogin();
    }
    showDash(me);
    await refresh();
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
    if (!["business", "admin"].includes(data.user.role)) {
      $("#login-err").textContent = "Not a business account.";
      $("#login-err").classList.remove("hidden");
      return;
    }
    localStorage.setItem(tokenKey, data.token);
    showDash(data.user);
    await refresh();
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

async function refresh() {
  const [listings, leads] = await Promise.all([api("/business/listings"), api("/business/leads")]);
  $("#listing-list").innerHTML = listings.length
    ? listings.map((l) => `
      <div class="bg-white border rounded-xl p-4 flex justify-between gap-3 items-start">
        <div>
          <p class="font-semibold">${l.title}</p>
          <p class="text-sm text-slate-500">${l.location?.neighborhood || ""}, ${l.location?.city || ""} · ${l.price} MAD</p>
          <p class="text-xs mt-1"><span class="uppercase font-bold text-slate-600">${l.status}</span>
            · verification: ${l.verificationStatus}</p>
        </div>
        <div class="flex flex-col gap-1">
          <button data-edit="${l.id}" class="text-sm text-emerald-700 font-medium">Edit</button>
          <button data-pub="${l.id}" class="text-sm text-slate-600">${l.status === "published" ? "Pause" : "Publish"}</button>
        </div>
      </div>`).join("")
    : `<p class="text-sm text-slate-500">No listings yet.</p>`;

  $("#listing-list").querySelectorAll("[data-edit]").forEach((btn) => {
    btn.onclick = () => openForm(listings.find((x) => x.id === btn.dataset.edit));
  });
  $("#listing-list").querySelectorAll("[data-pub]").forEach((btn) => {
    btn.onclick = async () => {
      const l = listings.find((x) => x.id === btn.dataset.pub);
      const status = l.status === "published" ? "paused" : "published";
      await api(`/business/listings/${l.id}`, { method: "PATCH", body: JSON.stringify({ status }) });
      await refresh();
    };
  });

  $("#leads-list").innerHTML = leads.length
    ? leads.map((lead) => `
      <div class="bg-white border rounded-xl p-4">
        <div class="flex justify-between">
          <p class="font-semibold text-sm">${lead.id}</p>
          <span class="text-[10px] font-bold uppercase bg-slate-100 px-2 py-0.5 rounded-full">${(lead.status || "").replace(/_/g, " ")}</span>
        </div>
        <p class="text-xs text-slate-500 mt-1">Listings: ${(lead.listingIds || []).join(", ")}</p>
        <p class="text-xs text-slate-400">${lead.createdAt || ""}</p>
      </div>`).join("")
    : `<p class="text-sm text-slate-500">No leads yet.</p>`;
}

function openForm(listing) {
  $("#form-section").classList.remove("hidden");
  $("#form-title").textContent = listing ? "Edit listing" : "Create listing";
  $("#f-id").value = listing?.id || "";
  $("#f-title").value = listing?.title || "";
  $("#f-desc").value = listing?.description || "";
  $("#f-price").value = listing?.price || "";
  $("#f-status").value = listing?.status || "draft";
  $("#f-city").value = listing?.location?.city || "Casablanca";
  $("#f-nb").value = listing?.location?.neighborhood || "";
  $("#f-ptype").value = listing?.propertyType || "apartment";
  $("#f-tx").value = listing?.transactionType || "buy";
  $("#f-beds").value = listing?.bedrooms ?? "";
  $("#f-baths").value = listing?.bathrooms ?? "";
  $("#f-area").value = listing?.sizeSqm ?? "";
  $("#f-image").value = listing?.images?.[0] || "";
  $("#f-parking").checked = !!listing?.parking;
  $("#f-furnished").checked = !!listing?.furnished;
  $("#form-section").scrollIntoView({ behavior: "smooth" });
}

$("#new-listing").onclick = () => openForm(null);
$("#form-cancel").onclick = () => $("#form-section").classList.add("hidden");

$("#listing-form").onsubmit = async (e) => {
  e.preventDefault();
  const payload = {
    title: $("#f-title").value,
    description: $("#f-desc").value,
    price: Number($("#f-price").value),
    status: $("#f-status").value,
    city: $("#f-city").value,
    neighborhood: $("#f-nb").value,
    propertyType: $("#f-ptype").value,
    transactionType: $("#f-tx").value,
    bedrooms: Number($("#f-beds").value) || null,
    bathrooms: Number($("#f-baths").value) || null,
    sizeSqm: Number($("#f-area").value) || null,
    image: $("#f-image").value || undefined,
    parking: $("#f-parking").checked,
    furnished: $("#f-furnished").checked,
  };
  const id = $("#f-id").value;
  if (id) {
    await api(`/business/listings/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
  } else {
    await api("/business/listings", { method: "POST", body: JSON.stringify(payload) });
  }
  $("#form-section").classList.add("hidden");
  await refresh();
};

boot();
