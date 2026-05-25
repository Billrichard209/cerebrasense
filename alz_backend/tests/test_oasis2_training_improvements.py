"""Tests for OASIS-2 training improvement helpers."""

from __future__ import annotations

from src.data.oasis2_loaders import filter_oasis2_train_records
from src.training.oasis_research import LossConfig, _effective_temporal_lambda, resolve_loss_class_weights


def test_effective_temporal_lambda_warmup() -> None:
    loss_cfg = LossConfig(temporal_lambda=0.05, temporal_lambda_warmup_epochs=10)
    assert _effective_temporal_lambda(loss_cfg, 5) == 0.0
    assert _effective_temporal_lambda(loss_cfg, 11) == 0.05


def test_resolve_loss_class_weights_from_counts() -> None:
    weights = resolve_loss_class_weights(None, label_counts={0: 180, 1: 79})
    assert weights is not None
    assert weights[0] < weights[1]


def test_filter_oasis2_train_records_stable_only() -> None:
    records = [
        {"subject_id": "A", "label": 0, "mixed_label_group": False, "visit_number": 1},
        {"subject_id": "B", "label": 0, "mixed_label_group": True, "visit_number": 1},
        {"subject_id": "B", "label": 1, "mixed_label_group": True, "visit_number": 2},
    ]
    filtered = filter_oasis2_train_records(records, training_cohort="stable_only")
    assert len(filtered) == 1
    assert filtered[0]["subject_id"] == "A"


def test_filter_oasis2_train_records_visit_filter() -> None:
    records = [
        {"subject_id": "B", "label": 0, "mixed_label_group": True, "visit_number": 1},
        {"subject_id": "B", "label": 0, "mixed_label_group": True, "visit_number": 2},
        {"subject_id": "B", "label": 1, "mixed_label_group": True, "visit_number": 3},
    ]
    filtered = filter_oasis2_train_records(records, training_cohort="visit_filter")
    visit_numbers = {int(record["visit_number"]) for record in filtered}
    assert visit_numbers == {3}
