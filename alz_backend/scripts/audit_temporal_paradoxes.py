"""Audit temporal paradoxes in longitudinal predictions.

This script identifies subjects whose predicted Dementia risk drops
significantly between visits, which contradicts the irreversible
nature of the disease and highlights potential model instability.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SESSION_VISIT_PATTERN = re.compile(r"_MR(\d+)\b", re.IGNORECASE)

def _extract_visit_number(session_id: str) -> int:
    match = SESSION_VISIT_PATTERN.search(str(session_id))
    return int(match.group(1)) if match else 999

def parse_args():
    parser = argparse.ArgumentParser(description="Audit temporal paradoxes in predictions.")
    parser.add_argument("--predictions-csv", type=Path, required=True, help="Path to predictions.csv from evaluation.")
    parser.add_argument("--output-json", type=Path, required=True, help="Path to save paradox report.")
    parser.add_argument("--epsilon", type=float, default=0.15, help="Minimum probability drop to consider a paradox.")
    return parser.parse_args()

def main():
    args = parse_args()
    
    if not args.predictions_csv.exists():
        print(f"Error: {args.predictions_csv} not found.")
        sys.exit(1)

    df = pd.read_csv(args.predictions_csv)
    
    # Ensure necessary columns exist
    required_cols = {"sample_id", "probability_class_1"}
    if not required_cols.issubset(df.columns):
        print(f"Error: CSV must contain {required_cols}")
        sys.exit(1)

    # Reconstruct subject_id from sample_id (e.g., OAS2_0001_MR1 -> OAS2_0001)
    if "meta_subject_id" in df.columns:
        df["subject_id"] = df["meta_subject_id"]
    else:
        df["subject_id"] = df["sample_id"].apply(lambda x: "_".join(str(x).split("_")[:2]))
    
    df["visit_order"] = df["sample_id"].apply(_extract_visit_number)
    
    paradoxes = []
    total_transitions = 0
    
    # Group by subject and sort by visit
    for subject_id, group in df.groupby("subject_id"):
        sorted_group = group.sort_values("visit_order").to_dict("records")
        if len(sorted_group) < 2:
            continue
            
        for i in range(len(sorted_group) - 1):
            visit_t = sorted_group[i]
            visit_t_plus_1 = sorted_group[i+1]
            
            prob_t = float(visit_t["probability_class_1"])
            prob_t_plus_1 = float(visit_t_plus_1["probability_class_1"])
            
            total_transitions += 1
            
            drop = prob_t - prob_t_plus_1
            if drop >= args.epsilon:
                paradoxes.append({
                    "subject_id": subject_id,
                    "visit_t_id": visit_t["sample_id"],
                    "visit_t_plus_1_id": visit_t_plus_1["sample_id"],
                    "prob_t": round(prob_t, 4),
                    "prob_t_plus_1": round(prob_t_plus_1, 4),
                    "drop": round(drop, 4),
                    "severity": "critical" if drop >= 0.3 else "warning"
                })

    # Sort paradoxes by drop magnitude
    paradoxes.sort(key=lambda x: x["drop"], reverse=True)
    
    report = {
        "epsilon": args.epsilon,
        "total_subjects_with_history": len(df.groupby("subject_id").filter(lambda x: len(x) > 1).subject_id.unique()),
        "total_transitions_checked": total_transitions,
        "paradox_count": len(paradoxes),
        "paradox_rate": round(len(paradoxes) / total_transitions, 4) if total_transitions > 0 else 0,
        "paradoxes": paradoxes
    }
    
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    
    print(f"Audit complete. Found {len(paradoxes)} paradoxes out of {total_transitions} transitions.")
    print(f"Report saved to {args.output_json}")
    
    if paradoxes:
        print("\nTop 3 Worst Paradoxes:")
        for p in paradoxes[:3]:
            print(f"- {p['subject_id']}: {p['visit_t_id']} ({p['prob_t']}) -> {p['visit_t_plus_1_id']} ({p['prob_t_plus_1']}) [Drop: {p['drop']}]")

if __name__ == "__main__":
    main()
