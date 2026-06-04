"""Tests for the next-level model board and OASIS-2 progression artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.configs.runtime import AppSettings
from src.evaluation.next_level import (
    DECISION_SUPPORT_NOTE,
    OASIS2_EXPERIMENT_LADDER,
    OASIS2_NEXT_CANDIDATE_RUN_NAME,
    build_candidate_comparison_report,
    build_frontend_research_payload,
    build_deployment_readiness,
    build_demo_bundle_manifest,
    build_failed_ablations,
    build_model_board,
    build_model_cards,
    build_next_level_artifacts,
    build_oasis2_progression_panel,
    build_oasis2_run_registry,
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


def _write_oasis2_run(
    settings: AppSettings,
    *,
    run_name: str,
    metrics: dict,
    rows: list[dict],
) -> None:
    eval_root = (
        settings.outputs_root
        / "runs"
        / "oasis2"
        / run_name
        / "evaluation"
        / "post_train_test_best_model"
    )
    eval_root.mkdir(parents=True, exist_ok=True)
    _write_json(eval_root / "metrics.json", metrics)
    pd.DataFrame(rows).to_csv(eval_root / "predictions.csv", index=False)


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
    assert board["promotion_gates"]["test_auroc"] == 0.80
    assert board["experiment_ladder"][0]["stage"] == "v2_specificity"


def test_model_board_marks_v3_failed_ablation_and_points_to_v3b(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _seed_evidence(settings)
    _write_oasis2_run(
        settings,
        run_name="oasis2_multimodal_v1",
        metrics={
            "auroc": 0.7250293772032903,
            "balanced_accuracy": 0.6533490011750881,
            "f1": 0.607143,
            "sensitivity": 0.73913,
            "specificity": 0.567568,
            "review_required_count": 31,
            "sample_count": 60,
            "subject_consensus": {"auroc": 0.6818181818181818},
        },
        rows=[
            {"true_label": 0, "predicted_label": 1, "probability_class_1": 0.55, "confidence_level": "low"},
            {"true_label": 1, "predicted_label": 1, "probability_class_1": 0.72, "confidence_level": "high"},
        ],
    )
    _write_oasis2_run(
        settings,
        run_name="oasis2_multimodal_v3_temporal",
        metrics={
            "auroc": 0.5593419506462984,
            "balanced_accuracy": 0.5346650998824912,
            "f1": 0.542857,
            "sensitivity": 0.826087,
            "specificity": 0.243243,
            "review_required_count": 58,
            "sample_count": 60,
            "subject_consensus": {"auroc": 0.5833333333333334},
        },
        rows=[
            {"true_label": 0, "predicted_label": 1, "probability_class_1": 0.48, "confidence_level": "low"},
            {"true_label": 1, "predicted_label": 0, "probability_class_1": 0.33, "confidence_level": "low"},
            {"true_label": 0, "predicted_label": 1, "probability_class_1": 0.44, "confidence_level": "medium"},
        ],
    )

    board = build_model_board(settings=settings)
    failed = build_failed_ablations(board)
    comparison = build_candidate_comparison_report(board)
    payload = build_frontend_research_payload(board, {"temporal_paradox_count": 0})

    assert board["next_candidate_run_name"] == OASIS2_NEXT_CANDIDATE_RUN_NAME
    assert failed[0]["run_name"] == "oasis2_multimodal_v3_temporal"
    assert failed[0]["status"] == "failed_ablation"
    assert comparison["status"] == "v3_failed_ablation"
    assert comparison["failure_mode"] == "model_discrimination_collapse"
    assert comparison["metric_deltas"]["auroc_delta"] < -0.1
    assert comparison["hard_case_counts"]["comparison"]["false_positive_count"] == 2
    assert payload["failed_ablations"][0]["status"] == "failed_ablation"
    assert payload["next_candidate_run_name"] == OASIS2_NEXT_CANDIDATE_RUN_NAME
    assert payload["candidate_comparison"]["next_candidate_run_name"] == OASIS2_NEXT_CANDIDATE_RUN_NAME


def test_oasis2_run_registry_tracks_ladder_and_integrity(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _seed_evidence(settings)
    board = build_model_board(settings=settings)

    registry = build_oasis2_run_registry(board, settings=settings)

    assert registry["decision_support_note"] == DECISION_SUPPORT_NOTE
    assert registry["integrity_status"] == "pass"
    assert registry["unique_run_names"] is True
    assert {stage["stage"] for stage in registry["experiment_ladder"]} == {
        stage["stage"] for stage in OASIS2_EXPERIMENT_LADDER
    }
    assert registry["unassigned_run_names"] == ["oasis2_unit"]


def test_progression_panel_detects_subject_risk_patterns(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    predictions_path = _seed_evidence(settings)

    panel, cases = build_oasis2_progression_panel(predictions_csv_path=predictions_path, settings=settings)

    assert panel["decision_support_note"] == DECISION_SUPPORT_NOTE
    assert panel["subject_count"] == 2
    assert panel["temporal_paradox_count"] == 1
    assert panel["mixed_label_subject_count"] == 1
    assert panel["high_priority_subject_count"] == 1
    assert panel["trajectory_review_subject_count"] >= 1
    assert cases.iloc[0]["subject_id"] == "s1"
    assert "trajectory_score" in cases.columns
    assert cases.iloc[0]["trajectory_status"] in {"review_required", "progression_watch"}
    assert cases.iloc[0]["reviewer_reasons"]


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
    assert handoff["error_learning_loop"]["decision_policy"].startswith("Use reviewer outcomes")
    assert handoff["review_queue"]["cases"][0]["case_type"] == "temporal_paradox_subject"


def test_model_cards_and_deployment_readiness_preserve_candidate_boundary(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    predictions_path = _seed_evidence(settings)
    board = build_model_board(settings=settings)
    progression, cases = build_oasis2_progression_panel(predictions_csv_path=predictions_path, settings=settings)
    handoff = build_reviewer_handoff_pack(
        predictions_csv_path=predictions_path,
        progression=progression,
        case_frame=cases,
        settings=settings,
    )

    cards = build_model_cards(board, progression, handoff)
    readiness = build_deployment_readiness(board, progression, settings=settings)
    demo_manifest = build_demo_bundle_manifest(board, handoff, settings=settings)

    assert cards["decision_support_note"] == DECISION_SUPPORT_NOTE
    assert any(card["status"] == "longitudinal_candidate" for card in cards["cards"])
    oasis2_card = next(card for card in cards["cards"] if card["dataset"] == "oasis2")
    assert "Drop-in OASIS-1 replacement" in oasis2_card["not_intended_for"]
    assert readiness["readiness_status"] == "blocked_candidate"
    assert readiness["onnx_export_allowed"] is False
    assert readiness["benchmark_targets"]["gpu_latency_ms_max"] == 300
    assert {action["id"] for action in demo_manifest["actions"]} == {
        "stable_oasis1_demo",
        "oasis2_candidate_demo",
        "review_hard_cases",
    }


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
    assert artifacts.run_registry_json_path.exists()
    assert artifacts.run_registry_md_path.exists()
    assert artifacts.model_cards_json_path.exists()
    assert artifacts.model_cards_md_path.exists()
    assert artifacts.deployment_readiness_json_path.exists()
    assert artifacts.deployment_readiness_md_path.exists()
    assert artifacts.demo_bundle_manifest_json_path.exists()
    assert artifacts.demo_bundle_manifest_md_path.exists()
    assert artifacts.candidate_comparison_json_path.exists()
    assert artifacts.candidate_comparison_md_path.exists()
    assert artifacts.demo_payload_json_path == frontend_payload
    payload = json.loads(frontend_payload.read_text(encoding="utf-8"))
    assert payload["decision_support_note"] == DECISION_SUPPORT_NOTE
    assert payload["oasis2_candidate"]["run_name"] == "oasis2_unit"
    assert payload["candidate_status"]["status"] == "candidate_only"
    assert payload["next_candidate_run_name"] == OASIS2_NEXT_CANDIDATE_RUN_NAME
    assert "failed_ablations" in payload
    assert "candidate_comparison" in payload
    assert {blocker["metric"] for blocker in payload["promotion_blockers"]} >= {
        "test_auroc",
        "temporal_paradox_count",
    }
    assert payload["review_queue"]["total_case_count"] > 0
    assert payload["active_vs_candidate"]["decision"] == "keep_oasis1_active_until_oasis2_gates_pass"
    assert payload["run_registry"]["integrity_status"] == "pass"
    assert payload["trajectory_intelligence"]["review_subject_count"] >= 1
    assert payload["error_learning_loop"]["taxonomy"]
    assert payload["model_cards"]
    assert payload["deployment_readiness"]["onnx_export_allowed"] is False
    assert len(payload["demo_bundle_actions"]["actions"]) == 3
    assert payload["paradox_summary"]["temporal_paradox_count"] == payload["progression"]["temporal_paradox_count"]
    assert payload["handoff_pack_paths"]["json"].endswith("review_handoff_pack.json")
    payload_text = json.dumps(payload).lower()
    assert "not diagnosis" in payload_text
    assert "not a medical device" in payload_text
