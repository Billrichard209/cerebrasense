"""Build the CerebraSense Control Tower evidence bundle and frontend payload."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.control_tower import build_cerebrasense_control_tower  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Optional report output root. Defaults to outputs/reports/control_tower/current.",
    )
    parser.add_argument(
        "--frontend-payload-path",
        type=Path,
        default=WORKSPACE_ROOT / "frontend_demo" / "data" / "research_mode.json",
        help="JSON payload consumed by frontend_demo Research Mode.",
    )
    parser.add_argument(
        "--skip-next-level-refresh",
        action="store_true",
        help="Use existing next-level artifacts instead of rebuilding them first.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifacts = build_cerebrasense_control_tower(
        output_root=args.output_root,
        frontend_payload_path=args.frontend_payload_path,
        refresh_next_level=not args.skip_next_level_refresh,
    )
    print(
        json.dumps(
            {
                "output_root": str(artifacts.output_root),
                "control_tower_json": str(artifacts.control_tower_json_path),
                "control_tower_md": str(artifacts.control_tower_md_path),
                "research_evidence_packet_md": str(artifacts.research_evidence_packet_md_path),
                "research_payload_json": str(artifacts.research_payload_json_path),
                "frontend_payload_json": (
                    None if artifacts.frontend_payload_json_path is None else str(artifacts.frontend_payload_json_path)
                ),
                "frontend_payload_write_status": artifacts.frontend_payload_write_status,
                "next_level_output_root": str(artifacts.next_level_output_root),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
