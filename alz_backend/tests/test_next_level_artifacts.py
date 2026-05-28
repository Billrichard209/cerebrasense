"""Tests for the next-level model board and OASIS-2 progression artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.configs.runtime import AppSettings
from src.evaluation.next_level import (
    DECISION_SUPPORT_NOTE,
    build_model_board,
    build_next_level_artifacts,
    build_oasis2_progression_panel,
    build_reviewer_handoff_pack,
)


def _settings(tmp_path: Path) -> AppSettings:
    project_root = tmp_path / "alz_backend"
    data_root = project_root / "data"
    outputs_root = project_root / "outputs"
    data_root.mkdir(parents=True, exist_ok=True)
    outputs_root.mkdir(parents=True, exist_ok=True)
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


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_evidence(settings: AppSettings) -> Path:
    _write_json(
        settings.outputs_root / "model_registry" / "oasis_current_baseline.json",
        {
            "run_name": "oasis_baseline",
            "recommended_threshold": 0.5,
            "test_metrics": {
                "auroc": 0.879,
                "f1": 0.848,
                "accuracy": 0.84,
                "sensitivity": 0.82,
                "specificity": 0.86,
                "review_required_count": 2,
                "sample_count": 40,
            },
        },
    )
    _write_json(
        settings.outputs_root / "model_registry" / "oasis_candidate_v3.json",
        {
            "run_name": "oasis_candidate_v3",
            "test_metrics": {
                "auroc": 0.82,
                "f1": 0.78,
                "accuracy": 0.79,
                "sensitivity": 0.76,
                "specificity": 0.81,
                "sample_count": 40,
            },
        },
    )
    oasis2_eval = (
        settings.outputs_root
        / "runs"
        / "oasis2"
        / "oasis2_unit"
        / "evaluation"
        / "post_train_test_best_model_threshold_youden_index"
    )
    _write_json(
        oasis2_eval / "metrics.json",
        {
            "auroc": 0.655,
            "f1": 0.61,
            "accuracy": 0.63,
            "sensitivity": 0.64,
            "specificity": 0.62,
            "review_required_count": 1,
            "sample_count": 4,
            "subject_consensus": {"auroc": 0.69, "f1": 0.64},
        },
    )
    predictions_path = oasis2_eval / "predictions.csv"
    pd.DataFrame(
        [
            {
                "sample_id": "s1_v1",
                "meta_subject_id": "s1",
                "meta_session_id": "ses1",
                "meta_visit_number": 1,
                "true_label": 0,
                "predicted_label": 1,
                "probability_class_1": 0.80,
                "confidence_level": "low",
                "normalized_entropy": 0.95,
                "review_flag": True,
            },
            {
                "sample_id": "s1_v2",
                "meta_subject_id": "s1",
                "meta_session_id": "ses2",
                "meta_visit_number": 2,
                "true_label": 1,
                "predicted_label": 0,
                "probability_class_1": 0.60,
                "confidence_level": "medium",
                "normalized_entropy": 0.55,
                "review_flag": False,
            },
            {
                "sample_id": "s2_v1",
                "meta_subject_id": "s2",
                "meta_session_id": "ses1",
                "meta_visit_number": 1,
                "true_label": 0,
                "predicted_label": 0,
                "probability_class_1": 0.20,
                "confidence_level": "high",
                "normalized_entropy": 0.25,
                "review_flag": False,
            },
        ]
    ).to_csv(predictions_path, index=False)
    return predictions_path


def test_model_board_ranks_oasis_tracks_and_keeps_disclaimer(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _seed_evidence(settings)

    board = build_model_board(settings=settings)

    assert board["decision_support_note"] == DECISION_SUPPORT_NOTE
    assert board["recommendation"] == "keep_oasis1_active"
    assert {entry["model_id"] for entry in board["entries"]} >= {
        "oasis1_active",
        "oasis1_candidate::oasis_candidate_v3",
        "oasis2::oasis2_unit",
    }
    assert board["entries"][0]["run_name"] == "oasis_baseline"


def test_progression_panel_detects_subject_risk_patterns(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    predictions_path = _seed_evidence(settings)

    panel, cases = build_oasis2_progression_panel(predictions_csv_path=predictions_path, settings=settings)

    assert panel["decision_support_note"] == DECISION_SUPPORT_NOTE
    assert panel["subject_count"] == 2
    assert panel["temporal_paradox_count"] == 1
    assert panel["mixed_label_subject_count"] == 1
    assert panel["high_priority_subject_count"] == 1
    assert cases.iloc[0]["subject_id"] == "s1"


def test_reviewer_handoff_pack_groups_hard_cases(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    predictions_path = _seed_evidence(settings)
    progression, cases = build_oasis2_progression_panel(predictions_csv_path=predictions_path, settings=settings)

    handoff = build_reviewer_handoff_pack(
        predictions_csv_path=predictions_path,
        progression=progression,
        case_frame=cases,
        settings=settings,
    )

    assert handoff["decision_support_note"] == DECISION_SUPPORT_NOTE
    assert handoff["category_counts"]["temporal_paradox_subjects"] == 1
    assert handoff["category_counts"]["false_positives"] == 1
    assert handoff["category_counts"]["false_negatives"] == 1
    assert handoff["category_counts"]["mixed_label_subjects"] == 1
    assert handoff["review_queue"]["cases"][0]["case_type"] == "temporal_paradox_subject"


def test_next_level_bundle_writes_frontend_payload(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _seed_evidence(settings)
    frontend_payload = tmp_path / "frontend_demo" / "data" / "research_mode.json"

    artifacts = build_next_level_artifacts(settings=settings, frontend_payload_path=frontend_payload)

    assert artifacts.model_board_json_path.exists()
    assert artifacts.model_board_md_path.exists()
    assert artifacts.progression_json_path.exists()
    assert artifacts.progression_md_path.exists()
    assert artifacts.progression_cases_csv_path.exists()
    assert artifacts.handoff_pack_json_path.exists()
    assert artifacts.handoff_pack_md_path.exists()
    assert artifacts.demo_payload_json_path == frontend_payload
    payload = json.loads(frontend_payload.read_text(encoding="utf-8"))
    assert payload["decision_support_note"] == DECISION_SUPPORT_NOTE
    assert payload["oasis2_candidate"]["run_name"] == "oasis2_unit"
    assert payload["candidate_status"]["status"] == "candidate_only"
    assert {blocker["metric"] for blocker in payload["promotion_blockers"]} >= {
        "test_auroc",
        "temporal_paradox_count",
    }
    assert payload["review_queue"]["total_case_count"] > 0
    assert payload["paradox_summary"]["temporal_paradox_count"] == payload["progression"]["temporal_paradox_count"]
    assert payload["handoff_pack_paths"]["json"].endswith("review_handoff_pack.json")
