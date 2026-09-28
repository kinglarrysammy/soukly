/**
 * Client configuration for local + staging/production.
 *
 * Priority:
 * 1. window.__SOUKLY_ENV__.apiBase (injected at deploy)
 * 2. Same-origin /api (recommended: nginx/Caddy reverse-proxy)
 * 3. Local dev fallback
 */
function detectApiBase() {
  if (typeof window !== "undefined" && window.__SOUKLY_ENV__ && window.__SOUKLY_ENV__.apiBase) {
    return window.__SOUKLY_ENV__.apiBase.replace(/\/$/, "");
  }
  if (typeof window !== "undefined" && window.location) {
    const host = window.location.hostname;
    // Local static server without proxy → talk to local API
    if (host === "localhost" || host === "127.0.0.1") {
      return "http://127.0.0.1:8787/api";
    }
    // Staging/production: same origin /api
    return window.location.origin + "/api";
  }
  return "/api";
}

const env = (typeof window !== "undefined" && window.__SOUKLY_ENV__) || {};

export const config = {
  appName: "Soukly",
  country: "Morocco",
  defaultCity: "Casablanca, Morocco",
  currency: "MAD",
  defaultRecommendationCount: 7,
  apiBase: detectApiBase(),
  allowLocalFallback: env.allowLocalFallback === true,
  features: {
    speechToText: false,
    whatsapp: false,
    auth: true,
  },
};
