"""Next-level evidence artifacts for OASIS-first model review."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.configs.runtime import AppSettings, get_app_settings
from src.utils.io_utils import ensure_directory

DECISION_SUPPORT_NOTE = (
    "Research decision-support only. These artifacts are not diagnosis, not a medical device, "
    "and must be reviewed with source imaging and clinical context."
)


@dataclass(slots=True)
class NextLevelArtifacts:
    """Paths written by the next-level evidence bundle."""

    output_root: Path
    model_board_json_path: Path
    model_board_md_path: Path
    progression_json_path: Path
    progression_md_path: Path
    progression_cases_csv_path: Path
    handoff_pack_json_path: Path
    handoff_pack_md_path: Path
    model_cards_json_path: Path
    model_cards_md_path: Path
    deployment_readiness_json_path: Path
    deployment_readiness_md_path: Path
    demo_bundle_manifest_json_path: Path
    demo_bundle_manifest_md_path: Path
    run_registry_json_path: Path
    run_registry_md_path: Path
    demo_payload_json_path: Path


OASIS2_BASELINE_CANDIDATE = {
    "run_name": "oasis2_multimodal_v1",
    "test_auroc": 0.7250293772032903,
    "balanced_accuracy": 0.6533490011750881,
    "subject_consensus_auroc": 0.6818181818181818,
    "review_required_count": 31,
    "temporal_paradox_count": 4,
}

OASIS2_V2_ACCEPTANCE_TARGETS = {
    "test_auroc": 0.7250293772032903,
    "subject_consensus_auroc": 0.72,
    "balanced_accuracy": 0.68,
    "review_required_count_max": 30,
    "temporal_paradox_count_max": 1,
}

OASIS2_PROMOTION_GATES = {
    "test_auroc": 0.80,
    "balanced_accuracy": 0.75,
    "specificity": 0.70,
    "subject_consensus_auroc": 0.78,
    "temporal_paradox_count_max": 0,
}

OASIS2_EXPERIMENT_LADDER = [
    {
        "stage": "v2_specificity",
        "run_name": "oasis2_multimodal_v2",
        "config_path": "configs/oasis2_train_multimodal_v2.yaml",
        "objective": "Improve specificity, balanced accuracy, subject AUROC, review burden, and paradox count without changing the multimodal pipeline.",
        "promotion_role": "candidate_refresh",
    },
    {
        "stage": "v3_temporal_consistency",
        "run_name": "oasis2_multimodal_v3_temporal",
        "config_path": "configs/oasis2_train_multimodal_v3_temporal.yaml",
        "objective": "Increase temporal consistency pressure and reduce visit-to-visit contradictions.",
        "promotion_role": "temporal_ablation",
    },
    {
        "stage": "v4_subject_consensus",
        "run_name": "oasis2_multimodal_v4_subject_consensus",
        "config_path": "configs/oasis2_train_multimodal_v4_subject_consensus.yaml",
        "objective": "Optimize subject-level agreement and handoff burden after the temporal candidate stabilizes.",
        "promotion_role": "subject_consensus_ablation",
    },
    {
        "stage": "multi_seed_confirmation",
        "run_name": "oasis2_multimodal_reliability_multiseed",
        "config_path": "run_oasis2_multiseed_eval.cmd",
        "objective": "Confirm the best candidate is not a lucky seed or split artifact.",
        "promotion_role": "stability_confirmation",
    },
]

OASIS2_REVIEW_THRESHOLDS = {
    "uncertainty_band_low": 0.40,
    "uncertainty_band_high": 0.60,
    "high_risk_review_min": 0.70,
    "temporal_drop_epsilon": 0.15,
    "trajectory_score_review_min": 0.55,
}

DEPLOYMENT_BENCHMARK_TARGETS = {
    "cpu_latency_ms_max": 1500,
    "gpu_latency_ms_max": 300,
    "model_size_mb_max": 600,
}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _portable_path(path: Path, root: Path) -> str:
    """Return a repo-relative path when possible for frontend/demo payloads."""

    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError:
        return str(resolved_path)


def _metric(metrics: dict[str, Any] | None, key: str, default: float = 0.0) -> float:
    if not isinstance(metrics, dict):
        return default
    try:
        return float(metrics.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def _balanced_accuracy_from_entry(entry: dict[str, Any]) -> float:
    sensitivity = _metric(entry, "sensitivity")
    specificity = _metric(entry, "specificity")
    if sensitivity == 0.0 and specificity == 0.0:
        return _metric(entry, "balanced_accuracy")
    return (sensitivity + specificity) / 2.0


def _round_metric(value: Any, digits: int = 6) -> float:
    try:
        return round(float(value or 0.0), digits)
    except (TypeError, ValueError):
        return 0.0


def _run_name_from_predictions_path(path: Path | None) -> str | None:
    if path is None:
        return None
    parts = list(path.parts)
    for index, part in enumerate(parts):
        if part == "oasis2" and index + 1 < len(parts):
            return parts[index + 1]
    return None


def _row_value(row: pd.Series, key: str, default: Any = None) -> Any:
    value = row.get(key, default)
    if pd.isna(value):
        return default
    return value


def _prediction_case(row: pd.Series, *, case_type: str, priority: str, reason: str) -> dict[str, Any]:
    return {
        "case_type": case_type,
        "priority": priority,
        "subject_id": str(_row_value(row, "meta_subject_id", _row_value(row, "sample_id", ""))),
        "session_id": str(_row_value(row, "meta_session_id", _row_value(row, "sample_id", ""))),
        "true_label": int(_row_value(row, "true_label", -1)),
        "predicted_label": int(_row_value(row, "predicted_label", -1)),
        "risk_score": round(float(_row_value(row, "probability_class_1", _row_value(row, "calibrated_probability_score", 0.0))), 6),
        "confidence_level": str(_row_value(row, "confidence_level", "unknown")),
        "review_required": str(_row_value(row, "review_flag", "False")).lower() in {"true", "1", "yes"},
        "reason": reason,
    }


def _candidate_score(metrics: dict[str, Any]) -> float:
    sensitivity = _metric(metrics, "sensitivity", _metric(metrics, "recall_sensitivity"))
    specificity = _metric(metrics, "specificity")
    balance = 1.0 - abs(sensitivity - specificity)
    review_count = _metric(metrics, "review_required_count")
    sample_count = max(_metric(metrics, "sample_count", 1.0), 1.0)
    review_penalty = review_count / sample_count
    return round(
        (0.35 * _metric(metrics, "auroc"))
        + (0.25 * _metric(metrics, "f1"))
        + (0.25 * max(balance, 0.0))
        + (0.15 * _metric(metrics.get("subject_consensus", {}), "auroc")),
        6,
    ) - round(0.15 * review_penalty, 6)


def _entry_promotion_gate_status(entry: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "test_auroc": entry.get("auroc"),
        "balanced_accuracy": _balanced_accuracy_from_entry(entry),
        "specificity": entry.get("specificity"),
        "subject_consensus_auroc": entry.get("subject_consensus_auroc"),
    }
    failures = [
        {
            "metric": metric,
            "actual": _round_metric(actual),
            "target": target,
            "comparator": ">=",
        }
        for metric, actual, target in [
            ("test_auroc", checks["test_auroc"], OASIS2_PROMOTION_GATES["test_auroc"]),
            ("balanced_accuracy", checks["balanced_accuracy"], OASIS2_PROMOTION_GATES["balanced_accuracy"]),
            ("specificity", checks["specificity"], OASIS2_PROMOTION_GATES["specificity"]),
            (
                "subject_consensus_auroc",
                checks["subject_consensus_auroc"],
                OASIS2_PROMOTION_GATES["subject_consensus_auroc"],
            ),
        ]
        if _round_metric(actual) < float(target)
    ]
    return {
        "automated_metric_gates_pass": len(failures) == 0,
        "failures": failures,
        "promotion_gates": dict(OASIS2_PROMOTION_GATES),
    }


def _entry(
    *,
    model_id: str,
    dataset: str,
    run_name: str,
    role: str,
    metrics: dict[str, Any],
    metrics_path: Path | None = None,
    threshold: float | None = None,
) -> dict[str, Any]:
    sensitivity = _metric(metrics, "sensitivity", _metric(metrics, "recall_sensitivity"))
    specificity = _metric(metrics, "specificity")
    entry = {
        "model_id": model_id,
        "dataset": dataset,
        "run_name": run_name,
        "role": role,
        "metrics_path": None if metrics_path is None else str(metrics_path),
        "threshold": threshold if threshold is not None else metrics.get("threshold"),
        "auroc": _metric(metrics, "auroc"),
        "accuracy": _metric(metrics, "accuracy"),
        "balanced_accuracy": _metric(metrics, "balanced_accuracy", (sensitivity + specificity) / 2.0),
        "f1": _metric(metrics, "f1"),
        "sensitivity": sensitivity,
        "specificity": specificity,
        "balance_gap": round(abs(sensitivity - specificity), 6),
        "review_required_count": int(_metric(metrics, "review_required_count")),
        "subject_consensus_auroc": _metric(metrics.get("subject_consensus", {}), "auroc"),
        "subject_consensus_f1": _metric(metrics.get("subject_consensus", {}), "f1"),
        "candidate_score": _candidate_score(metrics),
        "decision_support_only": True,
    }
    if dataset == "oasis2":
        entry["promotion_gate_status"] = _entry_promotion_gate_status(entry)
    return entry


def _preferred_oasis2_metrics(run_root: Path) -> tuple[dict[str, Any], Path | None, str]:
    evaluation_root = run_root / "evaluation"
    candidates = [
        path
        for path in evaluation_root.glob("post_train_test_best_model_threshold_*/metrics.json")
        if path.exists()
    ]
    candidates.extend(
        path
        for path in [
            evaluation_root / "post_train_test_best_model" / "metrics.json",
            evaluation_root / "test_best_model" / "metrics.json",
        ]
        if path.exists()
    )
    if not candidates:
        return {}, None, "missing_test_metrics"
    path = sorted(candidates, key=lambda item: item.stat().st_mtime, reverse=True)[0]
    return _read_json(path), path, path.parent.name


def _preferred_oasis1_metrics(run_root: Path) -> tuple[dict[str, Any], Path | None, str]:
    evaluation_root = run_root / "evaluation"
    candidates = [
        path
        for path in evaluation_root.glob("post_train_test_best_model_threshold_*/metrics.json")
        if path.exists()
    ]
    candidates.extend(
        path
        for path in [
            evaluation_root / "post_train_test_best_model" / "metrics.json",
            evaluation_root / "test_best_model" / "metrics.json",
            run_root / "metrics" / "final_metrics.json",
        ]
        if path.exists()
    )
    if not candidates:
        return {}, None, "missing_test_metrics"
    path = sorted(candidates, key=lambda item: item.stat().st_mtime, reverse=True)[0]
    return _read_json(path), path, path.parent.name


def _registry_metrics(registry: dict[str, Any]) -> dict[str, Any]:
    for key in ("test_metrics", "metrics", "evaluation_metrics"):
        metrics = registry.get(key)
        if isinstance(metrics, dict):
            return metrics
    return {}


def build_model_board(*, settings: AppSettings | None = None) -> dict[str, Any]:
    """Build a cross-track model board from saved evidence artifacts."""

    resolved_settings = settings or get_app_settings()
    entries: list[dict[str, Any]] = []

    registry_path = resolved_settings.outputs_root / "model_registry" / "oasis_current_baseline.json"
    registry = _read_json(registry_path)
    if registry:
        entries.append(
            _entry(
                model_id="oasis1_active",
                dataset="oasis1",
                run_name=str(registry.get("run_name", "unknown_oasis1_active")),
                role="stable_fallback",
                metrics=_registry_metrics(registry),
                metrics_path=registry_path,
                threshold=registry.get("recommended_threshold"),
            )
        )

    for candidate_registry_path in sorted(
        resolved_settings.outputs_root.glob("model_registry/oasis_candidate*.json")
    ):
        candidate_registry = _read_json(candidate_registry_path)
        metrics = _registry_metrics(candidate_registry)
        if metrics:
            entries.append(
                _entry(
                    model_id=f"oasis1_candidate::{candidate_registry_path.stem}",
                    dataset="oasis1",
                    run_name=str(candidate_registry.get("run_name", candidate_registry_path.stem)),
                    role="candidate_registry",
                    metrics=metrics,
                    metrics_path=candidate_registry_path,
                    threshold=candidate_registry.get("recommended_threshold"),
                )
            )

    oasis1_root = resolved_settings.outputs_root / "runs" / "oasis"
    if oasis1_root.exists():
        for run_root in sorted(path for path in oasis1_root.iterdir() if path.is_dir()):
            metrics, metrics_path, role = _preferred_oasis1_metrics(run_root)
            if metrics:
                entries.append(
                    _entry(
                        model_id=f"oasis1_run::{run_root.name}",
                        dataset="oasis1",
                        run_name=run_root.name,
                        role=role,
                        metrics=metrics,
                        metrics_path=metrics_path,
                    )
                )

    oasis2_root = resolved_settings.outputs_root / "runs" / "oasis2"
    if oasis2_root.exists():
        for run_root in sorted(path for path in oasis2_root.iterdir() if path.is_dir()):
            metrics, metrics_path, role = _preferred_oasis2_metrics(run_root)
            if metrics:
                entries.append(
                    _entry(
                        model_id=f"oasis2::{run_root.name}",
                        dataset="oasis2",
                        run_name=run_root.name,
                        role=role,
                        metrics=metrics,
                        metrics_path=metrics_path,
                    )
                )

    ranked = sorted(entries, key=lambda item: item["candidate_score"], reverse=True)
    active_oasis1 = next((entry for entry in ranked if entry["model_id"] == "oasis1_active"), None)
    best_oasis2 = next((entry for entry in ranked if entry["dataset"] == "oasis2"), None)
    recommendation = "keep_oasis1_active"
    if active_oasis1 and best_oasis2:
        oasis2_is_promising = (
            best_oasis2["auroc"] >= max(0.655, active_oasis1["auroc"] - 0.02)
            and best_oasis2["f1"] >= 0.60
            and best_oasis2["specificity"] > 0.0
            and best_oasis2["sensitivity"] > 0.0
        )
        recommendation = "track_oasis2_longitudinal_candidate" if oasis2_is_promising else "keep_oasis1_active"
    elif best_oasis2:
        recommendation = "track_oasis2_longitudinal_candidate"

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "cerebrasense_model_board",
        "decision_support_note": DECISION_SUPPORT_NOTE,
        "recommendation": recommendation,
        "promotion_gates": dict(OASIS2_PROMOTION_GATES),
        "experiment_ladder": list(OASIS2_EXPERIMENT_LADDER),
        "entry_count": len(ranked),
        "entries": ranked,
        "promotion_briefing": {
            "active_baseline": None if active_oasis1 is None else active_oasis1["run_name"],
            "best_oasis2_candidate": None if best_oasis2 is None else best_oasis2["run_name"],
            "rule": "OASIS-2 is tracked as a longitudinal candidate first; OASIS-1 remains fallback until held-out evidence and review burden clearly improve.",
            "frozen_oasis2_baseline_candidate": dict(OASIS2_BASELINE_CANDIDATE),
        },
    }


def build_oasis2_run_registry(model_board: dict[str, Any], *, settings: AppSettings | None = None) -> dict[str, Any]:
    """Build a compact OASIS-2 run registry with ladder coverage and integrity checks."""

    resolved_settings = settings or get_app_settings()
    entries = [entry for entry in model_board.get("entries", []) if entry.get("dataset") == "oasis2"]
    run_names = [str(entry.get("run_name", "")) for entry in entries if entry.get("run_name")]
    duplicate_run_names = sorted({run_name for run_name in run_names if run_names.count(run_name) > 1})
    ladder_runs = {str(stage["run_name"]): stage for stage in OASIS2_EXPERIMENT_LADDER}
    ladder_status = []
    for stage in OASIS2_EXPERIMENT_LADDER:
        run_name = str(stage["run_name"])
        matched = next((entry for entry in entries if entry.get("run_name") == run_name), None)
        config_path = resolved_settings.project_root / str(stage["config_path"])
        if str(stage["config_path"]).endswith(".cmd"):
            config_path = resolved_settings.workspace_root / str(stage["config_path"])
        ladder_status.append(
            {
                **stage,
                "status": "evaluated" if matched else "planned",
                "config_exists": config_path.exists(),
                "metrics_path": (
                    None
                    if matched is None or not matched.get("metrics_path")
                    else _portable_path(Path(str(matched["metrics_path"])), resolved_settings.workspace_root)
                ),
                "promotion_gate_status": None if matched is None else matched.get("promotion_gate_status"),
            }
        )
    unassigned_runs = sorted(run_name for run_name in run_names if run_name not in ladder_runs)
    missing_metrics = [entry.get("run_name") for entry in entries if not entry.get("metrics_path")]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "oasis2_run_registry",
        "decision_support_note": DECISION_SUPPORT_NOTE,
        "run_count": len(entries),
        "unique_run_names": len(duplicate_run_names) == 0,
        "duplicate_run_names": duplicate_run_names,
        "missing_metrics_runs": missing_metrics,
        "unassigned_run_names": unassigned_runs,
        "experiment_ladder": ladder_status,
        "entries": entries,
        "integrity_status": "pass" if not duplicate_run_names and not missing_metrics else "warn",
    }


def _write_run_registry_md(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# OASIS-2 Run Registry",
        "",
        payload["decision_support_note"],
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- integrity_status: {payload['integrity_status']}",
        f"- run_count: {payload['run_count']}",
        "",
        "## Experiment Ladder",
        "",
        "| Stage | Run | Status | Config |",
        "|---|---|---|---|",
    ]
    for stage in payload.get("experiment_ladder", []):
        lines.append(
            f"| {stage['stage']} | {stage['run_name']} | {stage['status']} | "
            f"{'present' if stage.get('config_exists') else 'missing/planned'} |"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_model_board_md(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# CerebraSense Model Board",
        "",
        payload["decision_support_note"],
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- recommendation: {payload['recommendation']}",
        f"- entry_count: {payload['entry_count']}",
        "",
        "## Ranked Models",
        "",
        "| Rank | Dataset | Run | AUROC | F1 | Sens | Spec | Review | Subject AUROC | Score |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, entry in enumerate(payload["entries"], start=1):
        lines.append(
            f"| {index} | {entry['dataset']} | {entry['run_name']} | "
            f"{entry['auroc']:.3f} | {entry['f1']:.3f} | {entry['sensitivity']:.3f} | "
            f"{entry['specificity']:.3f} | {entry['review_required_count']} | "
            f"{entry['subject_consensus_auroc']:.3f} | {entry['candidate_score']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Promotion Briefing",
            "",
            f"- active_baseline: {payload['promotion_briefing']['active_baseline']}",
            f"- best_oasis2_candidate: {payload['promotion_briefing']['best_oasis2_candidate']}",
            f"- rule: {payload['promotion_briefing']['rule']}",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _risk_volatility(scores: list[float]) -> float:
    if len(scores) < 2:
        return 0.0
    mean_score = sum(scores) / len(scores)
    variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
    return round(variance**0.5, 6)


def _risk_acceleration(deltas: list[float]) -> float:
    if len(deltas) < 2:
        return 0.0
    return round(deltas[-1] - deltas[0], 6)


def _trajectory_reviewer_reasons(
    *,
    max_risk: float,
    risk_delta: float,
    temporal_paradox_count: int,
    review_count: int,
    mixed_label_subject: bool,
    volatility: float,
) -> list[str]:
    reasons: list[str] = []
    if temporal_paradox_count > 0:
        reasons.append("temporal paradox")
    if mixed_label_subject:
        reasons.append("mixed longitudinal labels")
    if review_count > 0:
        reasons.append("low-confidence or review-flagged visits")
    if max_risk >= OASIS2_REVIEW_THRESHOLDS["high_risk_review_min"]:
        reasons.append("high maximum risk")
    if risk_delta >= 0.10:
        reasons.append("rising risk trajectory")
    if volatility >= 0.12:
        reasons.append("volatile visit-to-visit risk")
    return reasons or ["routine longitudinal tracking"]


def _trajectory_score(
    *,
    max_risk: float,
    risk_delta: float,
    acceleration: float,
    volatility: float,
    temporal_paradox_count: int,
    review_count: int,
    mixed_label_subject: bool,
) -> float:
    score = (
        (0.30 * max_risk)
        + (0.18 * max(risk_delta, 0.0))
        + (0.14 * max(acceleration, 0.0))
        + (0.14 * min(volatility, 1.0))
        + (0.12 * min(temporal_paradox_count, 3) / 3.0)
        + (0.07 * min(review_count, 3) / 3.0)
        + (0.05 if mixed_label_subject else 0.0)
    )
    return round(min(score, 1.0), 6)


def _trajectory_status(score: float, reasons: list[str]) -> str:
    if "temporal paradox" in reasons or score >= 0.70:
        return "review_required"
    if score >= OASIS2_REVIEW_THRESHOLDS["trajectory_score_review_min"] or "rising risk trajectory" in reasons:
        return "progression_watch"
    return "stable_watch"


def build_oasis2_progression_panel(
    *,
    predictions_csv_path: Path | None = None,
    settings: AppSettings | None = None,
    temporal_drop_epsilon: float = 0.15,
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Build a subject-level OASIS-2 progression panel from prediction rows."""

    resolved_settings = settings or get_app_settings()
    if predictions_csv_path is None:
        oasis2_root = resolved_settings.outputs_root / "runs" / "oasis2"
        candidates = list(oasis2_root.glob("*/evaluation/post_train_test_best_model*/predictions.csv"))
        if not candidates:
            return {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "artifact_type": "oasis2_progression_panel",
                "decision_support_note": DECISION_SUPPORT_NOTE,
                "subject_count": 0,
                "temporal_paradox_count": 0,
                "high_priority_subject_count": 0,
                "notes": ["No OASIS-2 prediction CSV was found."],
            }, pd.DataFrame()
        predictions_csv_path = sorted(candidates, key=lambda item: item.stat().st_mtime, reverse=True)[0]

    frame = pd.read_csv(predictions_csv_path)
    subject_col = "meta_subject_id" if "meta_subject_id" in frame.columns else "sample_id"
    session_col = "meta_session_id" if "meta_session_id" in frame.columns else "sample_id"
    visit_col = "meta_visit_number" if "meta_visit_number" in frame.columns else None
    score_col = "probability_class_1" if "probability_class_1" in frame.columns else "calibrated_probability_score"

    rows: list[dict[str, Any]] = []
    temporal_paradox_count = 0
    for subject_id, group in frame.groupby(subject_col, sort=True):
        work = group.copy()
        if visit_col:
            work["_visit_sort"] = pd.to_numeric(work[visit_col], errors="coerce").fillna(10**9)
            work = work.sort_values(["_visit_sort", session_col], kind="stable")
        scores = [float(value) for value in pd.to_numeric(work[score_col], errors="coerce").fillna(0.0).tolist()]
        labels = [int(value) for value in pd.to_numeric(work["true_label"], errors="coerce").dropna().tolist()]
        deltas = [round(scores[index] - scores[index - 1], 6) for index in range(1, len(scores))]
        risk_delta = round(scores[-1] - scores[0], 6) if len(scores) >= 2 else 0.0
        volatility = _risk_volatility(scores)
        acceleration = _risk_acceleration(deltas)
        subject_paradoxes = sum(1 for delta in deltas if delta <= -abs(temporal_drop_epsilon))
        temporal_paradox_count += subject_paradoxes
        review_count = int(work.get("review_flag", pd.Series(dtype=object)).astype(str).str.lower().isin({"true", "1", "yes"}).sum())
        mixed_label_subject = len(set(labels)) > 1
        max_risk = max(scores) if scores else 0.0
        reviewer_reasons = _trajectory_reviewer_reasons(
            max_risk=max_risk,
            risk_delta=risk_delta,
            temporal_paradox_count=subject_paradoxes,
            review_count=review_count,
            mixed_label_subject=mixed_label_subject,
            volatility=volatility,
        )
        trajectory_score = _trajectory_score(
            max_risk=max_risk,
            risk_delta=risk_delta,
            acceleration=acceleration,
            volatility=volatility,
            temporal_paradox_count=subject_paradoxes,
            review_count=review_count,
            mixed_label_subject=mixed_label_subject,
        )
        rows.append(
            {
                "subject_id": subject_id,
                "session_count": int(len(work)),
                "first_session": str(work[session_col].iloc[0]),
                "last_session": str(work[session_col].iloc[-1]),
                "first_risk": scores[0] if scores else None,
                "last_risk": scores[-1] if scores else None,
                "max_risk": max_risk,
                "risk_delta": risk_delta,
                "max_visit_delta": max(deltas, key=abs) if deltas else 0.0,
                "risk_acceleration": acceleration,
                "risk_volatility": volatility,
                "visit_deltas": deltas,
                "temporal_paradox_count": subject_paradoxes,
                "mixed_label_subject": mixed_label_subject,
                "review_required_count": review_count,
                "trajectory_score": trajectory_score,
                "trajectory_status": _trajectory_status(trajectory_score, reviewer_reasons),
                "reviewer_reasons": reviewer_reasons,
                "evidence_summary": (
                    f"{len(work)} visits; risk {scores[0]:.3f}->{scores[-1]:.3f}; "
                    f"delta {risk_delta:.3f}; max {max_risk:.3f}."
                    if scores
                    else "No valid risk scores."
                ),
                "high_priority": bool(subject_paradoxes > 0 or review_count > 0 or (scores and max_risk >= 0.7)),
            }
        )

    case_frame = pd.DataFrame(rows).sort_values(
        ["high_priority", "trajectory_score", "temporal_paradox_count", "max_risk"],
        ascending=[False, False, False, False],
        kind="stable",
    )
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "oasis2_progression_panel",
        "decision_support_note": DECISION_SUPPORT_NOTE,
        "predictions_csv_path": str(predictions_csv_path),
        "temporal_paradox_epsilon": float(abs(temporal_drop_epsilon)),
        "subject_count": int(len(case_frame)),
        "temporal_paradox_count": int(temporal_paradox_count),
        "mixed_label_subject_count": int(case_frame["mixed_label_subject"].sum()) if not case_frame.empty else 0,
        "high_priority_subject_count": int(case_frame["high_priority"].sum()) if not case_frame.empty else 0,
        "trajectory_review_subject_count": (
            int(case_frame["trajectory_status"].isin({"review_required", "progression_watch"}).sum()) if not case_frame.empty else 0
        ),
        "trajectory_score_review_min": OASIS2_REVIEW_THRESHOLDS["trajectory_score_review_min"],
        "top_subjects": case_frame.head(10).to_dict(orient="records"),
    }
    return payload, case_frame


