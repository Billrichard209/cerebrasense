"""Tests for the CerebraSense Control Tower evidence bundle."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.configs.runtime import AppSettings
from src.evaluation.control_tower import (
    build_cerebrasense_control_tower,
    build_control_tower_payload,
    build_next_best_action,
)
from src.evaluation.next_level import DECISION_SUPPORT_NOTE


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


def _seed_control_tower_evidence(settings: AppSettings) -> None:
    _write_json(
        settings.outputs_root / "model_registry" / "oasis_current_baseline.json",
        {
            "run_name": "oasis1_active_anchor",
            "recommended_threshold": 0.5,
            "test_metrics": {
                "auroc": 0.879,
                "f1": 0.848,
                "accuracy": 0.84,
                "sensitivity": 0.82,
                "specificity": 0.86,
                "review_required_count": 2,
                "sample_count": 60,
            },
        },
    )
    eval_root = (
        settings.outputs_root
        / "runs"
        / "oasis2"
        / "oasis2_multimodal_v1"
        / "evaluation"
        / "post_train_test_best_model_threshold_balanced_accuracy"
    )
    _write_json(
        eval_root / "metrics.json",
        {
            "auroc": 0.7250293772032903,
            "f1": 0.642857,
            "accuracy": 0.63,
            "balanced_accuracy": 0.6533490011750881,
            "sensitivity": 0.666667,
            "specificity": 0.592593,
            "review_required_count": 31,
            "sample_count": 60,
            "subject_consensus": {"auroc": 0.6818181818181818, "f1": 0.64},
        },
    )
    pd.DataFrame(
        [
            {
                "sample_id": f"s1_v{visit}",
                "meta_subject_id": "s1",
                "meta_session_id": f"ses{visit}",
                "meta_visit_number": visit,
                "true_label": int(visit % 2 == 0),
                "predicted_label": int(score >= 0.5),
                "probability_class_1": score,
                "confidence_level": "low" if visit == 1 else "medium",
                "normalized_entropy": 0.7,
                "review_flag": visit in {1, 2},
            }
            for visit, score in enumerate([0.92, 0.72, 0.54, 0.34, 0.12], start=1)
        ]
    ).to_csv(eval_root / "predictions.csv", index=False)


def test_control_tower_artifacts_extend_research_payload(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _seed_control_tower_evidence(settings)
    frontend_payload = tmp_path / "frontend_demo" / "data" / "research_mode.json"

    artifacts = build_cerebrasense_control_tower(
        settings=settings,
        frontend_payload_path=frontend_payload,
    )

    assert artifacts.control_tower_json_path.exists()
    assert artifacts.control_tower_md_path.exists()
    assert artifacts.research_evidence_packet_md_path.exists()
    payload = json.loads(frontend_payload.read_text(encoding="utf-8"))
    assert payload["decision_support_note"] == DECISION_SUPPORT_NOTE
    assert payload["control_tower_status"]["status"] == "candidate_blocked"
    assert payload["control_tower_status"]["candidate_only"] is True
    assert payload["next_best_action"]["id"] == "run_v3_temporal_consistency"
    assert payload["evidence_health"]["promotion_blocker_count"] > 0
    assert payload["deployment_health"]["onnx_export_allowed"] is False
    assert payload["active_vs_candidate_deltas"]["decision"] == "keep_oasis1_active_until_oasis2_gates_pass"


def test_control_tower_payload_is_portable_and_research_only(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _seed_control_tower_evidence(settings)
    frontend_payload = tmp_path / "frontend_demo" / "data" / "research_mode.json"

    build_cerebrasense_control_tower(settings=settings, frontend_payload_path=frontend_payload)

    payload_text = frontend_payload.read_text(encoding="utf-8").lower()
    assert str(tmp_path).lower() not in payload_text
    assert "c:\\" not in payload_text
    assert "onedrive" not in payload_text
    assert "not diagnosis" in payload_text
    assert "not a medical device" in payload_text
    assert "clinical deployment" not in payload_text


def test_next_best_action_rules_are_ordered() -> None:
    assert build_next_best_action({"oasis2_candidate": {}})["id"] == "evaluate_or_import_oasis2_candidate"

    assert (
        build_next_best_action(
            {
                "oasis2_candidate": {"run_name": "oasis2_multimodal_v1", "review_required_count": 31},
                "promotion_blockers": [{"metric": "temporal_paradox_count"}],
                "progression": {"temporal_paradox_count": 4},
                "review_queue": {"total_case_count": 31},
                "deployment_readiness": {"onnx_export_allowed": False},
            }
        )["id"]
        == "run_v3_temporal_consistency"
    )

    assert (
        build_next_best_action(
            {
                "oasis2_candidate": {"run_name": "oasis2_v2", "review_required_count": 31},
                "promotion_blockers": [{"metric": "specificity"}],
                "progression": {"temporal_paradox_count": 0},
                "review_queue": {"total_case_count": 0},
                "deployment_readiness": {"onnx_export_allowed": False},
            }
        )["id"]
        == "review_hard_cases"
    )

    assert (
        build_next_best_action(
            {
                "oasis2_candidate": {
                    "run_name": "oasis2_v4",
                    "review_required_count": 4,
                    "subject_consensus_auroc": 0.72,
                },
                "promotion_blockers": [{"metric": "subject_consensus_auroc"}],
                "progression": {"temporal_paradox_count": 0},
                "review_queue": {"total_case_count": 0},
                "deployment_readiness": {"onnx_export_allowed": False},
            }
        )["id"]
        == "run_v4_subject_consensus"
    )


def test_control_tower_gates_pass_marks_export_review_ready_not_promoted() -> None:
    payload = build_control_tower_payload(
        research_payload={
            "decision_support_note": DECISION_SUPPORT_NOTE,
            "active_model": {"run_name": "oasis1_active_anchor", "auroc": 0.87, "specificity": 0.86},
            "oasis2_candidate": {
                "run_name": "oasis2_candidate_pass",
                "auroc": 0.82,
                "specificity": 0.75,
                "review_required_count": 5,
                "subject_consensus_auroc": 0.79,
            },
            "promotion_blockers": [],
            "progression": {"temporal_paradox_count": 0},
            "review_queue": {"total_case_count": 5},
            "deployment_readiness": {"onnx_export_allowed": True},
        },
        model_board={"entry_count": 2},
        run_registry={"integrity_status": "pass"},
        progression={"trajectory_review_subject_count": 0},
        model_cards={"card_count": 2},
        handoff_pack={"review_queue": {"total_case_count": 5}, "error_learning_loop": {"taxonomy": []}},
        deployment_readiness={
            "readiness_status": "export_ready_after_review",
            "onnx_export_allowed": True,
            "benchmark_status": "run_latency_benchmark_before_demo_claims",
        },
        demo_bundle_manifest={"actions": []},
        source_artifacts={},
    )

    assert payload["control_tower_status"]["status"] == "promotion_review_ready"
    assert payload["control_tower_status"]["candidate_only"] is True
    assert payload["next_best_action"]["id"] == "prepare_onnx_export_review"
    assert "auto" not in json.dumps(payload["control_tower_status"]).lower()


def test_control_tower_windows_launchers_are_quoted() -> None:
    project_root = Path(__file__).resolve().parents[1]
    workspace_root = project_root.parent
    wrappers = [
        workspace_root / "build_cerebrasense_control_tower.cmd",
        project_root / "build_cerebrasense_control_tower.cmd",
    ]

    for wrapper in wrappers:
        text = wrapper.read_text(encoding="utf-8")
        assert wrapper.exists()
        assert "build_cerebrasense_control_tower.py" in text
        assert "--frontend-payload-path" in text
        assert '"%ROOT%' in text or '".\\alz_backend' in text
