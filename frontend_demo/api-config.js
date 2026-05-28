/** API base URL for CerebraSense frontend demo (served at /demo/ via FastAPI). */
window.CEREBRASENSE_API_BASE = window.CEREBRASENSE_API_BASE || "";
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
