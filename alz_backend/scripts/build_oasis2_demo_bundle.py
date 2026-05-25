"""Build a single OASIS-2 demo bundle from the active registry and evaluation artifacts."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.api.main import create_app  # noqa: E402
from src.configs.runtime import get_app_settings  # noqa: E402
from src.inference.dashboard_utils import load_dashboard_data  # noqa: E402
from src.models.registry import load_current_oasis2_model_entry  # noqa: E402
from src.utils.io_utils import ensure_directory  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an OASIS-2 local demo bundle.")
    parser.add_argument("--bundle-name", type=str, default="oasis2_demo_bundle")
    parser.add_argument("--run-name", type=str, default=None)
    args = parser.parse_args()

    settings = get_app_settings()
    try:
        entry = load_current_oasis2_model_entry()
        run_name = entry.run_name
    except FileNotFoundError:
        if args.run_name is None:
            raise SystemExit("No OASIS-2 registry entry found. Provide --run-name or promote a run first.")
        run_name = args.run_name
        entry = None

    bundle_root = ensure_directory(settings.outputs_root / "reports" / "demo" / args.bundle_name)
    run_root = settings.outputs_root / "runs" / "oasis2" / run_name

    copied: list[str] = []
    for rel in (
        "evaluation/post_train_test_best_model/metrics.json",
        "evaluation/post_train_test_best_model/predictions.csv",
        "evaluation/post_train_test_best_model_threshold_balanced_accuracy/metrics.json",
        "reports/oasis2_vs_oasis1_comparison.md",
        "metrics/epoch_metrics.csv",
    ):
        source = run_root / rel.replace("/", "\\") if "\\" in str(run_root) else run_root / rel
        if not source.exists():
            source = run_root / Path(rel)
        if source.exists():
            target = bundle_root / Path(rel).name if "/" in rel else bundle_root / rel
            if source.is_dir():
                shutil.copytree(source, target, dirs_exist_ok=True)
            else:
                shutil.copy2(source, bundle_root / source.name)
            copied.append(str(source))

    dashboard_payload, dashboard_error = load_dashboard_data(settings.project_root)
    (bundle_root / "dashboard_payload.json").write_text(
        json.dumps({"data": dashboard_payload, "error": dashboard_error}, indent=2),
        encoding="utf-8",
    )

    client = TestClient(create_app())
    health = client.get("/health")
    (bundle_root / "api_health.json").write_text(json.dumps(health.json(), indent=2), encoding="utf-8")

    summary = {
        "bundle_name": args.bundle_name,
        "run_name": run_name,
        "registry_entry": None if entry is None else entry.to_dict(),
        "copied_artifacts": copied,
        "dashboard_error": dashboard_error,
        "api_health_status": health.status_code,
    }
    (bundle_root / "bundle_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
