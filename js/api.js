/**
 * API client. In production (APP production flag), never falls back to local inventory.
 */
import { config } from "./config.js";

function getToken() {
  try {
    return localStorage.getItem("soukly_token") || null;
  } catch {
    return null;
  }
}

export function setToken(token) {
  if (token) localStorage.setItem("soukly_token", token);
  else localStorage.removeItem("soukly_token");
}

async function request(path, options = {}) {
  if (!config.apiBase) {
    const err = new Error("API_NOT_CONFIGURED");
    err.code = "API_NOT_CONFIGURED";
    throw err;
  }
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  let res;
  try {
    res = await fetch(config.apiBase + path, { ...options, headers, credentials: "include" });
  } catch (e) {
    const err = new Error("network_error");
    err.code = "network_error";
    throw err;
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.error || `API ${res.status}`);
    err.status = res.status;
    err.body = data;
    throw err;
  }
  return data;
}

export async function healthCheck() {
  try {
    return await request("/health");
  } catch {
    return null;
  }
}

export async function login(identifier, password) {
  const data = await request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ identifier, password }),
  });
  if (data.token) setToken(data.token);
  return data;
}

export async function register(payload) {
  const data = await request("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  if (data.token) setToken(data.token);
  return data;
}

export async function logout() {
  try {
    await request("/auth/logout", { method: "POST", body: "{}" });
  } finally {
    setToken(null);
  }
}

export async function me() {
  return request("/me");
}

export async function getCategories() {
  return request("/categories");
}

export async function getListings(filters = {}) {
  const q = new URLSearchParams();
  if (filters.categoryId) q.set("categoryId", filters.categoryId);
  if (filters.city) q.set("city", filters.city);
  const qs = q.toString();
  return request("/listings" + (qs ? `?${qs}` : ""));
}

export async function getListing(id) {
  return request(`/listings/${id}`);
}

export async function searchListings(query, opts = {}) {
  return request("/search", {
    method: "POST",
    body: JSON.stringify({
      query,
      userId: opts.userId || null,
      limit: opts.limit || config.defaultRecommendationCount,
    }),
  });
}

export async function createAgentRequest(payload) {
  return request("/agent-requests", {
    method: "POST",
    body: JSON.stringify({
      listingIds: payload.listingIds,
      searchRequestId: payload.searchRequestId || null,
      customerName: payload.customerName || null,
      customerPhone: payload.customerPhone || null,
    }),
  });
}

export async function getMyAgentRequests() {
  return request("/me/agent-requests");
}

export async function getAgentRequests() {
  return request("/agent-requests");
}

export async function getAgentRequest(id) {
  return request(`/agent-requests/${id}`);
}

export async function updateAgentRequest(id, patch) {
  return request(`/agent-requests/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export async function getNotifications() {
  return request("/notifications");
}
