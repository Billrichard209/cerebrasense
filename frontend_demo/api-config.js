/** API base URL for CerebraSense frontend demo. */
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

async function fetchDashboardData() {
  const response = await fetch(`${window.CEREBRASENSE_API_BASE}/dashboard/data`, {
    headers: cerebraSenseApiHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Dashboard API failed: ${response.status}`);
  }
  return response.json();
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
