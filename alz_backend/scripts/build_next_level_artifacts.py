"""Build the next-level CerebraSense evidence and frontend demo artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.next_level import build_next_level_artifacts  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Optional report output root. Defaults to outputs/reports/next_level/current.",
    )
    parser.add_argument(
        "--frontend-payload-path",
        type=Path,
        default=WORKSPACE_ROOT / "frontend_demo" / "data" / "research_mode.json",
        help="JSON payload consumed by frontend_demo Research Mode.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifacts = build_next_level_artifacts(
        output_root=args.output_root,
        frontend_payload_path=args.frontend_payload_path,
    )
    print(
        json.dumps(
            {
                "output_root": str(artifacts.output_root),
                "model_board_json": str(artifacts.model_board_json_path),
                "progression_json": str(artifacts.progression_json_path),
                "frontend_payload_json": str(artifacts.demo_payload_json_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