def _write_progression_md(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# OASIS-2 Progression Panel",
        "",
        payload["decision_support_note"],
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- subject_count: {payload.get('subject_count', 0)}",
        f"- temporal_paradox_count: {payload.get('temporal_paradox_count', 0)}",
        f"- mixed_label_subject_count: {payload.get('mixed_label_subject_count', 0)}",
        f"- high_priority_subject_count: {payload.get('high_priority_subject_count', 0)}",
        f"- trajectory_review_subject_count: {payload.get('trajectory_review_subject_count', 0)}",
        "",
        "## Top Subjects",
        "",
        "| Subject | Sessions | First Risk | Last Risk | Delta | Score | Status | Reason |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in payload.get("top_subjects", []):
        lines.append(
            f"| {row['subject_id']} | {row['session_count']} | "
            f"{float(row.get('first_risk') or 0.0):.3f} | {float(row.get('last_risk') or 0.0):.3f} | "
            f"{float(row.get('risk_delta') or 0.0):.3f} | {float(row.get('trajectory_score') or 0.0):.3f} | "
            f"{row.get('trajectory_status', 'track')} | {', '.join(row.get('reviewer_reasons', []))} |"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def _build_promotion_blockers(best_oasis2: dict[str, Any], progression: dict[str, Any]) -> list[dict[str, Any]]:
    if not best_oasis2:
        return [
            {
                "metric": "oasis2_candidate",
                "actual": None,
                "target": "available evaluated candidate",
                "message": "No evaluated OASIS-2 candidate was found.",
            }
        ]
    checks = [
        ("test_auroc", best_oasis2.get("auroc"), OASIS2_PROMOTION_GATES["test_auroc"], ">="),
        (
            "balanced_accuracy",
            _balanced_accuracy_from_entry(best_oasis2),
            OASIS2_PROMOTION_GATES["balanced_accuracy"],
            ">=",
        ),
        ("specificity", best_oasis2.get("specificity"), OASIS2_PROMOTION_GATES["specificity"], ">="),
        (
            "subject_consensus_auroc",
            best_oasis2.get("subject_consensus_auroc"),
            OASIS2_PROMOTION_GATES["subject_consensus_auroc"],
            ">=",
        ),
        (
            "temporal_paradox_count",
            progression.get("temporal_paradox_count", 0),
            OASIS2_PROMOTION_GATES["temporal_paradox_count_max"],
            "<=",
        ),
    ]
    blockers: list[dict[str, Any]] = []
    for metric, actual, target, comparator in checks:
        actual_value = float(actual or 0.0)
        failed = actual_value < float(target) if comparator == ">=" else actual_value > float(target)
        if failed:
            blockers.append(
                {
                    "metric": metric,
                    "actual": round(actual_value, 6),
                    "target": target,
                    "comparator": comparator,
                    "message": f"{metric} {actual_value:.3f} does not meet {comparator} {float(target):.3f}.",
                }
            )
    return blockers


def _build_candidate_status(best_oasis2: dict[str, Any], blockers: list[dict[str, Any]]) -> dict[str, Any]:
    if not best_oasis2:
        return {
            "status": "missing_candidate",
            "label": "Candidate missing",
            "reason": "No evaluated OASIS-2 candidate is available.",
            "baseline_locked": dict(OASIS2_BASELINE_CANDIDATE),
            "v2_acceptance_targets": dict(OASIS2_V2_ACCEPTANCE_TARGETS),
        }
    if blockers:
        status = "candidate_only"
        label = "Candidate only"
        reason = "OASIS-2 remains a longitudinal research candidate until promotion gates pass."
    else:
        status = "promotion_review_ready"
        label = "Promotion review ready"
        reason = "OASIS-2 meets automated gates and still requires human review before any active baseline change."
    return {
        "status": status,
        "label": label,
        "reason": reason,
        "baseline_locked": dict(OASIS2_BASELINE_CANDIDATE),
        "v2_acceptance_targets": dict(OASIS2_V2_ACCEPTANCE_TARGETS),
    }


def build_reviewer_handoff_pack(
    *,
    predictions_csv_path: Path | None = None,
    progression: dict[str, Any] | None = None,
    case_frame: pd.DataFrame | None = None,
    settings: AppSettings | None = None,
    max_cases_per_bucket: int = 8,
) -> dict[str, Any]:
    """Build a compact reviewer handoff pack for uncertain and inconsistent OASIS-2 cases."""

    resolved_settings = settings or get_app_settings()
    resolved_progression = progression or {}
    if predictions_csv_path is None and resolved_progression.get("predictions_csv_path"):
        predictions_csv_path = Path(str(resolved_progression["predictions_csv_path"]))
    if predictions_csv_path is None:
        oasis2_root = resolved_settings.outputs_root / "runs" / "oasis2"
        candidates = list(oasis2_root.glob("*/evaluation/post_train_test_best_model*/predictions.csv"))
        predictions_csv_path = sorted(candidates, key=lambda item: item.stat().st_mtime, reverse=True)[0] if candidates else None

    frame = pd.read_csv(predictions_csv_path) if predictions_csv_path is not None and predictions_csv_path.exists() else pd.DataFrame()
    queue: list[dict[str, Any]] = []
    false_positives: list[dict[str, Any]] = []
    false_negatives: list[dict[str, Any]] = []
    low_confidence_cases: list[dict[str, Any]] = []
    mixed_label_subjects: list[dict[str, Any]] = []

    if not frame.empty:
        score_col = "probability_class_1" if "probability_class_1" in frame.columns else "calibrated_probability_score"
        if {"true_label", "predicted_label"}.issubset(frame.columns):
            false_positive_frame = frame[(frame["true_label"].astype(int) == 0) & (frame["predicted_label"].astype(int) == 1)]
            if score_col in false_positive_frame.columns:
                false_positive_frame = false_positive_frame.sort_values(score_col, ascending=False, kind="stable")
            false_positives = [
                _prediction_case(row, case_type="false_positive", priority="high", reason="Non-demented label predicted as demented.")
                for _, row in false_positive_frame.head(max_cases_per_bucket).iterrows()
            ]
            false_negative_frame = frame[(frame["true_label"].astype(int) == 1) & (frame["predicted_label"].astype(int) == 0)]
            if score_col in false_negative_frame.columns:
                false_negative_frame = false_negative_frame.sort_values(score_col, ascending=True, kind="stable")
            false_negatives = [
                _prediction_case(row, case_type="false_negative", priority="critical", reason="Demented label predicted as non-demented.")
                for _, row in false_negative_frame.head(max_cases_per_bucket).iterrows()
            ]

        low_mask = pd.Series(False, index=frame.index)
        if "confidence_level" in frame.columns:
            low_mask = low_mask | frame["confidence_level"].astype(str).str.lower().eq("low")
        if "review_flag" in frame.columns:
            low_mask = low_mask | frame["review_flag"].astype(str).str.lower().isin({"true", "1", "yes"})
        low_frame = frame[low_mask].copy()
        sort_col = "normalized_entropy" if "normalized_entropy" in low_frame.columns else "uncertainty_score"
        if sort_col in low_frame.columns:
            low_frame = low_frame.sort_values(sort_col, ascending=False, kind="stable")
        low_confidence_cases = [
            _prediction_case(row, case_type="low_confidence", priority="medium", reason="Low confidence or explicit review flag.")
            for _, row in low_frame.head(max_cases_per_bucket).iterrows()
        ]

        if "true_label" in frame.columns:
            subject_col = "meta_subject_id" if "meta_subject_id" in frame.columns else "sample_id"
            session_col = "meta_session_id" if "meta_session_id" in frame.columns else "sample_id"
            for subject_id, group in frame.groupby(subject_col, sort=True):
                labels = sorted({int(label) for label in pd.to_numeric(group["true_label"], errors="coerce").dropna().tolist()})
                if len(labels) <= 1:
                    continue
                risks = pd.to_numeric(group.get(score_col, pd.Series(dtype=float)), errors="coerce").fillna(0.0)
                mixed_label_subjects.append(
                    {
                        "case_type": "mixed_label_subject",
                        "priority": "high",
                        "subject_id": str(subject_id),
                        "session_id": str(group[session_col].iloc[-1]),
                        "session_count": int(len(group)),
                        "label_sequence": labels,
                        "max_risk": round(float(risks.max()), 6),
                        "reason": "Subject has mixed longitudinal labels and needs subject-level consensus review.",
                    }
                )
        mixed_label_subjects = sorted(mixed_label_subjects, key=lambda item: item["max_risk"], reverse=True)[:max_cases_per_bucket]

    temporal_subjects = []
    if case_frame is not None and not case_frame.empty:
        paradox_frame = case_frame[case_frame["temporal_paradox_count"].fillna(0).astype(int) > 0]
        for _, row in paradox_frame.head(max_cases_per_bucket).iterrows():
            temporal_subjects.append(
                {
                    "case_type": "temporal_paradox_subject",
                    "priority": "critical",
                    "subject_id": str(row["subject_id"]),
                    "session_id": str(row.get("last_session", "")),
                    "risk_score": round(float(row.get("last_risk") or 0.0), 6),
                    "temporal_paradox_count": int(row.get("temporal_paradox_count") or 0),
                    "risk_delta": round(float(row.get("risk_delta") or 0.0), 6),
                    "reason": "Longitudinal risk dropped beyond the paradox threshold.",
                }
            )
    elif resolved_progression.get("top_subjects"):
        for row in resolved_progression.get("top_subjects", []):
            if int(row.get("temporal_paradox_count") or 0) > 0:
                temporal_subjects.append(
                    {
                        "case_type": "temporal_paradox_subject",
                        "priority": "critical",
                        "subject_id": str(row.get("subject_id", "")),
                        "session_id": str(row.get("last_session", "")),
                        "risk_score": round(float(row.get("last_risk") or 0.0), 6),
                        "temporal_paradox_count": int(row.get("temporal_paradox_count") or 0),
                        "risk_delta": round(float(row.get("risk_delta") or 0.0), 6),
                        "reason": "Longitudinal risk dropped beyond the paradox threshold.",
                    }
                )
        temporal_subjects = temporal_subjects[:max_cases_per_bucket]

    queue = (temporal_subjects + false_negatives + false_positives + low_confidence_cases + mixed_label_subjects)[:20]
    category_counts = {
        "temporal_paradox_subjects": len(temporal_subjects),
        "false_positives": len(false_positives),
        "false_negatives": len(false_negatives),
        "low_confidence_cases": len(low_confidence_cases),
        "mixed_label_subjects": len(mixed_label_subjects),
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "oasis2_reviewer_handoff_pack",
        "decision_support_note": DECISION_SUPPORT_NOTE,
        "candidate_run_name": _run_name_from_predictions_path(predictions_csv_path),
        "source_predictions_csv": None if predictions_csv_path is None else str(predictions_csv_path),
        "category_counts": category_counts,
        "categories": {
            "temporal_paradox_subjects": temporal_subjects,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "low_confidence_cases": low_confidence_cases,
            "mixed_label_subjects": mixed_label_subjects,
        },
        "error_learning_loop": {
            "taxonomy": list(category_counts.keys()),
            "counts": category_counts,
            "review_thresholds": dict(OASIS2_REVIEW_THRESHOLDS),
            "next_actions": [
                "Review false negatives first because missed positive labels carry the highest research risk.",
                "Audit temporal paradox subjects before any threshold or promotion decision.",
                "Use low-confidence cases to tune review thresholds without relabeling source data silently.",
                "Track mixed-label subjects separately from session-level errors.",
            ],
            "decision_policy": "Use reviewer outcomes to update thresholds and candidate notes only; do not overwrite source labels.",
        },
        "review_queue": {
            "total_case_count": len(queue),
            "cases": queue,
        },
    }


def _write_handoff_pack_md(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# OASIS-2 Reviewer Handoff Pack",
        "",
        payload["decision_support_note"],
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- candidate_run_name: {payload.get('candidate_run_name')}",
        "",
        "## Category Counts",
        "",
    ]
    for key, value in payload.get("category_counts", {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Priority Queue",
            "",
            "| Priority | Type | Subject | Session | Risk | Reason |",
            "|---|---|---|---|---:|---|",
        ]
    )
    for case in payload.get("review_queue", {}).get("cases", []):
        lines.append(
            f"| {case.get('priority')} | {case.get('case_type')} | {case.get('subject_id')} | "
            f"{case.get('session_id', '')} | {float(case.get('risk_score') or case.get('max_risk') or 0.0):.3f} | "
            f"{case.get('reason')} |"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def build_model_cards(
    model_board: dict[str, Any],
    progression: dict[str, Any],
    handoff_pack: dict[str, Any],
) -> dict[str, Any]:
    """Create concise model cards for the active OASIS-1 anchor and OASIS-2 candidate."""

    entries = model_board.get("entries", [])
    active = next((entry for entry in entries if entry.get("model_id") == "oasis1_active"), {})
    candidate = next((entry for entry in entries if entry.get("dataset") == "oasis2"), {})
    blockers = _build_promotion_blockers(candidate, progression)
    cards: list[dict[str, Any]] = []
    if active:
        cards.append(
            {
                "model_id": active.get("model_id"),
                "run_name": active.get("run_name"),
                "dataset": "oasis1",
                "status": "active_anchor",
                "intended_use": "Stable OASIS-first structural MRI research decision-support baseline.",
                "not_intended_for": "Autonomous diagnosis, medical-use rollout, or non-OASIS disease claims.",
                "evidence": {
                    "auroc": active.get("auroc"),
                    "f1": active.get("f1"),
                    "specificity": active.get("specificity"),
                    "review_required_count": active.get("review_required_count"),
                },
                "decision_support_note": DECISION_SUPPORT_NOTE,
            }
        )
    if candidate:
        cards.append(
            {
                "model_id": candidate.get("model_id"),
                "run_name": candidate.get("run_name"),
                "dataset": "oasis2",
                "status": "longitudinal_candidate",
                "intended_use": "Longitudinal OASIS-2 research candidate for progression review and subject-level evidence.",
                "not_intended_for": "Drop-in OASIS-1 replacement, diagnosis, or medical-use rollout claims.",
                "evidence": {
                    "auroc": candidate.get("auroc"),
                    "balanced_accuracy": _balanced_accuracy_from_entry(candidate),
                    "specificity": candidate.get("specificity"),
                    "subject_consensus_auroc": candidate.get("subject_consensus_auroc"),
                    "review_required_count": candidate.get("review_required_count"),
                    "temporal_paradox_count": progression.get("temporal_paradox_count", 0),
                    "handoff_case_count": handoff_pack.get("review_queue", {}).get("total_case_count", 0),
                },
                "promotion_gates": dict(OASIS2_PROMOTION_GATES),
                "promotion_blockers": blockers,
                "decision_support_note": DECISION_SUPPORT_NOTE,
            }
        )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "cerebrasense_model_cards",
        "decision_support_note": DECISION_SUPPORT_NOTE,
        "card_count": len(cards),
        "cards": cards,
    }


def _write_model_cards_md(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# CerebraSense Model Cards",
        "",
        payload["decision_support_note"],
        "",
    ]
    for card in payload.get("cards", []):
        evidence = card.get("evidence", {})
        lines.extend(
            [
                f"## {card.get('run_name')}",
                "",
                f"- dataset: {card.get('dataset')}",
                f"- status: {card.get('status')}",
                f"- intended_use: {card.get('intended_use')}",
                f"- not_intended_for: {card.get('not_intended_for')}",
                f"- AUROC: {float(evidence.get('auroc') or 0.0):.3f}",
                f"- specificity: {float(evidence.get('specificity') or 0.0):.3f}",
                f"- review_required_count: {evidence.get('review_required_count')}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def build_deployment_readiness(
    model_board: dict[str, Any],
    progression: dict[str, Any],
    *,
    settings: AppSettings | None = None,
) -> dict[str, Any]:
    """Summarize ONNX/export readiness without promoting a candidate prematurely."""

    resolved_settings = settings or get_app_settings()
    entries = model_board.get("entries", [])
    candidate = next((entry for entry in entries if entry.get("dataset") == "oasis2"), {})
    blockers = _build_promotion_blockers(candidate, progression)
    run_name = candidate.get("run_name")
    run_root = resolved_settings.outputs_root / "runs" / "oasis2" / str(run_name) if run_name else None
    checkpoint_path = run_root / "checkpoints" / "best_model.pt" if run_root else None
    onnx_path = run_root / "exports" / "best_model.onnx" if run_root else None
    model_size_mb = (
        round(checkpoint_path.stat().st_size / (1024 * 1024), 3)
        if checkpoint_path is not None and checkpoint_path.exists()
        else None
    )
    onnx_export_allowed = bool(candidate) and not blockers
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "cerebrasense_deployment_readiness",
        "decision_support_note": DECISION_SUPPORT_NOTE,
        "candidate_run_name": run_name,
        "readiness_status": "export_ready_after_review" if onnx_export_allowed else "blocked_candidate",
        "onnx_export_allowed": onnx_export_allowed,
        "onnx_export_rule": "Export OASIS-2 to ONNX only after automated promotion gates pass and human review confirms candidate status.",
        "promotion_blockers": blockers,
        "checkpoint_path": None if checkpoint_path is None else _portable_path(checkpoint_path, resolved_settings.workspace_root),
        "checkpoint_exists": bool(checkpoint_path is not None and checkpoint_path.exists()),
        "onnx_path": None if onnx_path is None else _portable_path(onnx_path, resolved_settings.workspace_root),
        "onnx_exists": bool(onnx_path is not None and onnx_path.exists()),
        "model_size_mb": model_size_mb,
        "benchmark_targets": dict(DEPLOYMENT_BENCHMARK_TARGETS),
        "benchmark_status": "pending_export" if not onnx_export_allowed else "run_latency_benchmark_before_demo_claims",
    }


def _write_deployment_readiness_md(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# CerebraSense Deployment Readiness",
        "",
        payload["decision_support_note"],
        "",
        f"- candidate_run_name: {payload.get('candidate_run_name')}",
        f"- readiness_status: {payload.get('readiness_status')}",
        f"- onnx_export_allowed: {payload.get('onnx_export_allowed')}",
        f"- checkpoint_exists: {payload.get('checkpoint_exists')}",
        f"- onnx_exists: {payload.get('onnx_exists')}",
        f"- benchmark_status: {payload.get('benchmark_status')}",
        "",
        "## Export Rule",
        "",
        payload["onnx_export_rule"],
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def build_demo_bundle_manifest(
    model_board: dict[str, Any],
    handoff_pack: dict[str, Any],
    *,
    settings: AppSettings | None = None,
) -> dict[str, Any]:
    """Describe one-click demo bundle actions without changing runtime state."""

    resolved_settings = settings or get_app_settings()
    entries = model_board.get("entries", [])
    active = next((entry for entry in entries if entry.get("model_id") == "oasis1_active"), {})
    candidate = next((entry for entry in entries if entry.get("dataset") == "oasis2"), {})
    candidate_run_name = candidate.get("run_name") or "oasis2_multimodal_v1"
    actions = [
        {
            "id": "stable_oasis1_demo",
            "label": "Stable OASIS-1 Demo",
            "status": "ready" if active else "missing_active_model",
            "command": "python scripts/build_oasis_demo_bundle.py --bundle-name oasis1_stable_demo",
            "output_path": _portable_path(resolved_settings.outputs_root / "reports" / "demo" / "oasis1_stable_demo", resolved_settings.workspace_root),
        },
        {
            "id": "oasis2_candidate_demo",
            "label": "OASIS-2 Candidate Demo",
            "status": "ready" if candidate else "missing_candidate",
            "command": f"python scripts/build_oasis2_demo_bundle.py --run-name {candidate_run_name} --bundle-name oasis2_candidate_demo",
            "output_path": _portable_path(resolved_settings.outputs_root / "reports" / "demo" / "oasis2_candidate_demo", resolved_settings.workspace_root),
        },
        {
            "id": "review_hard_cases",
            "label": "Review Hard Cases",
            "status": "ready" if handoff_pack.get("review_queue", {}).get("total_case_count", 0) else "no_cases",
            "command": "python scripts/build_next_level_artifacts.py",
            "output_path": _portable_path(resolved_settings.outputs_root / "reports" / "next_level" / "current" / "review_handoff_pack.md", resolved_settings.workspace_root),
        },
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "cerebrasense_demo_bundle_manifest",
        "decision_support_note": DECISION_SUPPORT_NOTE,
        "actions": actions,
    }


def _write_demo_bundle_manifest_md(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# CerebraSense Demo Bundle Actions",
        "",
        payload["decision_support_note"],
        "",
        "| Action | Status | Command |",
        "|---|---|---|",
    ]
    for action in payload.get("actions", []):
        lines.append(f"| {action['label']} | {action['status']} | `{action['command']}` |")
    path.write_text("\n".join(lines), encoding="utf-8")


def build_frontend_research_payload(
    model_board: dict[str, Any],
    progression: dict[str, Any],
    handoff_pack: dict[str, Any] | None = None,
    handoff_pack_paths: dict[str, str] | None = None,
    model_cards: dict[str, Any] | None = None,
    deployment_readiness: dict[str, Any] | None = None,
    demo_bundle_manifest: dict[str, Any] | None = None,
    run_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create the compact JSON contract consumed by the frontend demo."""

    active_oasis1 = next((entry for entry in model_board.get("entries", []) if entry.get("model_id") == "oasis1_active"), {})
    best = active_oasis1 or (model_board.get("entries", [{}])[0] if model_board.get("entries") else {})
    best_oasis2 = next((entry for entry in model_board.get("entries", []) if entry.get("dataset") == "oasis2"), {})
    blockers = _build_promotion_blockers(best_oasis2, progression)
    candidate_status = _build_candidate_status(best_oasis2, blockers)
    handoff = handoff_pack or {}
    cards = model_cards or {}
    readiness = deployment_readiness or {}
    demo_manifest = demo_bundle_manifest or {}
    registry = run_registry or {}
    paradox_summary = {
        "temporal_paradox_count": progression.get("temporal_paradox_count", 0),
        "temporal_paradox_epsilon": progression.get("temporal_paradox_epsilon"),
        "high_priority_subject_count": progression.get("high_priority_subject_count", 0),
        "top_subjects": [
            subject
            for subject in progression.get("top_subjects", [])
            if int(subject.get("temporal_paradox_count") or 0) > 0
        ][:5],
    }
    top_model_summaries = [
        {
            "dataset": entry.get("dataset"),
            "run_name": entry.get("run_name"),
            "role": entry.get("role"),
            "auroc": entry.get("auroc"),
            "balanced_accuracy": _balanced_accuracy_from_entry(entry),
            "specificity": entry.get("specificity"),
            "review_required_count": entry.get("review_required_count"),
            "subject_consensus_auroc": entry.get("subject_consensus_auroc"),
        }
        for entry in model_board.get("entries", [])[:5]
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "research",
        "decision_support_note": DECISION_SUPPORT_NOTE,
        "headline": "OASIS-2 longitudinal candidate board",
        "active_model": {
            "run_name": best.get("run_name"),
            "dataset": best.get("dataset"),
            "auroc": best.get("auroc"),
            "f1": best.get("f1"),
            "specificity": best.get("specificity"),
            "balanced_accuracy": _balanced_accuracy_from_entry(best) if best else None,
            "review_required_count": best.get("review_required_count"),
        },
        "oasis2_candidate": {
            "run_name": best_oasis2.get("run_name"),
            "auroc": best_oasis2.get("auroc"),
            "f1": best_oasis2.get("f1"),
            "sensitivity": best_oasis2.get("sensitivity"),
            "specificity": best_oasis2.get("specificity"),
            "balanced_accuracy": _balanced_accuracy_from_entry(best_oasis2) if best_oasis2 else None,
            "review_required_count": best_oasis2.get("review_required_count"),
            "subject_consensus_auroc": best_oasis2.get("subject_consensus_auroc"),
            "recommendation": model_board.get("recommendation"),
        },
        "active_vs_candidate": {
            "active_run_name": best.get("run_name"),
            "candidate_run_name": best_oasis2.get("run_name"),
            "auroc_delta": (
                round(float(best_oasis2.get("auroc") or 0.0) - float(best.get("auroc") or 0.0), 6)
                if best and best_oasis2
                else None
            ),
            "specificity_delta": (
                round(float(best_oasis2.get("specificity") or 0.0) - float(best.get("specificity") or 0.0), 6)
                if best and best_oasis2
                else None
            ),
            "decision": "keep_oasis1_active_until_oasis2_gates_pass",
        },
        "model_board_summary": {
            "entry_count": model_board.get("entry_count", 0),
            "recommendation": model_board.get("recommendation"),
            "top_models": top_model_summaries,
        },
        "candidate_status": candidate_status,
        "promotion_blockers": blockers,
        "experiment_ladder": registry.get("experiment_ladder", model_board.get("experiment_ladder", [])),
        "run_registry": {
            "integrity_status": registry.get("integrity_status"),
            "run_count": registry.get("run_count", 0),
            "unique_run_names": registry.get("unique_run_names", True),
        },
        "progression": {
            "subject_count": progression.get("subject_count", 0),
            "temporal_paradox_count": progression.get("temporal_paradox_count", 0),
            "high_priority_subject_count": progression.get("high_priority_subject_count", 0),
            "trajectory_review_subject_count": progression.get("trajectory_review_subject_count", 0),
            "trajectory_score_review_min": progression.get("trajectory_score_review_min"),
            "top_subjects": progression.get("top_subjects", [])[:5],
        },
        "trajectory_intelligence": {
            "review_subject_count": progression.get("trajectory_review_subject_count", 0),
            "score_review_min": progression.get("trajectory_score_review_min"),
            "top_subjects": progression.get("top_subjects", [])[:5],
        },
        "paradox_summary": paradox_summary,
        "error_learning_loop": handoff.get("error_learning_loop", {}),
        "review_queue": handoff.get("review_queue", {"total_case_count": 0, "cases": []}),
        "model_cards": cards.get("cards", []),
        "deployment_readiness": readiness,
        "demo_bundle_actions": demo_manifest,
        "handoff_pack_paths": handoff_pack_paths or {},
    }


def build_next_level_artifacts(
    *,
    settings: AppSettings | None = None,
    output_root: Path | None = None,
    frontend_payload_path: Path | None = None,
) -> NextLevelArtifacts:
    """Build model board, progression panel, and frontend bridge payload."""

    resolved_settings = settings or get_app_settings()
    resolved_output_root = ensure_directory(
        output_root or resolved_settings.outputs_root / "reports" / "next_level" / "current"
    )
    model_board = build_model_board(settings=resolved_settings)
    run_registry = build_oasis2_run_registry(model_board, settings=resolved_settings)
    progression, case_frame = build_oasis2_progression_panel(settings=resolved_settings)

    board_json = resolved_output_root / "model_board.json"
    board_md = resolved_output_root / "model_board.md"
    run_registry_json = resolved_output_root / "oasis2_run_registry.json"
    run_registry_md = resolved_output_root / "oasis2_run_registry.md"
    progression_json = resolved_output_root / "oasis2_progression_panel.json"
    progression_md = resolved_output_root / "oasis2_progression_panel.md"
    progression_csv = resolved_output_root / "oasis2_progression_cases.csv"
    handoff_json = resolved_output_root / "review_handoff_pack.json"
    handoff_md = resolved_output_root / "review_handoff_pack.md"
    model_cards_json = resolved_output_root / "model_cards.json"
    model_cards_md = resolved_output_root / "model_cards.md"
    deployment_readiness_json = resolved_output_root / "deployment_readiness.json"
    deployment_readiness_md = resolved_output_root / "deployment_readiness.md"
    demo_bundle_manifest_json = resolved_output_root / "demo_bundle_manifest.json"
    demo_bundle_manifest_md = resolved_output_root / "demo_bundle_manifest.md"
    demo_json = frontend_payload_path or resolved_output_root / "research_mode_payload.json"
    handoff_payload = build_reviewer_handoff_pack(
        predictions_csv_path=Path(str(progression["predictions_csv_path"])) if progression.get("predictions_csv_path") else None,
        progression=progression,
        case_frame=case_frame,
        settings=resolved_settings,
    )
    model_cards = build_model_cards(model_board, progression, handoff_payload)
    deployment_readiness = build_deployment_readiness(model_board, progression, settings=resolved_settings)
    demo_bundle_manifest = build_demo_bundle_manifest(model_board, handoff_payload, settings=resolved_settings)
    demo_payload = build_frontend_research_payload(
        model_board,
        progression,
        handoff_pack=handoff_payload,
        handoff_pack_paths={
            "json": _portable_path(handoff_json, resolved_settings.workspace_root),
            "markdown": _portable_path(handoff_md, resolved_settings.workspace_root),
        },
        model_cards=model_cards,
        deployment_readiness=deployment_readiness,
        demo_bundle_manifest=demo_bundle_manifest,
        run_registry=run_registry,
    )

    board_json.write_text(json.dumps(model_board, indent=2), encoding="utf-8")
    _write_model_board_md(model_board, board_md)
    run_registry_json.write_text(json.dumps(run_registry, indent=2), encoding="utf-8")
    _write_run_registry_md(run_registry, run_registry_md)
    progression_json.write_text(json.dumps(progression, indent=2), encoding="utf-8")
    _write_progression_md(progression, progression_md)
    case_frame.to_csv(progression_csv, index=False)
    handoff_json.write_text(json.dumps(handoff_payload, indent=2), encoding="utf-8")
    _write_handoff_pack_md(handoff_payload, handoff_md)
    model_cards_json.write_text(json.dumps(model_cards, indent=2), encoding="utf-8")
    _write_model_cards_md(model_cards, model_cards_md)
    deployment_readiness_json.write_text(json.dumps(deployment_readiness, indent=2), encoding="utf-8")
    _write_deployment_readiness_md(deployment_readiness, deployment_readiness_md)
    demo_bundle_manifest_json.write_text(json.dumps(demo_bundle_manifest, indent=2), encoding="utf-8")
    _write_demo_bundle_manifest_md(demo_bundle_manifest, demo_bundle_manifest_md)
    ensure_directory(demo_json.parent)
    demo_json.write_text(json.dumps(demo_payload, indent=2), encoding="utf-8")

    return NextLevelArtifacts(
        output_root=resolved_output_root,
        model_board_json_path=board_json,
        model_board_md_path=board_md,
        run_registry_json_path=run_registry_json,
        run_registry_md_path=run_registry_md,
        progression_json_path=progression_json,
        progression_md_path=progression_md,
        progression_cases_csv_path=progression_csv,
        handoff_pack_json_path=handoff_json,
        handoff_pack_md_path=handoff_md,
        model_cards_json_path=model_cards_json,
        model_cards_md_path=model_cards_md,
        deployment_readiness_json_path=deployment_readiness_json,
        deployment_readiness_md_path=deployment_readiness_md,
        demo_bundle_manifest_json_path=demo_bundle_manifest_json,
        demo_bundle_manifest_md_path=demo_bundle_manifest_md,
        demo_payload_json_path=demo_json,
    )
