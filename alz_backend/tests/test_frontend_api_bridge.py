"""Regression tests for the static frontend to backend API bridge."""

from __future__ import annotations

from pathlib import Path


def test_static_frontend_api_config_targets_backend_port() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    api_config = (workspace_root / "frontend_demo" / "api-config.js").read_text(encoding="utf-8")

    assert "inferCerebraSenseApiBase" in api_config
    assert "isStaticFrontend" in api_config
    assert "http://127.0.0.1:8000" in api_config


def test_frontend_scripts_are_cache_busted_for_data_bridge() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    index_html = (workspace_root / "frontend_demo" / "index.html").read_text(encoding="utf-8")

    assert "./api-config.js?v=data-bridge-20260529" in index_html
    assert "./app.js?v=data-bridge-20260529" in index_html
