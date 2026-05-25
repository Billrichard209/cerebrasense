"""Check whether the OASIS-2 productization path is aligned across local and synced artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.configs.runtime import get_app_settings  # noqa: E402
from src.utils.io_utils import ensure_directory  # noqa: E402


@dataclass(slots=True, frozen=True)
class ProductizationCheck:
    name: str
    status: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class OASIS2ProductizationReport:
    generated_at: str
    expected_run_name: str | None
    overall_status: str
    checks: list[ProductizationCheck]
    recommendations: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        summary = {"pass": 0, "warn": 0, "fail": 0}
        for check in self.checks:
            summary[check.status] = summary.get(check.status, 0) + 1
        return {
            "generated_at": self.generated_at,
            "expected_run_name": self.expected_run_name,
            "overall_status": self.overall_status,
            "summary": summary,
            "checks": [asdict(check) for check in self.checks],
            "recommendations": list(self.recommendations),
        }


def _overall_status(checks: list[ProductizationCheck]) -> str:
    if any(check.status == "fail" for check in checks):
        return "fail"
    if any(check.status == "warn" for check in checks):
        return "warn"
    return "pass"


def build_report(*, expected_run_name: str | None, source_runtime_root: Path | None) -> OASIS2ProductizationReport:
    settings = get_app_settings()
    checks: list[ProductizationCheck] = []

    registry_path = settings.outputs_root / "model_registry" / "oasis2_current_baseline.json"
    if registry_path.exists():
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
        run_name = str(payload.get("run_name") or "")
        checkpoint = Path(str(payload.get("checkpoint_path") or ""))
        if not checkpoint.is_absolute():
            checkpoint = (settings.project_root / checkpoint).resolve()
        if checkpoint.exists():
            checks.append(ProductizationCheck("local_registry_checkpoint", "pass", "OASIS-2 registry checkpoint resolves.", {"path": str(checkpoint)}))
        else:
            checks.append(ProductizationCheck("local_registry_checkpoint", "fail", "OASIS-2 registry checkpoint missing.", {"path": str(checkpoint)}))
        if expected_run_name and run_name != expected_run_name:
            checks.append(
                ProductizationCheck(
                    "expected_run_name",
                    "warn",
                    f"Active OASIS-2 run is {run_name!r}, expected {expected_run_name!r}.",
                    {},
                )
            )
    else:
        checks.append(ProductizationCheck("local_registry", "fail", f"Missing OASIS-2 registry: {registry_path}", {}))

    if expected_run_name:
        run_root = settings.outputs_root / "runs" / "oasis2" / expected_run_name
        predictions = run_root / "evaluation" / "post_train_test_best_model" / "predictions.csv"
        audit_json = settings.outputs_root / "reports" / "longitudinal" / f"audit_{expected_run_name}.json"
        onnx_candidates = [
            settings.project_root / "best_model.onnx",
            settings.project_root / f"best_model_{expected_run_name}.onnx",
        ]
        if run_root.exists():
            checks.append(ProductizationCheck("local_run_root", "pass", "Local OASIS-2 run folder exists.", {"path": str(run_root)}))
        else:
            checks.append(ProductizationCheck("local_run_root", "fail", "Local OASIS-2 run folder missing.", {"path": str(run_root)}))
        if predictions.exists():
            checks.append(ProductizationCheck("test_predictions", "pass", "Held-out test predictions exist.", {"path": str(predictions)}))
        else:
            checks.append(ProductizationCheck("test_predictions", "warn", "Test predictions missing; run post_train_pipeline.", {"path": str(predictions)}))
        if audit_json.exists():
            audit = json.loads(audit_json.read_text(encoding="utf-8"))
            paradox_count = int(audit.get("paradox_count", 0))
            checks.append(
                ProductizationCheck(
                    "temporal_paradox_audit",
                    "pass" if paradox_count == 0 else "warn",
                    f"Temporal paradox audit: {paradox_count} paradoxes.",
                    {"path": str(audit_json)},
                )
            )
        else:
            checks.append(ProductizationCheck("temporal_paradox_audit", "warn", "Temporal paradox audit not found.", {}))
        if any(path.exists() for path in onnx_candidates):
            checks.append(ProductizationCheck("onnx_export", "pass", "ONNX export detected for serving.", {}))
        else:
            checks.append(ProductizationCheck("onnx_export", "warn", "No ONNX export found at project root.", {}))

    if source_runtime_root is not None:
        runtime_registry = source_runtime_root / "outputs" / "model_registry" / "oasis2_current_baseline.json"
        if runtime_registry.exists():
            checks.append(ProductizationCheck("runtime_registry", "pass", "Synced runtime OASIS-2 registry found.", {"path": str(runtime_registry)}))
        else:
            checks.append(ProductizationCheck("runtime_registry", "warn", "Synced runtime OASIS-2 registry missing.", {"path": str(runtime_registry)}))

    recommendations = []
    if any(check.status == "fail" for check in checks):
        recommendations.append("Import the promoted Colab run with import_promoted_oasis2_run.cmd before demoing OASIS-2.")
    if any(check.name == "test_predictions" and check.status == "warn" for check in checks):
        recommendations.append("Run scripts/post_train_pipeline.py --run-name <run> after training completes.")
    recommendations.append("Regenerate the leaderboard with build_oasis2_leaderboard.cmd and compare test AUROC across seeds.")

    return OASIS2ProductizationReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        expected_run_name=expected_run_name,
        overall_status=_overall_status(checks),
        checks=checks,
        recommendations=recommendations,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Check OASIS-2 productization alignment.")
    parser.add_argument("--expected-run-name", type=str, default=None)
    parser.add_argument("--source-runtime-root", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args()

    report = build_report(
        expected_run_name=args.expected_run_name,
        source_runtime_root=args.source_runtime_root.expanduser().resolve() if args.source_runtime_root else None,
    )
    settings = get_app_settings()
    output_json = args.output_json or (
        settings.outputs_root / "reports" / "productization" / "oasis2_productization_status.json"
    )
    ensure_directory(output_json.parent)
    output_json.write_text(json.dumps(report.to_payload(), indent=2), encoding="utf-8")
    print(json.dumps(report.to_payload(), indent=2))
    if report.overall_status == "fail":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
