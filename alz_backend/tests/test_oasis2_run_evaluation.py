"""Tests for OASIS-2 run evaluation helpers."""

from __future__ import annotations

import json
from pathlib import Path

from src.configs.runtime import AppSettings
from src.evaluation.oasis2_run import (
    OASIS2RunEvaluationConfig,
    build_oasis2_run_evaluation_paths,
    compute_oasis2_subject_consensus_metrics,
    resolve_oasis2_checkpoint_path,
    save_oasis2_vs_oasis1_comparison,
)
from src.evaluation.evaluate_oasis import OASISEvaluationResult, OASISPredictionRecord
from src.evaluation.thresholds import ThresholdCalibrationResult


def _build_settings(tmp_path: Path) -> AppSettings:
    project_root = tmp_path / "alz_backend"
    data_root = project_root / "data"
    outputs_root = project_root / "outputs"
    data_root.mkdir(parents=True)
    outputs_root.mkdir(parents=True)
    return AppSettings(
        project_root=project_root,
        workspace_root=project_root.parent,
        collection_root=project_root.parent,
        data_root=data_root,
        outputs_root=outputs_root,
        kaggle_source_root=project_root.parent,
        oasis_source_root=project_root.parent / "OASIS",
    )


def test_resolve_oasis2_checkpoint_path_accepts_explicit_drive_candidate(tmp_path: Path) -> None:
    settings = _build_settings(tmp_path)
    checkpoint_path = tmp_path / "drive" / "best_model.pt"
    checkpoint_path.parent.mkdir(parents=True)
    checkpoint_path.write_bytes(b"checkpoint")

    resolved = resolve_oasis2_checkpoint_path(
        OASIS2RunEvaluationConfig(run_name="oasis2_colab_improved_v1", checkpoint_path=checkpoint_path),
        settings=settings,
    )

    assert resolved == checkpoint_path


def test_build_oasis2_run_evaluation_paths_writes_under_oasis2_run(tmp_path: Path) -> None:
    settings = _build_settings(tmp_path)

    paths = build_oasis2_run_evaluation_paths(
        OASIS2RunEvaluationConfig(run_name="candidate", split="test", output_name="calibrated test"),
        settings=settings,
    )

    assert paths.evaluation_root == settings.outputs_root / "runs" / "oasis2" / "candidate" / "evaluation" / "calibrated_test"
    assert paths.metrics_json_path.name == "metrics.json"


def test_save_oasis2_vs_oasis1_comparison_keeps_promotion_conservative(tmp_path: Path) -> None:
    settings = _build_settings(tmp_path)
    registry_root = settings.outputs_root / "model_registry"
    registry_root.mkdir(parents=True)
    (registry_root / "oasis_current_baseline.json").write_text(
        json.dumps(
            {
                "run_name": "oasis1_active",
                "test_metrics": {
                    "accuracy": 0.86,
                    "auroc": 0.88,
                    "f1": 0.85,
                    "sensitivity": 0.93,
                    "specificity": 0.81,
                    "review_required_count": 10,
                },
            }
        ),
        encoding="utf-8",
    )
    calibration = ThresholdCalibrationResult(
        threshold=0.42,
        selection_metric="balanced_accuracy",
        validation_metrics={},
        test_metrics={},
        output_dir=tmp_path,
        calibration_report_path=tmp_path / "threshold_calibration.json",
        threshold_grid_path=tmp_path / "threshold_grid.csv",
        test_metrics_path=tmp_path / "test_metrics.json",
    )

    output_path = save_oasis2_vs_oasis1_comparison(
        run_name="oasis2_colab_improved_v1",
        raw_test_metrics={"accuracy": 0.6, "auroc": 0.7},
        calibrated_test_metrics={
            "accuracy": 0.63,
            "auroc": 0.64,
            "f1": 0.71,
            "sensitivity": 0.89,
            "specificity": 0.37,
            "review_required_count": 20,
        },
        calibration=calibration,
        output_path=settings.outputs_root / "runs" / "oasis2" / "candidate" / "reports" / "comparison.md",
        settings=settings,
    )

    text = output_path.read_text(encoding="utf-8")
    assert "- recommendation: do_not_promote" in text
    assert "not a drop-in replacement" in text


def test_compute_oasis2_subject_consensus_metrics_averages_visits() -> None:
    result = OASISEvaluationResult(
        dataset="oasis2",
        dataset_type="3d_volumes",
        class_names=("nondemented", "demented"),
        metrics={"threshold": 0.5},
        predictions=[
            OASISPredictionRecord(
                sample_id="s1v1",
                true_label=0,
                true_label_name="nondemented",
                predicted_label=1,
                predicted_label_name="demented",
                probabilities=[0.4, 0.6],
                confidence=0.6,
                entropy=0.0,
                normalized_entropy=0.0,
                probability_margin=0.2,
                uncertainty_score=0.4,
                meta={"subject_id": "OAS2_0001"},
            ),
            OASISPredictionRecord(
                sample_id="s1v2",
                true_label=0,
                true_label_name="nondemented",
                predicted_label=0,
                predicted_label_name="nondemented",
                probabilities=[0.8, 0.2],
                confidence=0.8,
                entropy=0.0,
                normalized_entropy=0.0,
                probability_margin=0.6,
                uncertainty_score=0.2,
                meta={"subject_id": "OAS2_0001"},
            ),
            OASISPredictionRecord(
                sample_id="s2v1",
                true_label=1,
                true_label_name="demented",
                predicted_label=1,
                predicted_label_name="demented",
                probabilities=[0.2, 0.8],
                confidence=0.8,
                entropy=0.0,
                normalized_entropy=0.0,
                probability_margin=0.6,
                uncertainty_score=0.2,
                meta={"subject_id": "OAS2_0002"},
            ),
        ],
    )

    metrics = compute_oasis2_subject_consensus_metrics(result)

    assert metrics["sample_count"] == 2
    assert metrics["confusion_counts"]["true_negative"] == 1
    assert metrics["confusion_counts"]["true_positive"] == 1
