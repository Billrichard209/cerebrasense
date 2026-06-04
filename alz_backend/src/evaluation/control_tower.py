"""CerebraSense Control Tower artifacts for evidence-command demos."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.configs.runtime import AppSettings, get_app_settings
from src.evaluation.next_level import (
    DECISION_SUPPORT_NOTE,
    OASIS2_PROMOTION_GATES,
    OASIS2_V2_ACCEPTANCE_TARGETS,
    build_next_level_artifacts,
)
from src.utils.io_utils import ensure_directory


@dataclass(slots=True)
class ControlTowerArtifacts:
    """Paths written by the Control Tower evidence bundle."""

    output_root: Path
    control_tower_json_path: Path
    control_tower_md_path: Path
    research_evidence_packet_md_path: Path
    research_payload_json_path: Path
    frontend_payload_json_path: Path | None
    frontend_payload_write_status: str
    next_level_output_root: Path


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _portable_path(path: Path, root: Path) -> str:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError:
        return str(resolved_path)


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _candidate_run_name(payload: dict[str, Any]) -> str | None:
    candidate = payload.get("oasis2_candidate", {})
    run_name = candidate.get("run_name")
    return str(run_name) if run_name else None


def _active_vs_candidate_deltas(payload: dict[str, Any]) -> dict[str, Any]:
    active = payload.get("active_model", {})
    candidate = payload.get("oasis2_candidate", {})
    return {
        "active_run_name": active.get("run_name"),
        "candidate_run_name": candidate.get("run_name"),
        "auroc_delta": round(_safe_float(candidate.get("auroc")) - _safe_float(active.get("auroc")), 6),
        "specificity_delta": round(_safe_float(candidate.get("specificity")) - _safe_float(active.get("specificity")), 6),
        "review_required_delta": int(_safe_float(candidate.get("review_required_count")) - _safe_float(active.get("review_required_count"))),
        "subject_consensus_auroc_delta": round(_safe_float(candidate.get("subject_consensus_auroc")), 6),
        "decision": "keep_oasis1_active_until_oasis2_gates_pass",
    }


def build_next_best_action(payload: dict[str, Any]) -> dict[str, Any]:
    """Select the next operational action from evidence and promotion blockers."""

    candidate = payload.get("oasis2_candidate", {})
    run_name = _candidate_run_name(payload)
    blockers = payload.get("promotion_blockers", [])
    progression = payload.get("progression", {})
    review_queue = payload.get("review_queue", {})
    deployment = payload.get("deployment_readiness", {})
    failed_ablations = payload.get("failed_ablations", [])
    next_candidate_run_name = payload.get("next_candidate_run_name")

    if not run_name:
        return {
            "id": "evaluate_or_import_oasis2_candidate",
            "label": "Evaluate OASIS-2",
            "priority": "critical",
            "reason": "No evaluated OASIS-2 candidate is available.",
            "command": "python scripts/evaluate_oasis2_candidate.py --run-name <run_name> --device auto --selection-metric balanced_accuracy",
        }

    if not blockers and deployment.get("onnx_export_allowed"):
        return {
            "id": "prepare_onnx_export_review",
            "label": "Prepare ONNX Review",
            "priority": "high",
            "reason": "Automated gates pass; export can be prepared for human review without auto-promotion.",
            "command": f"python scripts/post_train_pipeline.py --run-name {run_name} --device auto",
        }

    if int(progression.get("temporal_paradox_count") or 0) > OASIS2_PROMOTION_GATES["temporal_paradox_count_max"]:
        return {
            "id": "run_v3_temporal_consistency",
            "label": "Run V3 Temporal",
            "priority": "critical",
            "reason": "Temporal paradoxes remain above the zero-paradox promotion gate.",
            "command": "python scripts/train_oasis2.py --config configs/oasis2_train_multimodal_v3_temporal.yaml",
        }

    if any(item.get("run_name") == "oasis2_multimodal_v3_temporal" for item in failed_ablations):
        return {
            "id": "run_v3b_temporal_light",
            "label": "Run V3b Light",
            "priority": "critical",
            "reason": "V3 reached temporal consistency but failed discrimination; run the lighter temporal recovery recipe.",
            "command": "python scripts/train_oasis2.py --config configs/oasis2_train_multimodal_v3b_temporal_light.yaml",
            "run_name": next_candidate_run_name or "oasis2_multimodal_v3b_temporal_light",
        }

    review_count = int(_safe_float(candidate.get("review_required_count")))
    handoff_count = int(_safe_float(review_queue.get("total_case_count")))
    if review_count > int(OASIS2_V2_ACCEPTANCE_TARGETS["review_required_count_max"]) or handoff_count >= 20:
        return {
            "id": "review_hard_cases",
            "label": "Review Hard Cases",
            "priority": "high",
            "reason": "Review burden is still above the OASIS-2 v2 acceptance target.",
            "command": "python scripts/build_cerebrasense_control_tower.py",
        }

    if _safe_float(candidate.get("subject_consensus_auroc")) < OASIS2_PROMOTION_GATES["subject_consensus_auroc"]:
        return {
            "id": "run_v4_subject_consensus",
            "label": "Run V4 Consensus",
            "priority": "high",
            "reason": "Subject-consensus AUROC is below the promotion gate.",
            "command": "python scripts/train_oasis2.py --config configs/oasis2_train_multimodal_v4_subject_consensus.yaml",
        }

    return {
        "id": "run_v2_specificity",
        "label": "Run V2 Specificity",
        "priority": "medium",
        "reason": "OASIS-2 remains blocked by metric gates; continue the reliability ladder.",
        "command": "python scripts/train_oasis2.py --config configs/oasis2_train_multimodal_v2.yaml",
    }


def build_control_tower_payload(
    *,
    research_payload: dict[str, Any],
    model_board: dict[str, Any],
    run_registry: dict[str, Any],
    progression: dict[str, Any],
    model_cards: dict[str, Any],
    handoff_pack: dict[str, Any],
    deployment_readiness: dict[str, Any],
    demo_bundle_manifest: dict[str, Any],
    source_artifacts: dict[str, str],
) -> dict[str, Any]:
    """Build the unified Control Tower payload from generated evidence artifacts."""

    blockers = research_payload.get("promotion_blockers", [])
    candidate = research_payload.get("oasis2_candidate", {})
    next_best_action = build_next_best_action(research_payload)
    evidence_health_status = "pass" if run_registry.get("integrity_status") == "pass" and model_cards.get("card_count", 0) else "warn"
    if blockers:
        evidence_health_status = "warn"
    deployment_status = "blocked" if not deployment_readiness.get("onnx_export_allowed") else "review_ready"
    control_status = "candidate_blocked" if blockers else "promotion_review_ready"
    if not candidate.get("run_name"):
        control_status = "missing_candidate"

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "cerebrasense_control_tower",
        "decision_support_note": DECISION_SUPPORT_NOTE,
        "control_tower_status": {
            "status": control_status,
            "label": control_status.replace("_", " ").title(),
            "candidate_run_name": candidate.get("run_name"),
            "active_run_name": research_payload.get("active_model", {}).get("run_name"),
            "candidate_only": True,
            "human_review_required": True,
        },
        "next_best_action": next_best_action,
        "evidence_health": {
            "status": evidence_health_status,
            "model_board_entries": model_board.get("entry_count", 0),
            "run_registry_status": run_registry.get("integrity_status"),
            "model_card_count": model_cards.get("card_count", 0),
            "promotion_blocker_count": len(blockers),
            "trajectory_review_subject_count": progression.get("trajectory_review_subject_count", 0),
            "decision_support_wording_present": DECISION_SUPPORT_NOTE in json.dumps(research_payload),
        },
        "deployment_health": {
            "status": deployment_status,
            "readiness_status": deployment_readiness.get("readiness_status"),
            "onnx_export_allowed": bool(deployment_readiness.get("onnx_export_allowed")),
            "benchmark_status": deployment_readiness.get("benchmark_status"),
            "local_demo_path": "http://127.0.0.1:8000/demo/",
            "static_demo_path": "http://127.0.0.1:8080/",
        },
        "active_vs_candidate_deltas": _active_vs_candidate_deltas(research_payload),
        "failed_ablations": research_payload.get("failed_ablations", []),
        "candidate_comparison": research_payload.get("candidate_comparison", {}),
        "next_candidate_run_name": research_payload.get("next_candidate_run_name"),
        "blocker_summary": {
            "count": len(blockers),
            "metrics": [blocker.get("metric") for blocker in blockers],
            "promotion_gates": dict(OASIS2_PROMOTION_GATES),
        },
        "reviewer_logic": {
            "handoff_case_count": handoff_pack.get("review_queue", {}).get("total_case_count", 0),
            "error_taxonomy": handoff_pack.get("error_learning_loop", {}).get("taxonomy", []),
            "decision_policy": handoff_pack.get("error_learning_loop", {}).get("decision_policy"),
        },
        "demo_actions": demo_bundle_manifest.get("actions", []),
        "source_artifacts": source_artifacts,
        "claim_policy": {
            "scope": "OASIS-first longitudinal structural MRI research decision support.",
            "forbidden_claims": [
                "autonomous diagnosis",
                "medical device",
                "OASIS-2 replacement before gates pass",
                "silent external-dataset mixing",
            ],
        },
    }


def extend_research_payload_with_control_tower(
    research_payload: dict[str, Any],
    control_tower_payload: dict[str, Any],
) -> dict[str, Any]:
    """Add compact Control Tower fields to the frontend Research Mode contract."""

    extended = dict(research_payload)
    for key in (
        "control_tower_status",
        "next_best_action",
        "evidence_health",
        "deployment_health",
        "active_vs_candidate_deltas",
    ):
        extended[key] = control_tower_payload[key]
    return extended


def _write_control_tower_md(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# CerebraSense Control Tower",
        "",
        payload["decision_support_note"],
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- status: {payload['control_tower_status']['status']}",
        f"- next_best_action: {payload['next_best_action']['id']}",
        f"- evidence_health: {payload['evidence_health']['status']}",
        f"- deployment_health: {payload['deployment_health']['status']}",
        f"- promotion_blockers: {payload['blocker_summary']['count']}",
        "",
        "## Active vs Candidate",
        "",
        f"- active_run_name: {payload['active_vs_candidate_deltas']['active_run_name']}",
        f"- candidate_run_name: {payload['active_vs_candidate_deltas']['candidate_run_name']}",
        f"- auroc_delta: {payload['active_vs_candidate_deltas']['auroc_delta']}",
        f"- specificity_delta: {payload['active_vs_candidate_deltas']['specificity_delta']}",
        f"- review_required_delta: {payload['active_vs_candidate_deltas']['review_required_delta']}",
        "",
        "## Next Best Action",
        "",
        f"- label: {payload['next_best_action']['label']}",
        f"- priority: {payload['next_best_action']['priority']}",
        f"- reason: {payload['next_best_action']['reason']}",
        f"- command: `{payload['next_best_action']['command']}`",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_research_evidence_packet(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# CerebraSense Research Evidence Packet",
        "",
        payload["decision_support_note"],
        "",
        "## Scope",
        "",
        "CerebraSense is an OASIS-first longitudinal structural MRI research decision-support platform.",
        "It does not make diagnosis claims, medical-device claims, or silent external-dataset harmonization claims.",
        "",
        "## Evidence Health",
        "",
        f"- status: {payload['evidence_health']['status']}",
        f"- model_board_entries: {payload['evidence_health']['model_board_entries']}",
        f"- model_card_count: {payload['evidence_health']['model_card_count']}",
        f"- promotion_blocker_count: {payload['evidence_health']['promotion_blocker_count']}",
        "",
        "## Failure Modes",
        "",
        f"- blocker_metrics: {', '.join(str(metric) for metric in payload['blocker_summary']['metrics'])}",
        f"- handoff_case_count: {payload['reviewer_logic']['handoff_case_count']}",
        f"- error_taxonomy: {', '.join(payload['reviewer_logic']['error_taxonomy'])}",
        "",
        "## Deployment Limits",
        "",
        f"- deployment_health: {payload['deployment_health']['status']}",
        f"- onnx_export_allowed: {payload['deployment_health']['onnx_export_allowed']}",
        "- OASIS-2 remains candidate-only until strict promotion gates pass and review confirms the decision.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def build_cerebrasense_control_tower(
    *,
    settings: AppSettings | None = None,
    output_root: Path | None = None,
    frontend_payload_path: Path | None = None,
    refresh_next_level: bool = True,
) -> ControlTowerArtifacts:
    """Build Control Tower artifacts and refresh the frontend Research Mode payload."""

    resolved_settings = settings or get_app_settings()
    resolved_output_root = ensure_directory(
        output_root or resolved_settings.outputs_root / "reports" / "control_tower" / "current"
    )
    base_payload_path = resolved_output_root / "research_mode_payload_base.json"
    if refresh_next_level:
        next_artifacts = build_next_level_artifacts(
            settings=resolved_settings,
            frontend_payload_path=base_payload_path,
        )
        next_level_root = next_artifacts.output_root
    else:
        next_level_root = resolved_settings.outputs_root / "reports" / "next_level" / "current"
        if not base_payload_path.exists():
            base_payload_path = next_level_root / "research_mode_payload.json"

    research_payload = _read_json(base_payload_path)
    model_board = _read_json(next_level_root / "model_board.json")
    run_registry = _read_json(next_level_root / "oasis2_run_registry.json")
    progression = _read_json(next_level_root / "oasis2_progression_panel.json")
    handoff_pack = _read_json(next_level_root / "review_handoff_pack.json")
    model_cards = _read_json(next_level_root / "model_cards.json")
    deployment_readiness = _read_json(next_level_root / "deployment_readiness.json")
    demo_bundle_manifest = _read_json(next_level_root / "demo_bundle_manifest.json")
    source_artifacts = {
        "model_board_json": _portable_path(next_level_root / "model_board.json", resolved_settings.workspace_root),
        "run_registry_json": _portable_path(next_level_root / "oasis2_run_registry.json", resolved_settings.workspace_root),
        "progression_json": _portable_path(next_level_root / "oasis2_progression_panel.json", resolved_settings.workspace_root),
        "handoff_pack_json": _portable_path(next_level_root / "review_handoff_pack.json", resolved_settings.workspace_root),
        "model_cards_json": _portable_path(next_level_root / "model_cards.json", resolved_settings.workspace_root),
        "deployment_readiness_json": _portable_path(next_level_root / "deployment_readiness.json", resolved_settings.workspace_root),
    }

    control_tower_payload = build_control_tower_payload(
        research_payload=research_payload,
        model_board=model_board,
        run_registry=run_registry,
        progression=progression,
        model_cards=model_cards,
        handoff_pack=handoff_pack,
        deployment_readiness=deployment_readiness,
        demo_bundle_manifest=demo_bundle_manifest,
        source_artifacts=source_artifacts,
    )
    frontend_payload = extend_research_payload_with_control_tower(research_payload, control_tower_payload)

    control_json = resolved_output_root / "control_tower.json"
    control_md = resolved_output_root / "control_tower.md"
    evidence_packet_md = resolved_output_root / "research_evidence_packet.md"
    research_payload_json = resolved_output_root / "research_mode_payload.json"
    control_json.write_text(json.dumps(control_tower_payload, indent=2), encoding="utf-8")
    _write_control_tower_md(control_tower_payload, control_md)
    _write_research_evidence_packet(control_tower_payload, evidence_packet_md)
    research_payload_json.write_text(json.dumps(frontend_payload, indent=2), encoding="utf-8")

    frontend_payload_written_path: Path | None = None
    frontend_payload_write_status = "not_requested"
    if frontend_payload_path is not None:
        ensure_directory(frontend_payload_path.parent)
        try:
            frontend_payload_path.write_text(json.dumps(frontend_payload, indent=2), encoding="utf-8")
            frontend_payload_written_path = frontend_payload_path
            frontend_payload_write_status = "written"
        except PermissionError:
            fallback_path = resolved_output_root / "frontend_research_mode_write_fallback.json"
            fallback_path.write_text(json.dumps(frontend_payload, indent=2), encoding="utf-8")
            frontend_payload_written_path = fallback_path
            frontend_payload_write_status = "fallback_written_permission_denied"

    return ControlTowerArtifacts(
        output_root=resolved_output_root,
        control_tower_json_path=control_json,
        control_tower_md_path=control_md,
        research_evidence_packet_md_path=evidence_packet_md,
        research_payload_json_path=research_payload_json,
        frontend_payload_json_path=frontend_payload_written_path,
        frontend_payload_write_status=frontend_payload_write_status,
        next_level_output_root=next_level_root,
    )
