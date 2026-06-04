"""Analyze prediction errors on OASIS-2 mixed-label longitudinal subjects."""

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

DEFAULT_SPLIT_ROOT = "oasis2_supervised_seed42_split42_train70_val15_test15"


def analyze_mixed_label_errors(
    *,
    predictions_csv: Path,
    train_manifest_csv: Path,
    output_root: Path,
) -> dict:
    predictions = pd.read_csv(predictions_csv)
    manifest = pd.read_csv(train_manifest_csv)
    if "mixed_label_group" not in manifest.columns:
        raise ValueError("Train manifest is missing mixed_label_group column.")

    mixed_subjects = set(
        manifest.loc[manifest["mixed_label_group"].fillna(False).astype(bool), "subject_id"].astype(str).tolist()
    )
    subject_col = "meta_subject_id" if "meta_subject_id" in predictions.columns else "subject_id"
    if subject_col not in predictions.columns:
        raise ValueError("Predictions CSV must include meta_subject_id or subject_id.")

    subset = predictions[predictions[subject_col].astype(str).isin(mixed_subjects)].copy()
    if subset.empty:
        ensure_directory(output_root)
        per_subject = pd.DataFrame(
            columns=[subject_col, "visit_count", "error_count", "mean_probability", "error_rate"]
        )
        summary = {
            "status": "no_evaluable_mixed_label_rows",
            "predictions_csv": str(predictions_csv),
            "mixed_subject_count": len(mixed_subjects),
            "evaluated_rows": 0,
            "overall_error_rate": None,
            "per_subject_error_rate_mean": None,
            "per_subject_error_rate_max": None,
        }
        subset.to_csv(output_root / "mixed_label_prediction_rows.csv", index=False)
        per_subject.to_csv(output_root / "mixed_label_subject_summary.csv", index=False)
        (output_root / "mixed_label_error_summary.json").write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8",
        )
        (output_root / "mixed_label_error_summary.md").write_text(
            "\n".join(
                [
                    "# OASIS-2 Mixed-Label Error Analysis",
                    "",
                    "- status: no_evaluable_mixed_label_rows",
                    f"- mixed_subject_count: {summary['mixed_subject_count']}",
                    "- evaluated_rows: 0",
                    "",
                    "No mixed-label subjects were present in the evaluated predictions split.",
                ]
            ),
            encoding="utf-8",
        )
        return summary

    subset["is_error"] = subset["true_label"].astype(int) != subset["predicted_label"].astype(int)
    per_subject = (
        subset.groupby(subject_col)
        .agg(
            visit_count=("predicted_label", "count"),
            error_count=("is_error", "sum"),
            mean_probability=("probability_class_1", "mean"),
        )
        .reset_index()
    )
    per_subject["error_rate"] = per_subject["error_count"] / per_subject["visit_count"]

    overall_error_rate = float(subset["is_error"].mean())
    summary = {
        "predictions_csv": str(predictions_csv),
        "mixed_subject_count": len(mixed_subjects),
        "evaluated_rows": int(len(subset)),
        "overall_error_rate": overall_error_rate,
        "per_subject_error_rate_mean": float(per_subject["error_rate"].mean()),
        "per_subject_error_rate_max": float(per_subject["error_rate"].max()),
    }

    ensure_directory(output_root)
    subset.to_csv(output_root / "mixed_label_prediction_rows.csv", index=False)
    per_subject.to_csv(output_root / "mixed_label_subject_summary.csv", index=False)
    (output_root / "mixed_label_error_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (output_root / "mixed_label_error_summary.md").write_text(
        "\n".join(
            [
                "# OASIS-2 Mixed-Label Error Analysis",
                "",
                f"- mixed_subject_count: {summary['mixed_subject_count']}",
                f"- evaluated_rows: {summary['evaluated_rows']}",
                f"- overall_error_rate: {summary['overall_error_rate']:.4f}",
                f"- per_subject_error_rate_mean: {summary['per_subject_error_rate_mean']:.4f}",
                f"- per_subject_error_rate_max: {summary['per_subject_error_rate_max']:.4f}",
                "",
                "Mixed-label groups include converted patients whose early visits remain nondemented.",
            ]
        ),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze OASIS-2 errors on mixed-label subjects.")
    parser.add_argument("--run-name", type=str, required=True)
    parser.add_argument("--split-root-name", type=str, default=DEFAULT_SPLIT_ROOT)
    parser.add_argument("--predictions-csv", type=Path, default=None)
    args = parser.parse_args()

    settings = get_app_settings()
    run_root = settings.outputs_root / "runs" / "oasis2" / args.run_name
    predictions_csv = args.predictions_csv or (
        run_root / "evaluation" / "post_train_test_best_model" / "predictions.csv"
    )
    train_manifest = settings.outputs_root / "reports" / args.split_root_name / "oasis2_train_manifest.csv"
    output_root = ensure_directory(settings.outputs_root / "reports" / "oasis2_mixed_label_errors" / args.run_name)

    summary = analyze_mixed_label_errors(
        predictions_csv=predictions_csv,
        train_manifest_csv=train_manifest,
        output_root=output_root,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
