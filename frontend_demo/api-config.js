/** API base URL for CerebraSense frontend demo. */
const CEREBRASENSE_DASHBOARD_TIMEOUT_MS = 3500;
const CEREBRASENSE_DASHBOARD_FALLBACK = "./data/dashboard_fallback.json";

function inferCerebraSenseApiBase() {
  if (window.CEREBRASENSE_API_BASE) return window.CEREBRASENSE_API_BASE;
  const isLocal = window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost";
  const isStaticFrontend = isLocal && window.location.port && window.location.port !== "8000";
  return isStaticFrontend ? "http://127.0.0.1:8000" : "";
}

window.CEREBRASENSE_API_BASE = inferCerebraSenseApiBase();
window.CEREBRASENSE_API_KEY = window.CEREBRASENSE_API_KEY || "";

function cerebraSenseApiHeaders(extraHeaders = {}) {
  const headers = { ...extraHeaders };
  if (window.CEREBRASENSE_API_KEY) {
    headers["X-API-Key"] = window.CEREBRASENSE_API_KEY;
  }
  return headers;
}

async function fetchWithTimeout(url, options = {}, timeoutMs = CEREBRASENSE_DASHBOARD_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    window.clearTimeout(timeout);
  }
}

async function fetchDashboardData() {
  const liveUrl = `${window.CEREBRASENSE_API_BASE}/dashboard/data`;
  try {
    const response = await fetchWithTimeout(liveUrl, {
      headers: cerebraSenseApiHeaders(),
    });
    if (!response.ok) {
      throw new Error(`Dashboard API failed: ${response.status}`);
    }
    return response.json();
  } catch (liveError) {
    console.warn("Live dashboard API unavailable; trying packaged demo payload.", liveError);
    const fallback = await fetch(CEREBRASENSE_DASHBOARD_FALLBACK, { cache: "no-store" });
    if (!fallback.ok) {
      throw liveError;
    }
    return fallback.json();
  }
}

async function fetchOasis2LongitudinalDashboard(runName) {
  const query = runName ? `?run_name=${encodeURIComponent(runName)}` : "";
  const response = await fetch(`${window.CEREBRASENSE_API_BASE}/longitudinal/oasis2/dashboard${query}`, {
    headers: cerebraSenseApiHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Longitudinal dashboard API failed: ${response.status}`);
  }
  return response.json();
}
