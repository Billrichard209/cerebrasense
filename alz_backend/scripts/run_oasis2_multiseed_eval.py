"""Train/evaluate OASIS-2 across multiple split seeds and summarize test AUROC stability."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.configs.runtime import get_app_settings  # noqa: E402
from src.utils.io_utils import ensure_directory  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OASIS-2 multi-seed evaluation summary.")
    parser.add_argument("--base-run-name", type=str, required=True, help="Prefix, e.g. oasis2_mri_baseline_v2")
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--dry-run-train", action="store_true", help="Only run eval suite on existing runs.")
    parser.add_argument("--training-cohort", type=str, default="full")
    args = parser.parse_args()

    settings = get_app_settings()
    python = sys.executable
    rows: list[dict] = []

    for seed in args.seeds:
        run_name = f"{args.base_run_name}_seed{seed}"
        if not args.dry_run_train:
            train_cmd = [
                python,
                "scripts/train_oasis2.py",
                "--run-name",
                run_name,
                "--split-seed",
                str(seed),
                "--training-cohort",
                args.training_cohort,
                "--device",
                args.device,
            ]
            if args.config is not None:
                train_cmd.extend(["--config", str(args.config)])
            print(" ".join(train_cmd), flush=True)
            if subprocess.run(train_cmd, cwd=str(PROJECT_ROOT)).returncode != 0:
                raise SystemExit(f"Training failed for seed {seed}")

        eval_cmd = [python, "scripts/run_oasis2_eval_suite.py", "--run-name", run_name, "--device", args.device]
        if subprocess.run(eval_cmd, cwd=str(PROJECT_ROOT)).returncode != 0:
            raise SystemExit(f"Evaluation suite failed for seed {seed}")

        metrics_path = (
            settings.outputs_root
            / "runs"
            / "oasis2"
            / run_name
            / "evaluation"
            / "post_train_test_best_model_threshold_balanced_accuracy"
            / "metrics.json"
        )
        if not metrics_path.exists():
            metrics_path = (
                settings.outputs_root
                / "runs"
                / "oasis2"
                / run_name
                / "evaluation"
                / "post_train_test_best_model"
                / "metrics.json"
            )
        metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
        rows.append(
            {
                "run_name": run_name,
                "seed": seed,
                "test_auroc": metrics.get("auroc"),
                "test_balanced_accuracy": metrics.get("balanced_accuracy", metrics.get("accuracy")),
                "test_specificity": metrics.get("specificity"),
                "test_f1": metrics.get("f1"),
            }
        )

    frame = pd.DataFrame(rows)
    output_dir = ensure_directory(settings.outputs_root / "experiments" / "oasis2_multiseed")
    csv_path = output_dir / f"{args.base_run_name}_multiseed_summary.csv"
    frame.to_csv(csv_path, index=False)
    summary = {
        "base_run_name": args.base_run_name,
        "seeds": args.seeds,
        "test_auroc_mean": float(frame["test_auroc"].mean()) if not frame.empty else None,
        "test_auroc_std": float(frame["test_auroc"].std()) if len(frame) > 1 else 0.0,
        "output_csv": str(csv_path),
        "rows": rows,
    }
    (output_dir / f"{args.base_run_name}_multiseed_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
