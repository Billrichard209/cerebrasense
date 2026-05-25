"""Aggregate OASIS-2 run metrics into a leaderboard CSV and refresh training_summary.md."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.configs.runtime import get_app_settings  # noqa: E402
from src.utils.io_utils import ensure_directory  # noqa: E402


def _load_metrics(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _find_prediction_csv(run_root: Path) -> Path | None:
    candidates = [
        run_root / "evaluation" / "post_train_test_best_model" / "predictions.csv",
        run_root / "evaluation" / "post_train_test_best_model_threshold_youden_index" / "predictions.csv",
        run_root / "evaluation" / "post_train_val_best_model" / "predictions.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _mixed_group_error_rate(predictions_csv: Path, train_manifest: Path | None) -> float | None:
    if not predictions_csv.exists() or train_manifest is None or not train_manifest.exists():
        return None
    predictions = pd.read_csv(predictions_csv)
    manifest = pd.read_csv(train_manifest)
    if "mixed_label_group" not in manifest.columns or "meta_subject_id" not in predictions.columns:
        return None
    mixed_subjects = set(
        manifest.loc[manifest["mixed_label_group"].fillna(False).astype(bool), "subject_id"].astype(str).tolist()
    )
    if not mixed_subjects:
        return None
    subset = predictions[predictions["meta_subject_id"].astype(str).isin(mixed_subjects)].copy()
    if subset.empty or "true_label" not in subset.columns or "predicted_label" not in subset.columns:
        return None
    errors = (subset["true_label"].astype(int) != subset["predicted_label"].astype(int)).mean()
    return float(errors)


def collect_run_rows(runs_root: Path, split_manifest_root: Path | None) -> list[dict]:
    rows: list[dict] = []
    if not runs_root.exists():
        return rows
    train_manifest = None
    if split_manifest_root is not None:
        candidate = split_manifest_root / "oasis2_train_manifest.csv"
        train_manifest = candidate if candidate.exists() else None

    for run_dir in sorted(runs_root.iterdir()):
        if not run_dir.is_dir():
            continue
        val_metrics = _load_metrics(run_dir / "evaluation" / "post_train_val_best_model" / "metrics.json")
        test_metrics = _load_metrics(run_dir / "evaluation" / "post_train_test_best_model" / "metrics.json")
        test_calibrated = _load_metrics(
            run_dir / "evaluation" / "post_train_test_best_model_threshold_youden_index" / "metrics.json"
        )
        epoch_csv = run_dir / "metrics" / "epoch_metrics.csv"
        val_auroc_train = None
        if epoch_csv.exists():
            epoch_frame = pd.read_csv(epoch_csv)
            if "auroc" in epoch_frame.columns and not epoch_frame.empty:
                val_auroc_train = float(epoch_frame["auroc"].max())

        predictions_csv = _find_prediction_csv(run_dir)
        mixed_error = (
            _mixed_group_error_rate(predictions_csv, train_manifest)
            if predictions_csv is not None and train_manifest is not None
            else None
        )

        rows.append(
            {
                "run_name": run_dir.name,
                "val_auroc": val_metrics.get("auroc"),
                "val_accuracy": val_metrics.get("accuracy"),
                "val_f1": val_metrics.get("f1"),
                "test_auroc": test_metrics.get("auroc"),
                "test_accuracy": test_metrics.get("accuracy"),
                "test_balanced_acc": test_calibrated.get("balanced_accuracy", test_metrics.get("balanced_accuracy")),
                "test_specificity": test_calibrated.get("specificity", test_metrics.get("specificity")),
                "test_f1": test_calibrated.get("f1", test_metrics.get("f1")),
                "best_val_auroc_training": val_auroc_train,
                "mixed_group_error_rate": mixed_error,
                "has_test_predictions": predictions_csv is not None,
            }
        )
    return rows


def write_training_summary(rows: list[dict], output_path: Path) -> None:
    lines = [
        "# Training Accuracy Summary",
        "",
        "## OASIS-2 Leaderboard (auto-generated)",
        "",
        "Compare runs on **held-out test AUROC**, not validation F1 alone.",
        "",
    ]
    if not rows:
        lines.append("_No OASIS-2 runs found under outputs/runs/oasis2._")
    else:
        frame = pd.DataFrame(rows).sort_values("test_auroc", ascending=False, na_position="last")
        headers = list(frame.columns)
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for _, row in frame.iterrows():
            cells = [str(row[column]) if pd.notna(row[column]) else "" for column in headers]
            lines.append("| " + " | ".join(cells) + " |")
    lines.extend(
        [
            "",
            "## OASIS-1 (reference)",
            "",
            "- **Model**: DenseNet121 (MONAI)",
            "- **Test Accuracy**: 0.8611",
            "- **Test AUROC**: 0.8794",
            "- **Test F1-Score**: 0.8485",
            "",
            "---",
            "*Regenerate with: `python scripts/build_oasis2_leaderboard.py`*",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the OASIS-2 experiment leaderboard.")
    parser.add_argument("--workspace-root", type=Path, default=None)
    args = parser.parse_args()

    settings = get_app_settings()
    runs_root = settings.outputs_root / "runs" / "oasis2"
    split_root = settings.outputs_root / "reports" / "oasis2_supervised_seed42_split42_train70_val15_test15"
    rows = collect_run_rows(runs_root, split_root)

    leaderboard_dir = ensure_directory(settings.outputs_root / "experiments")
    leaderboard_csv = leaderboard_dir / "oasis2_leaderboard.csv"
    pd.DataFrame(rows).to_csv(leaderboard_csv, index=False)

    summary_path = (
        Path(args.workspace_root).resolve() / "training_summary.md"
        if args.workspace_root is not None
        else settings.workspace_root / "training_summary.md"
    )
    if not summary_path.parent.exists():
        summary_path = settings.collection_root / "training_summary.md"
    write_training_summary(rows, summary_path)

    print(f"Wrote leaderboard: {leaderboard_csv}")
    print(f"Wrote summary: {summary_path}")


if __name__ == "__main__":
    main()
