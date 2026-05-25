"""Promote an OASIS-2 run to oasis2_current_baseline.json when gates pass."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.configs.runtime import get_app_settings  # noqa: E402
from src.models.registry import ModelRegistryEntry, save_oasis_model_entry  # noqa: E402
from src.security.disclaimers import STANDARD_DECISION_SUPPORT_DISCLAIMER  # noqa: E402
from src.utils.io_utils import ensure_directory  # noqa: E402

PROMOTION_GATES = {
    "test_auroc": 0.80,
    "balanced_accuracy": 0.75,
    "specificity": 0.70,
    "sensitivity": 0.65,
    "subject_auroc": 0.78,
    "max_paradox_count": 0,
}


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def evaluate_promotion_gates(*, run_name: str, settings) -> tuple[bool, list[str], dict]:
    run_root = settings.outputs_root / "runs" / "oasis2" / run_name
    metrics_path = (
        run_root / "evaluation" / "post_train_test_best_model_threshold_balanced_accuracy" / "metrics.json"
    )
    if not metrics_path.exists():
        metrics_path = run_root / "evaluation" / "post_train_test_best_model" / "metrics.json"
    metrics = _load_json(metrics_path)
    subject = metrics.get("subject_consensus", {})
    audit_path = settings.outputs_root / "reports" / "longitudinal" / f"audit_{run_name}.json"
    audit = _load_json(audit_path)
    paradox_count = int(audit.get("paradox_count", 0))

    failures: list[str] = []
    test_auroc = float(metrics.get("auroc", 0.0))
    if test_auroc < PROMOTION_GATES["test_auroc"]:
        failures.append(f"test_auroc {test_auroc:.4f} < {PROMOTION_GATES['test_auroc']}")
    balanced = float(metrics.get("balanced_accuracy", metrics.get("accuracy", 0.0)))
    if balanced < PROMOTION_GATES["balanced_accuracy"]:
        failures.append(f"balanced_accuracy {balanced:.4f} < {PROMOTION_GATES['balanced_accuracy']}")
    specificity = float(metrics.get("specificity", 0.0))
    if specificity < PROMOTION_GATES["specificity"]:
        failures.append(f"specificity {specificity:.4f} < {PROMOTION_GATES['specificity']}")
    sensitivity = float(metrics.get("sensitivity", metrics.get("recall_sensitivity", 0.0)))
    if sensitivity < PROMOTION_GATES["sensitivity"]:
        failures.append(f"sensitivity {sensitivity:.4f} < {PROMOTION_GATES['sensitivity']}")
    subject_auroc = float(subject.get("auroc", 0.0))
    if subject_auroc and subject_auroc < PROMOTION_GATES["subject_auroc"]:
        failures.append(f"subject_auroc {subject_auroc:.4f} < {PROMOTION_GATES['subject_auroc']}")
    if paradox_count > PROMOTION_GATES["max_paradox_count"]:
        failures.append(f"paradox_count {paradox_count} > {PROMOTION_GATES['max_paradox_count']}")

    summary = {
        "test_auroc": test_auroc,
        "balanced_accuracy": balanced,
        "specificity": specificity,
        "sensitivity": sensitivity,
        "subject_auroc": subject_auroc,
        "paradox_count": paradox_count,
        "metrics_path": str(metrics_path),
    }
    return len(failures) == 0, failures, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote an OASIS-2 run when quality gates pass.")
    parser.add_argument("--run-name", type=str, required=True)
    parser.add_argument("--force", action="store_true", help="Promote even when gates fail (not recommended).")
    parser.add_argument("--registry-output", type=Path, default=None)
    args = parser.parse_args()

    settings = get_app_settings()
    run_root = settings.outputs_root / "runs" / "oasis2" / args.run_name
    checkpoint = run_root / "checkpoints" / "best_model.pt"
    if not checkpoint.exists():
        raise SystemExit(f"Checkpoint not found: {checkpoint}")

    passed, failures, summary = evaluate_promotion_gates(run_name=args.run_name, settings=settings)
    if not passed and not args.force:
        print(json.dumps({"status": "blocked", "failures": failures, "summary": summary}, indent=2))
        raise SystemExit(1)

    calibration_dir = run_root / "calibration" / "threshold_balanced_accuracy"
    calibration = _load_json(calibration_dir / "threshold_calibration.json")
    test_metrics = _load_json(
        run_root / "evaluation" / "post_train_test_best_model_threshold_balanced_accuracy" / "metrics.json"
    )
    val_metrics = _load_json(run_root / "evaluation" / "post_train_val_best_model" / "metrics.json")
    recommended_threshold = float(calibration.get("threshold", 0.5))

    entry = ModelRegistryEntry(
        registry_version="1.0",
        model_id="oasis2_current_baseline",
        dataset="oasis2",
        run_name=args.run_name,
        checkpoint_path=str(checkpoint.resolve()),
        model_config_path=str((settings.project_root / "configs" / "oasis_model.yaml").resolve()),
        preprocessing_config_path=str((settings.project_root / "configs" / "oasis_transforms.yaml").resolve()),
        image_size=[128, 128, 128],
        promoted_at_utc=datetime.now(timezone.utc).isoformat(),
        decision_support_only=True,
        clinical_disclaimer=STANDARD_DECISION_SUPPORT_DISCLAIMER,
        default_threshold=0.5,
        recommended_threshold=recommended_threshold,
        threshold_calibration=calibration,
        validation_metrics=val_metrics,
        test_metrics=test_metrics,
        promotion_decision={
            "approved": passed,
            "forced": args.force and not passed,
            "gate_summary": summary,
            "failures": failures,
        },
        notes=[
            "OASIS-2 longitudinal decision-support registry entry.",
            "Promotion requires held-out test metrics and zero temporal paradoxes unless --force is used.",
        ],
    )
    registry_path = args.registry_output or (settings.outputs_root / "model_registry" / "oasis2_current_baseline.json")
    save_oasis_model_entry(entry, registry_path)
    print(json.dumps({"status": "promoted", "registry_path": str(registry_path), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
