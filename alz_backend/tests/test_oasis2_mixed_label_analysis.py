"""Tests for OASIS-2 mixed-label error analysis."""

from __future__ import annotations

import json

import pandas as pd

from scripts.analyze_oasis2_mixed_label_errors import analyze_mixed_label_errors


def test_mixed_label_analysis_allows_no_evaluable_rows(tmp_path) -> None:
    """A split with no mixed-label predictions should emit an empty report."""

    predictions_csv = tmp_path / "predictions.csv"
    train_manifest_csv = tmp_path / "train_manifest.csv"
    output_root = tmp_path / "mixed_label"

    pd.DataFrame(
        [
            {
                "meta_subject_id": "OAS2_0001",
                "true_label": 0,
                "predicted_label": 0,
                "probability_class_1": 0.2,
            }
        ]
    ).to_csv(predictions_csv, index=False)
    pd.DataFrame(
        [
            {"subject_id": "OAS2_0002", "mixed_label_group": True},
        ]
    ).to_csv(train_manifest_csv, index=False)

    summary = analyze_mixed_label_errors(
        predictions_csv=predictions_csv,
        train_manifest_csv=train_manifest_csv,
        output_root=output_root,
    )

    assert summary["status"] == "no_evaluable_mixed_label_rows"
    assert summary["mixed_subject_count"] == 1
    assert summary["evaluated_rows"] == 0
    assert summary["overall_error_rate"] is None
    assert (output_root / "mixed_label_prediction_rows.csv").exists()
    assert (output_root / "mixed_label_subject_summary.csv").exists()

    saved_summary = json.loads((output_root / "mixed_label_error_summary.json").read_text(encoding="utf-8"))
    assert saved_summary == summary
