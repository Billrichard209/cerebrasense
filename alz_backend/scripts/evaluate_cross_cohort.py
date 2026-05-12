"""Evaluate an OASIS-2 model on OASIS-1 data (Cross-Cohort Generalization).

This script tests for "Domain Shift" or "Scanner Bias" by taking a model trained 
on OASIS-2 longitudinal data and testing its zero-shot performance on the
OASIS-1 cross-sectional dataset.
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.configs.runtime import get_app_settings
from src.data.oasis_loaders import OASISLoaderConfig, build_oasis_dataloaders
from src.evaluation.evaluate_oasis import evaluate_oasis_model_on_loader
from src.evaluation.oasis_run import load_oasis_checkpoint
from src.models.factory import load_oasis_model_config, build_model
from src.training.oasis_research import load_oasis_transform_config

def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate an OASIS-2 model on OASIS-1 data.")
    parser.add_argument("--run-name", required=True, help="Name of the trained OASIS-2 run (e.g., oasis2_bias_stability_v1).")
    parser.add_argument("--device", default="cpu", help="Device to run inference on.")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size for OASIS-1 loader.")
    parser.add_argument("--threshold", type=float, default=0.5, help="Classification threshold.")
    parser.add_argument("--output-json", type=Path, default=Path("outputs/reports/cross_cohort_evaluation.json"), help="Output path.")
    return parser.parse_args()

def main():
    args = parse_args()
    settings = get_app_settings()
    
    run_root = settings.outputs_root / "runs" / "oasis2" / args.run_name
    checkpoint_path = run_root / "checkpoints" / "best_model.pt"
    
    if not checkpoint_path.exists():
        print(f"Error: Checkpoint not found at {checkpoint_path}")
        sys.exit(1)
        
    print(f"Loading OASIS-2 model from {checkpoint_path}...")
    checkpoint = load_oasis_checkpoint(checkpoint_path, device=args.device)
    
    # We assume the model config is in the run root or we use default
    config_path = run_root / "model_config.yaml"
    model_cfg = load_oasis_model_config(config_path if config_path.exists() else None)
    
    model = build_model(model_cfg).to(args.device)
    model.load_state_dict(checkpoint.model_state_dict)
    model.eval()
    
    print("Building OASIS-1 Data Loaders...")
    transform_cfg = load_oasis_transform_config()
    loader_cfg = OASISLoaderConfig(
        batch_size=args.batch_size,
        transform_config=transform_cfg,
    )
    dataloaders = build_oasis_dataloaders(loader_cfg)
    test_loader = dataloaders.test_loader
    
    print(f"Evaluating OASIS-2 model on OASIS-1 Test Set (N={len(test_loader.dataset)})...")
    
    result = evaluate_oasis_model_on_loader(
        model=model,
        loader=test_loader,
        device=args.device,
        class_names=model_cfg.class_names,
        decision_threshold=args.threshold,
    )
    
    print("\n--- Cross-Cohort Results ---")
    metrics = result.metrics
    print(f"Accuracy:    {metrics.get('accuracy', 0.0):.4f}")
    print(f"AUROC:       {metrics.get('auroc', 0.0):.4f}")
    print(f"F1 Score:    {metrics.get('f1', 0.0):.4f}")
    print(f"Sensitivity: {metrics.get('sensitivity', 0.0):.4f}")
    print(f"Specificity: {metrics.get('specificity', 0.0):.4f}")
    
    payload = {
        "source_model": args.run_name,
        "target_dataset": "oasis1",
        "threshold": args.threshold,
        "metrics": metrics
    }
    
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nReport saved to {args.output_json}")

if __name__ == "__main__":
    main()
