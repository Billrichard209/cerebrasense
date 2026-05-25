"""Standard OASIS-2 evaluation suite: val + test + threshold calibration + leaderboard."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _run(command: list[str]) -> None:
    print(" ".join(command), flush=True)
    result = subprocess.run(command, cwd=str(PROJECT_ROOT), check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the standard OASIS-2 post-train evaluation suite.")
    parser.add_argument("--run-name", type=str, required=True)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--skip-post-train", action="store_true")
    parser.add_argument("--workspace-root", type=Path, default=None)
    args = parser.parse_args()

    python = sys.executable
    if not args.skip_post_train:
        _run(
            [
                python,
                "scripts/post_train_pipeline.py",
                "--run-name",
                args.run_name,
                "--device",
                args.device,
            ]
        )

    _run(
        [
            python,
            "scripts/evaluate_oasis2_candidate.py",
            "--run-name",
            args.run_name,
            "--device",
            args.device,
            "--selection-metric",
            "balanced_accuracy",
        ]
    )

    _run(
        [
            python,
            "scripts/analyze_oasis2_mixed_label_errors.py",
            "--run-name",
            args.run_name,
        ]
    )

    leaderboard_cmd = [python, "scripts/build_oasis2_leaderboard.py"]
    if args.workspace_root is not None:
        leaderboard_cmd.extend(["--workspace-root", str(args.workspace_root)])
    _run(leaderboard_cmd)

    print(json.dumps({"status": "ok", "run_name": args.run_name}, indent=2))


if __name__ == "__main__":
    main()
