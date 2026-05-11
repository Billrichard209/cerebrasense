"""Run-level OASIS-2 checkpoint evaluation and comparison helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.configs.runtime import AppSettings, get_app_settings
from src.data.oasis2_loaders import OASIS2LoaderConfig, build_oasis2_dataloaders
from src.evaluation.calibration import ConfidenceBandConfig
from src.evaluation.evaluate_oasis import OASISEvaluationResult, evaluate_oasis_model_on_loader
from src.evaluation.metrics import compute_binary_classification_metrics, threshold_binary_scores
from src.evaluation.oasis_run import LoadedCheckpoint, load_oasis_checkpoint
from src.evaluation.thresholds import ThresholdCalibrationResult
from src.models.factory import OASISModelConfig, build_model, load_oasis_model_config
from src.training.oasis2_research import default_oasis2_train_config_path, load_oasis_transform_config_for_oasis2
from src.training.oasis_research import ResearchOASISTrainingConfig, load_research_oasis_training_config
from src.utils.io_utils import ensure_directory


class OASIS2RunEvaluationError(ValueError):
    """Raised when OASIS-2 run evaluation cannot proceed safely."""


@dataclass(slots=True, frozen=True)
class OASIS2RunEvaluationConfig:
    """Configuration for evaluating one OASIS-2 checkpoint."""

    run_name: str
    split: str = "val"
    checkpoint_name: str = "best_model.pt"
    checkpoint_path: Path | None = None
    training_config_path: Path | None = None
    model_config_path: Path | None = None
    threshold: float | None = None
    batch_size: int | None = None
    num_workers: int | None = None
    cache_rate: float | None = None
    image_size: tuple[int, int, int] | None = None
    seed: int | None = None
    split_seed: int | None = None
    device: str = "cpu"
    max_batches: int | None = None
    output_name: str | None = None


@dataclass(slots=True)
class OASIS2RunEvaluationPaths:
    """Output paths for OASIS-2 run evaluation."""

    evaluation_root: Path
    report_json_path: Path
    predictions_csv_path: Path
    metrics_json_path: Path
    summary_report_path: Path


@dataclass(slots=True)
class OASIS2RunEvaluationResult:
    """OASIS-2 evaluation result plus saved artifacts."""

    config: OASIS2RunEvaluationConfig
    checkpoint: LoadedCheckpoint
    result: OASISEvaluationResult
    paths: OASIS2RunEvaluationPaths


def resolve_oasis2_run_root(settings: AppSettings, run_name: str) -> Path:
    """Return the standard local OASIS-2 run root, creating it for imported runs."""

    return ensure_directory(settings.outputs_root / "runs" / "oasis2" / run_name)


def resolve_oasis2_checkpoint_path(
    cfg: OASIS2RunEvaluationConfig,
    *,
    settings: AppSettings | None = None,
) -> Path:
    """Resolve the checkpoint for an OASIS-2 run evaluation."""

    if cfg.checkpoint_path is not None:
        checkpoint_path = Path(cfg.checkpoint_path)
    else:
        resolved_settings = settings or get_app_settings()
        checkpoint_path = resolve_oasis2_run_root(resolved_settings, cfg.run_name) / "checkpoints" / cfg.checkpoint_name
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"OASIS-2 checkpoint not found: {checkpoint_path}")
    return checkpoint_path


def _load_training_config(cfg: OASIS2RunEvaluationConfig) -> ResearchOASISTrainingConfig:
    return load_research_oasis_training_config(cfg.training_config_path or default_oasis2_train_config_path())


def load_oasis2_model_for_evaluation(
    cfg: OASIS2RunEvaluationConfig,
    *,
    settings: AppSettings | None = None,
) -> tuple[object, OASISModelConfig, LoadedCheckpoint]:
    """Build the OASIS-2 model and load the requested checkpoint."""

    training_cfg = _load_training_config(cfg)
    model_cfg = load_oasis_model_config(cfg.model_config_path or training_cfg.model_config_path)
    checkpoint = load_oasis_checkpoint(resolve_oasis2_checkpoint_path(cfg, settings=settings), device=cfg.device)
    model = build_model(model_cfg)
    model.load_state_dict(checkpoint.model_state_dict)
    return model, model_cfg, checkpoint


def _effective_data_value(explicit: Any, fallback: Any) -> Any:
    return fallback if explicit is None else explicit


def _build_loader(cfg: OASIS2RunEvaluationConfig) -> object:
    """Build the requested OASIS-2 split loader."""

    if cfg.split not in {"val", "test"}:
        raise OASIS2RunEvaluationError(f"OASIS-2 evaluation supports split='val' or 'test', got {cfg.split!r}.")

    training_cfg = _load_training_config(cfg)
    data_cfg = training_cfg.data
    image_size = tuple(_effective_data_value(cfg.image_size, data_cfg.image_size))
    loader_cfg = OASIS2LoaderConfig(
        seed=int(_effective_data_value(cfg.seed, data_cfg.seed)),
        split_seed=_effective_data_value(cfg.split_seed, data_cfg.split_seed),
        train_fraction=data_cfg.train_fraction,
        val_fraction=data_cfg.val_fraction,
        test_fraction=data_cfg.test_fraction,
        batch_size=int(_effective_data_value(cfg.batch_size, data_cfg.batch_size)),
        num_workers=int(_effective_data_value(cfg.num_workers, data_cfg.num_workers)),
        cache_rate=float(_effective_data_value(cfg.cache_rate, data_cfg.cache_rate)),
        transform_config=load_oasis_transform_config_for_oasis2(
            ResearchOASISTrainingConfig(
                run_name=training_cfg.run_name,
                epochs=training_cfg.epochs,
                device=training_cfg.device,
                mixed_precision=training_cfg.mixed_precision,
                deterministic=training_cfg.deterministic,
                dry_run=training_cfg.dry_run,
                model_config_path=training_cfg.model_config_path,
                data=type(data_cfg)(**{**asdict(data_cfg), "image_size": image_size}),
                optimizer=training_cfg.optimizer,
                scheduler=training_cfg.scheduler,
                loss=training_cfg.loss,
                early_stopping=training_cfg.early_stopping,
                checkpoint=training_cfg.checkpoint,
            )
        ),
    )
    dataloaders = build_oasis2_dataloaders(loader_cfg)
    return dataloaders.val_loader if cfg.split == "val" else dataloaders.test_loader


def _evaluation_folder_name(cfg: OASIS2RunEvaluationConfig) -> str:
    checkpoint_stem = Path(cfg.checkpoint_name).stem
    return (cfg.output_name or f"{cfg.split}_{checkpoint_stem}").replace(" ", "_").replace("/", "_").replace("\\", "_")


def build_oasis2_run_evaluation_paths(
    cfg: OASIS2RunEvaluationConfig,
    *,
    settings: AppSettings | None = None,
) -> OASIS2RunEvaluationPaths:
    """Build output paths for an OASIS-2 evaluation."""

    resolved_settings = settings or get_app_settings()
    run_root = resolve_oasis2_run_root(resolved_settings, cfg.run_name)
    evaluation_root = ensure_directory(run_root / "evaluation" / _evaluation_folder_name(cfg))
    return OASIS2RunEvaluationPaths(
        evaluation_root=evaluation_root,
        report_json_path=evaluation_root / "evaluation_report.json",
        predictions_csv_path=evaluation_root / "predictions.csv",
        metrics_json_path=evaluation_root / "metrics.json",
        summary_report_path=evaluation_root / "summary_report.md",
    )


def _prediction_rows(result: OASISEvaluationResult) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    threshold = result.metrics.get("threshold")
    for prediction in result.predictions:
        row = {
            "sample_id": prediction.sample_id,
            "true_label": prediction.true_label,
            "true_label_name": prediction.true_label_name,
            "predicted_label": prediction.predicted_label,
            "predicted_label_name": prediction.predicted_label_name,
            "threshold": threshold,
            "confidence": prediction.confidence,
            "calibrated_probability_score": prediction.calibrated_probability_score,
            "confidence_level": prediction.confidence_level,
            "review_flag": prediction.review_flag,
            "entropy": prediction.entropy,
            "normalized_entropy": prediction.normalized_entropy,
            "probability_margin": prediction.probability_margin,
            "uncertainty_score": prediction.uncertainty_score,
        }
        for index, probability in enumerate(prediction.probabilities):
            row[f"probability_class_{index}"] = probability
        for key, value in prediction.meta.items():
            row[f"meta_{key}"] = value
        rows.append(row)
    return rows


def _json_safe(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(nested) for key, nested in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return str(value)


def save_oasis2_run_evaluation(
    *,
    cfg: OASIS2RunEvaluationConfig,
    checkpoint: LoadedCheckpoint,
    result: OASISEvaluationResult,
    paths: OASIS2RunEvaluationPaths,
) -> None:
    """Save JSON, CSV, and Markdown reports for one OASIS-2 evaluation."""

    result.metrics["subject_consensus"] = compute_oasis2_subject_consensus_metrics(result)
    payload = result.to_payload()
    payload["run"] = {
        "run_name": cfg.run_name,
        "split": cfg.split,
        "checkpoint_path": str(checkpoint.path),
        "checkpoint_metadata": _json_safe(
            {key: checkpoint.metadata.get(key) for key in ("epoch", "best_epoch", "best_monitor_value") if key in checkpoint.metadata}
        ),
        "config": {
            **asdict(cfg),
            "checkpoint_path": str(cfg.checkpoint_path) if cfg.checkpoint_path else None,
            "training_config_path": str(cfg.training_config_path) if cfg.training_config_path else None,
            "model_config_path": str(cfg.model_config_path) if cfg.model_config_path else None,
        },
    }
    paths.report_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    paths.metrics_json_path.write_text(json.dumps(result.metrics, indent=2), encoding="utf-8")
    pd.DataFrame(_prediction_rows(result)).to_csv(paths.predictions_csv_path, index=False)

    metrics = result.metrics
    lines = [
        f"# OASIS-2 Run Evaluation: {cfg.run_name}",
        "",
        "Research decision-support evaluation only; not diagnosis.",
        "",
        "## Run",
        "",
        f"- split: {cfg.split}",
        f"- checkpoint: {checkpoint.path}",
        f"- sample_count: {metrics.get('sample_count', 0)}",
        f"- threshold: {metrics.get('threshold', 0.5):.6f}",
        "",
        "## Metrics",
        "",
        f"- accuracy: {metrics.get('accuracy', 0.0):.6f}",
        f"- auroc: {metrics.get('auroc', 0.0):.6f}",
        f"- precision: {metrics.get('precision', 0.0):.6f}",
        f"- sensitivity: {metrics.get('sensitivity', metrics.get('recall_sensitivity', 0.0)):.6f}",
        f"- specificity: {metrics.get('specificity', 0.0):.6f}",
        f"- f1: {metrics.get('f1', 0.0):.6f}",
        f"- review_required_count: {metrics.get('review_required_count', 0)}",
        "",
        "## Subject Consensus",
        "",
        f"- subject_count: {metrics.get('subject_consensus', {}).get('sample_count', 0)}",
        f"- subject_accuracy: {metrics.get('subject_consensus', {}).get('accuracy', 0.0):.6f}",
        f"- subject_auroc: {metrics.get('subject_consensus', {}).get('auroc', 0.0):.6f}",
        f"- subject_f1: {metrics.get('subject_consensus', {}).get('f1', 0.0):.6f}",
        f"- subject_sensitivity: {metrics.get('subject_consensus', {}).get('sensitivity', 0.0):.6f}",
        f"- subject_specificity: {metrics.get('subject_consensus', {}).get('specificity', 0.0):.6f}",
        "",
        "## Notes",
        "",
        "- OASIS-2 is same-family longitudinal evidence, not a drop-in replacement for the active OASIS-1 baseline.",
        "- Promotion should require credible held-out test performance and improved specificity/review burden.",
    ]
    paths.summary_report_path.write_text("\n".join(lines), encoding="utf-8")


def compute_oasis2_subject_consensus_metrics(result: OASISEvaluationResult) -> dict[str, Any]:
    """Average visit probabilities per subject and score one consensus label per subject."""

    threshold = float(result.metrics.get("threshold", 0.5))
    grouped: dict[str, dict[str, list[float] | list[int]]] = {}
    for prediction in result.predictions:
        subject_id = str(prediction.meta.get("subject_id") or prediction.sample_id)
        grouped.setdefault(subject_id, {"scores": [], "labels": []})
        grouped[subject_id]["scores"].append(float(prediction.probabilities[1] if len(prediction.probabilities) > 1 else 0.0))
        if prediction.true_label is not None:
            grouped[subject_id]["labels"].append(int(prediction.true_label))

    y_true: list[int] = []
    y_score: list[float] = []
    for values in grouped.values():
        labels = [int(label) for label in values["labels"]]
        if not labels:
            continue
        scores = [float(score) for score in values["scores"]]
        y_true.append(max(labels))
        y_score.append(sum(scores) / len(scores))

    if not y_true:
        return {"sample_count": 0, "threshold": threshold}
    y_pred = threshold_binary_scores(y_score, threshold=threshold)
    metrics = compute_binary_classification_metrics(y_true, y_pred, y_score=y_score)
    metrics["threshold"] = threshold
    metrics["aggregation"] = "subject_mean_probability_ever_positive_label"
    return metrics


def evaluate_oasis2_run_checkpoint(
    cfg: OASIS2RunEvaluationConfig,
    *,
    settings: AppSettings | None = None,
) -> OASIS2RunEvaluationResult:
    """Evaluate a trained OASIS-2 checkpoint and save run-local artifacts."""

    resolved_settings = settings or get_app_settings()
    model, model_cfg, checkpoint = load_oasis2_model_for_evaluation(cfg, settings=resolved_settings)
    result = evaluate_oasis_model_on_loader(
        model=model,
        loader=_build_loader(cfg),
        device=cfg.device,
        class_names=model_cfg.class_names,
        max_batches=cfg.max_batches,
        calibration_config=ConfidenceBandConfig(),
        decision_threshold=float(cfg.threshold if cfg.threshold is not None else 0.5),
    )
    result.dataset = "oasis2"
    result.notes.append("OASIS-2 evaluation uses subject-safe supervised splits and explicit binary labels.")
    paths = build_oasis2_run_evaluation_paths(cfg, settings=resolved_settings)
    save_oasis2_run_evaluation(cfg=cfg, checkpoint=checkpoint, result=result, paths=paths)
    return OASIS2RunEvaluationResult(config=cfg, checkpoint=checkpoint, result=result, paths=paths)


def save_oasis2_vs_oasis1_comparison(
    *,
    run_name: str,
    raw_test_metrics: dict[str, Any],
    calibrated_test_metrics: dict[str, Any],
    calibration: ThresholdCalibrationResult,
    output_path: Path,
    settings: AppSettings | None = None,
) -> Path:
    """Write a compact comparison report against the active OASIS-1 baseline."""

    resolved_settings = settings or get_app_settings()
    registry_path = resolved_settings.outputs_root / "model_registry" / "oasis_current_baseline.json"
    active = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else {}
    oasis1_test = active.get("test_metrics", {})

    def metric_delta(metric: str) -> float | None:
        if metric not in calibrated_test_metrics or metric not in oasis1_test:
            return None
        return float(calibrated_test_metrics[metric]) - float(oasis1_test[metric])

    calibrated_review = float(calibrated_test_metrics.get("review_required_count", 0))
    oasis1_review = float(oasis1_test.get("review_required_count", 0))
    specificity_delta = metric_delta("specificity")
    credible = (
        metric_delta("auroc") is not None
        and metric_delta("f1") is not None
        and specificity_delta is not None
        and float(calibrated_test_metrics.get("auroc", 0.0)) >= float(oasis1_test.get("auroc", 1.0))
        and float(calibrated_test_metrics.get("f1", 0.0)) >= float(oasis1_test.get("f1", 1.0))
        and specificity_delta > 0.0
        and calibrated_review <= oasis1_review
    )
    recommendation = "promotion_candidate" if credible else "do_not_promote"

    lines = [
        f"# OASIS-2 Candidate Comparison: {run_name}",
        "",
        f"- recommendation: {recommendation}",
        f"- calibrated_threshold: {calibration.threshold}",
        f"- calibration_selection_metric: {calibration.selection_metric}",
        "",
        "## OASIS-2 Test Metrics",
        "",
        f"- raw_0_5_auroc: {raw_test_metrics.get('auroc')}",
        f"- raw_0_5_accuracy: {raw_test_metrics.get('accuracy')}",
        f"- calibrated_auroc: {calibrated_test_metrics.get('auroc')}",
        f"- calibrated_accuracy: {calibrated_test_metrics.get('accuracy')}",
        f"- calibrated_f1: {calibrated_test_metrics.get('f1')}",
        f"- calibrated_sensitivity: {calibrated_test_metrics.get('sensitivity', calibrated_test_metrics.get('recall_sensitivity'))}",
        f"- calibrated_specificity: {calibrated_test_metrics.get('specificity')}",
        f"- calibrated_review_required_count: {calibrated_test_metrics.get('review_required_count')}",
        f"- subject_accuracy: {calibrated_test_metrics.get('subject_consensus', {}).get('accuracy')}",
        f"- subject_auroc: {calibrated_test_metrics.get('subject_consensus', {}).get('auroc')}",
        f"- subject_f1: {calibrated_test_metrics.get('subject_consensus', {}).get('f1')}",
        f"- subject_specificity: {calibrated_test_metrics.get('subject_consensus', {}).get('specificity')}",
        "",
        "## Active OASIS-1 Baseline",
        "",
        f"- run_name: {active.get('run_name')}",
        f"- test_auroc: {oasis1_test.get('auroc')}",
        f"- test_accuracy: {oasis1_test.get('accuracy')}",
        f"- test_f1: {oasis1_test.get('f1')}",
        f"- test_sensitivity: {oasis1_test.get('sensitivity', oasis1_test.get('recall_sensitivity'))}",
        f"- test_specificity: {oasis1_test.get('specificity')}",
        f"- review_required_count: {oasis1_test.get('review_required_count')}",
        "",
        "## Decision Note",
        "",
        "- OASIS-2 is longitudinal/same-family evidence, not a drop-in replacement until held-out test metrics and review burden beat OASIS-1.",
        "- Promotion only if calibrated test performance is credible and specificity improves.",
    ]
    ensure_directory(output_path.parent)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
