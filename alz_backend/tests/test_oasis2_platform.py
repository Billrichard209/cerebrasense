"""Tests for OASIS-2 platform helpers (dashboard API, promotion gates)."""

from __future__ import annotations

import json
from pathlib import Path

from src.api.services import build_dashboard_payload, build_oasis2_longitudinal_dashboard_payload
from scripts.promote_oasis2_run import evaluate_promotion_gates


def test_build_dashboard_payload_handles_missing_csvs() -> None:
    payload = build_dashboard_payload()
    assert "subjects" in payload or "error" in payload


def test_promotion_gates_block_weak_metrics(tmp_path: Path, monkeypatch) -> None:
    settings_root = tmp_path / "outputs"
    run_name = "weak_run"
    run_root = settings_root / "runs" / "oasis2" / run_name
    eval_root = run_root / "evaluation" / "post_train_test_best_model_threshold_balanced_accuracy"
    eval_root.mkdir(parents=True)
    (eval_root / "metrics.json").write_text(
        json.dumps(
            {
                "auroc": 0.55,
                "balanced_accuracy": 0.60,
                "specificity": 0.50,
                "sensitivity": 0.70,
                "subject_consensus": {"auroc": 0.60},
            }
        ),
        encoding="utf-8",
    )
    (settings_root / "reports" / "longitudinal").mkdir(parents=True)
    (settings_root / "reports" / "longitudinal" / f"audit_{run_name}.json").write_text(
        json.dumps({"paradox_count": 0}),
        encoding="utf-8",
    )

    class FakeSettings:
        outputs_root = settings_root
        project_root = tmp_path

    passed, failures, _ = evaluate_promotion_gates(run_name=run_name, settings=FakeSettings())
    assert passed is False
    assert failures
