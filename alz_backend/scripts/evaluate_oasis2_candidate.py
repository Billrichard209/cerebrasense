"""Evaluate, calibrate, and compare an OASIS-2 candidate checkpoint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.configs.runtime import get_app_settings  # noqa: E402
from src.evaluation.oasis2_run import (  # noqa: E402
    OASIS2RunEvaluationConfig,
    evaluate_oasis2_run_checkpoint,
    save_oasis2_vs_oasis1_comparison,
)
from src.evaluation.thresholds import calibrate_binary_threshold  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate and calibrate an OASIS-2 candidate against OASIS-1.")
    parser.add_argument("--run-name", default="oasis2_colab_improved_v1")
    parser.add_argument("--checkpoint-path", type=Path, default=None)
    parser.add_argument("--checkpoint-name", default="best_model.pt")
    parser.add_argument("--training-config-path", type=Path, default=None)
    parser.add_argument("--model-config-path", type=Path, default=None)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--num-workers", type=int, default=None)
    parser.add_argument("--cache-rate", type=float, default=None)
    parser.add_argument("--image-size", type=int, nargs=3, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--split-seed", type=int, default=None)
    parser.add_argument("--max-batches", type=int, default=None)
    parser.add_argument("--selection-metric", default="youden_index")
    parser.add_argument("--threshold-step", type=float, default=0.01)
    return parser


def _cfg(args: argparse.Namespace, *, split: str, threshold: float | None, output_name: str) -> OASIS2RunEvaluationConfig:
    return OASIS2RunEvaluationConfig(
        run_name=args.run_name,
        split=split,
        checkpoint_name=args.checkpoint_name,
        checkpoint_path=args.checkpoint_path,
        training_config_path=args.training_config_path,
        model_config_path=args.model_config_path,
        threshold=threshold,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        cache_rate=args.cache_rate,
        image_size=None if args.image_size is None else tuple(args.image_size),
        seed=args.seed,
        split_seed=args.split_seed,
        device=args.device,
        max_batches=args.max_batches,
        output_name=output_name,
    )


def main() -> None:
    args = build_parser().parse_args()
    settings = get_app_settings()

    val_eval = evaluate_oasis2_run_checkpoint(
        _cfg(args, split="val", threshold=0.5, output_name="post_train_val_best_model"),
        settings=settings,
    )
    test_raw = evaluate_oasis2_run_checkpoint(
        _cfg(args, split="test", threshold=0.5, output_name="post_train_test_best_model"),
        settings=settings,
    )

    run_root = settings.outputs_root / "runs" / "oasis2" / args.run_name
    calibration = calibrate_binary_threshold(
        validation_predictions_path=val_eval.paths.predictions_csv_path,
        test_predictions_path=test_raw.paths.predictions_csv_path,
        output_dir=run_root / "calibration" / f"threshold_{args.selection_metric}",
        selection_metric=args.selection_metric,
        threshold_step=args.threshold_step,
    )

    test_calibrated = evaluate_oasis2_run_checkpoint(
        _cfg(
            args,
            split="test",
            threshold=calibration.threshold,
            output_name=f"post_train_test_best_model_threshold_{args.selection_metric}",
        ),
        settings=settings,
    )
    comparison_path = save_oasis2_vs_oasis1_comparison(
        run_name=args.run_name,
        raw_test_metrics=test_raw.result.metrics,
        calibrated_test_metrics=test_calibrated.result.metrics,
        calibration=calibration,
        output_path=run_root / "reports" / "oasis2_vs_oasis1_comparison.md",
        settings=settings,
    )

    print(f"run_name={args.run_name}")
    print(f"val_metrics={val_eval.paths.metrics_json_path}")
    print(f"test_raw_metrics={test_raw.paths.metrics_json_path}")
    print(f"recommended_threshold={calibration.threshold}")
    print(f"threshold_calibration={calibration.calibration_report_path}")
    print(f"test_calibrated_metrics={test_calibrated.paths.metrics_json_path}")
    print(f"comparison={comparison_path}")
    print(json.dumps({"final_calibrated_test_metrics": test_calibrated.result.metrics}, indent=2))


if __name__ == "__main__":
    main()
