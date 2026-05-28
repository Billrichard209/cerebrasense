"""Regression tests for OASIS-2 productization helper artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from scripts.promote_oasis2_run import _balanced_accuracy, _resolve_image_size, _resolve_model_config_path
from scripts.build_oasis2_leaderboard import collect_run_rows
from src.configs.runtime import AppSettings
from src.training.oasis_research import load_research_oasis_training_config


def _settings(tmp_path: Path) -> AppSettings:
    project_root = tmp_path / "alz_backend"
    data_root = project_root / "data"
    outputs_root = project_root / "outputs"
    (project_root / "configs").mkdir(parents=True)
    data_root.mkdir(parents=True)
    outputs_root.mkdir(parents=True)
    return AppSettings(
        project_root=project_root,
        workspace_root=tmp_path,
        collection_root=tmp_path,
        data_root=data_root,
        outputs_root=outputs_root,
        kaggle_source_root=tmp_path,
        oasis_source_root=tmp_path / "OASIS",
        serving_config_path=project_root / "configs" / "backend_serving.yaml",
    )


def test_oasis2_promotion_uses_resolved_multimodal_config_and_image_size(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    multimodal_config = settings.project_root / "configs" / "oasis2_multimodal_model.yaml"
    multimodal_config.write_text("architecture: resnet50_multimodal\n", encoding="utf-8")
    run_root = settings.outputs_root / "runs" / "oasis2" / "run1"
    (run_root / "configs").mkdir(parents=True)
    (run_root / "configs" / "resolved_config.json").write_text(
        json.dumps(
            {
                "training": {
                    "model": {"architecture": "resnet50_multimodal"},
                    "data": {"image_size": [96, 96, 96]},
                }
            }
        ),
        encoding="utf-8",
    )

    assert _resolve_model_config_path(run_root=run_root, settings=settings) == multimodal_config.resolve()
    assert _resolve_image_size(run_root=run_root) == [96, 96, 96]
    assert _balanced_accuracy({"sensitivity": 0.7, "specificity": 0.5, "accuracy": 0.1}) == 0.6


def test_oasis2_multimodal_v2_config_keeps_reliability_pipeline() -> None:
    cfg = load_research_oasis_training_config(Path("configs/oasis2_train_multimodal_v2.yaml"))

    assert cfg.run_name == "oasis2_multimodal_v2"
    assert cfg.model.architecture == "resnet50_multimodal"
    assert cfg.model_config_path == Path("configs/oasis2_multimodal_model.yaml")
    assert cfg.data.image_size == (96, 96, 96)
    assert cfg.loss.temporal_lambda == 0.15


def test_temporal_audit_uses_meta_session_ids(tmp_path: Path, capsys) -> None:
    from scripts.audit_temporal_paradoxes import main

    predictions = tmp_path / "predictions.csv"
    output = tmp_path / "audit.json"
    pd.DataFrame(
        [
            {
                "sample_id": "OAS2_0001",
                "meta_subject_id": "OAS2_0001",
                "meta_session_id": "OAS2_0001_MR1",
                "probability_class_1": 0.9,
            },
            {
                "sample_id": "OAS2_0001",
                "meta_subject_id": "OAS2_0001",
                "meta_session_id": "OAS2_0001_MR2",
                "probability_class_1": 0.5,
            },
        ]
    ).to_csv(predictions, index=False)

    import sys

    old_argv = sys.argv
    sys.argv = [
        "audit_temporal_paradoxes.py",
        "--predictions-csv",
        str(predictions),
        "--output-json",
        str(output),
    ]
    try:
        main()
    finally:
        sys.argv = old_argv

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["paradoxes"][0]["visit_t_id"] == "OAS2_0001_MR1"
    assert payload["paradoxes"][0]["visit_t_plus_1_id"] == "OAS2_0001_MR2"


def test_oasis2_leaderboard_prefers_balanced_calibration_and_sorts(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    best = runs_root / "best_run" / "evaluation" / "post_train_test_best_model_threshold_balanced_accuracy"
    other = runs_root / "other_run" / "evaluation" / "post_train_test_best_model"
    best.mkdir(parents=True)
    other.mkdir(parents=True)
    (best / "metrics.json").write_text(
        json.dumps(
            {
                "auroc": 0.72,
                "accuracy": 0.63,
                "balanced_accuracy": 0.65,
                "sensitivity": 0.74,
                "specificity": 0.57,
                "f1": 0.61,
                "threshold": 0.47,
                "review_required_count": 31,
                "subject_consensus": {"auroc": 0.68},
            }
        ),
        encoding="utf-8",
    )
    (best / "predictions.csv").write_text("sample_id\nx\n", encoding="utf-8")
    (other / "metrics.json").write_text(json.dumps({"auroc": 0.4}), encoding="utf-8")
    (other / "predictions.csv").write_text("sample_id\nx\n", encoding="utf-8")

    rows = collect_run_rows(runs_root, split_manifest_root=None)

    assert rows[0]["run_name"] == "best_run"
    assert rows[0]["test_balanced_acc"] == 0.65
    assert rows[0]["threshold"] == 0.47
    assert rows[0]["subject_consensus_auroc"] == 0.68

    (best / "metrics.json").write_text(
        json.dumps({"auroc": 0.72, "sensitivity": 0.7, "specificity": 0.5}),
        encoding="utf-8",
    )
    rows = collect_run_rows(runs_root, split_manifest_root=None)
    assert rows[0]["test_balanced_acc"] == 0.6
