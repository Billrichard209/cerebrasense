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
    demo_payload_json_path: Path


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _metric(metrics: dict[str, Any] | None, key: str, default: float = 0.0) -> float:
    if not isinstance(metrics, dict):
        return default
    try:
        return float(metrics.get(key, default) or default)
    except (TypeError, ValueError):
        return default


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
    return {
        "model_id": model_id,
        "dataset": dataset,
        "run_name": run_name,
        "role": role,
        "metrics_path": None if metrics_path is None else str(metrics_path),
        "threshold": threshold if threshold is not None else metrics.get("threshold"),
        "auroc": _metric(metrics, "auroc"),
        "accuracy": _metric(metrics, "accuracy"),
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
        "entry_count": len(ranked),
        "entries": ranked,
        "promotion_briefing": {
            "active_baseline": None if active_oasis1 is None else active_oasis1["run_name"],
            "best_oasis2_candidate": None if best_oasis2 is None else best_oasis2["run_name"],
            "rule": "OASIS-2 is tracked as a longitudinal candidate first; OASIS-1 remains fallback until held-out evidence and review burden clearly improve.",
        },
    }


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


def build_oasis2_progression_panel(
    *,
    predictions_csv_path: Path | None = None,
    settings: AppSettings | None = None,
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
        subject_paradoxes = sum(1 for delta in deltas if delta < -0.05)
        temporal_paradox_count += subject_paradoxes
        review_count = int(work.get("review_flag", pd.Series(dtype=object)).astype(str).str.lower().isin({"true", "1", "yes"}).sum())
        rows.append(
            {
                "subject_id": subject_id,
                "session_count": int(len(work)),
                "first_session": str(work[session_col].iloc[0]),
                "last_session": str(work[session_col].iloc[-1]),
                "first_risk": scores[0] if scores else None,
                "last_risk": scores[-1] if scores else None,
                "max_risk": max(scores) if scores else None,
                "risk_delta": round(scores[-1] - scores[0], 6) if len(scores) >= 2 else 0.0,
                "temporal_paradox_count": subject_paradoxes,
                "mixed_label_subject": len(set(labels)) > 1,
                "review_required_count": review_count,
                "high_priority": bool(subject_paradoxes > 0 or review_count > 0 or (scores and max(scores) >= 0.7)),
            }
        )

    case_frame = pd.DataFrame(rows).sort_values(
        ["high_priority", "temporal_paradox_count", "max_risk"],
        ascending=[False, False, False],
        kind="stable",
    )
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "oasis2_progression_panel",
        "decision_support_note": DECISION_SUPPORT_NOTE,
        "predictions_csv_path": str(predictions_csv_path),
        "subject_count": int(len(case_frame)),
        "temporal_paradox_count": int(temporal_paradox_count),
        "mixed_label_subject_count": int(case_frame["mixed_label_subject"].sum()) if not case_frame.empty else 0,
        "high_priority_subject_count": int(case_frame["high_priority"].sum()) if not case_frame.empty else 0,
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
        "",
        "## Top Subjects",
        "",
        "| Subject | Sessions | First Risk | Last Risk | Delta | Paradoxes | Review |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload.get("top_subjects", []):
        lines.append(
            f"| {row['subject_id']} | {row['session_count']} | "
            f"{float(row.get('first_risk') or 0.0):.3f} | {float(row.get('last_risk') or 0.0):.3f} | "
            f"{float(row.get('risk_delta') or 0.0):.3f} | {row['temporal_paradox_count']} | "
            f"{row['review_required_count']} |"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def build_frontend_research_payload(model_board: dict[str, Any], progression: dict[str, Any]) -> dict[str, Any]:
    """Create the compact JSON contract consumed by the frontend demo."""

    best = model_board.get("entries", [{}])[0] if model_board.get("entries") else {}
    best_oasis2 = next((entry for entry in model_board.get("entries", []) if entry.get("dataset") == "oasis2"), {})
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
            "review_required_count": best.get("review_required_count"),
        },
        "oasis2_candidate": {
            "run_name": best_oasis2.get("run_name"),
            "auroc": best_oasis2.get("auroc"),
            "subject_consensus_auroc": best_oasis2.get("subject_consensus_auroc"),
            "recommendation": model_board.get("recommendation"),
        },
        "progression": {
            "subject_count": progression.get("subject_count", 0),
            "temporal_paradox_count": progression.get("temporal_paradox_count", 0),
            "high_priority_subject_count": progression.get("high_priority_subject_count", 0),
            "top_subjects": progression.get("top_subjects", [])[:5],
        },
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
    progression, case_frame = build_oasis2_progression_panel(settings=resolved_settings)
    demo_payload = build_frontend_research_payload(model_board, progression)

    board_json = resolved_output_root / "model_board.json"
    board_md = resolved_output_root / "model_board.md"
    progression_json = resolved_output_root / "oasis2_progression_panel.json"
    progression_md = resolved_output_root / "oasis2_progression_panel.md"
    progression_csv = resolved_output_root / "oasis2_progression_cases.csv"
    demo_json = frontend_payload_path or resolved_output_root / "research_mode_payload.json"

    board_json.write_text(json.dumps(model_board, indent=2), encoding="utf-8")
    _write_model_board_md(model_board, board_md)
    progression_json.write_text(json.dumps(progression, indent=2), encoding="utf-8")
    _write_progression_md(progression, progression_md)
    case_frame.to_csv(progression_csv, index=False)
    ensure_directory(demo_json.parent)
    demo_json.write_text(json.dumps(demo_payload, indent=2), encoding="utf-8")

    return NextLevelArtifacts(
        output_root=resolved_output_root,
        model_board_json_path=board_json,
        model_board_md_path=board_md,
        progression_json_path=progression_json,
        progression_md_path=progression_md,
        progression_cases_csv_path=progression_csv,
        demo_payload_json_path=demo_json,
    )
