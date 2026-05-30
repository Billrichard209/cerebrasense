"""Regression tests for the static frontend to backend API bridge."""

from __future__ import annotations

from pathlib import Path
import json


def test_static_frontend_api_config_targets_backend_port() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    api_config = (workspace_root / "frontend_demo" / "api-config.js").read_text(encoding="utf-8")

    assert "inferCerebraSenseApiBase" in api_config
    assert "isStaticFrontend" in api_config
    assert "http://127.0.0.1:8000" in api_config
    assert "CEREBRASENSE_DASHBOARD_TIMEOUT_MS" in api_config
    assert "./data/dashboard_fallback.json" in api_config


def test_frontend_scripts_are_cache_busted_for_data_bridge() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    index_html = (workspace_root / "frontend_demo" / "index.html").read_text(encoding="utf-8")

    assert "./api-config.js?v=data-bridge-20260529b" in index_html
    assert "./app.js?v=data-bridge-20260529b" in index_html


def test_frontend_render_path_is_guarded() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    app_js = (workspace_root / "frontend_demo" / "app.js").read_text(encoding="utf-8")

    assert "runSafeStep(\"initial render\", triggerFullRender)" in app_js
    assert "function getActivePatient()" in app_js
    assert "function updatePatientSelectorLabel()" in app_js
    assert "if (menuBtn && sidebar && overlay)" in app_js
    assert "renderNoDashboardData()" in app_js


def test_frontend_dashboard_fallback_payload_is_portable() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    fallback_path = workspace_root / "frontend_demo" / "data" / "dashboard_fallback.json"
    payload = json.loads(fallback_path.read_text(encoding="utf-8"))

    assert payload["subjects"]
    assert not any("C:\\" in json.dumps(subject) for subject in payload["subjects"])
    assert "decision-support" in json.dumps(payload).lower()
