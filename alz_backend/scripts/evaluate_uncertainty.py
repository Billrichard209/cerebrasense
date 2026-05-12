"""Monte Carlo Dropout Uncertainty Evaluation.

This script runs multiple forward passes with Dropout enabled during
inference to estimate the model's epistemic uncertainty. Scans with high
variance across passes are flagged as "Low Confidence".
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.configs.runtime import get_app_settings
from src.evaluation.evaluate_oasis import evaluate_oasis_model_on_loader
from src.evaluation.oasis_run import load_oasis_checkpoint
from src.models.factory import load_oasis_model_config, build_model
from src.data.oasis2_loaders import OASIS2LoaderConfig, build_oasis2_dataloaders
from src.training.oasis_research import load_oasis_transform_config

def enable_dropout(model):
    """Enable dropout layers during inference."""
    for m in model.modules():
        if m.__class__.__name__.startswith('Dropout'):
            m.train()

def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate Uncertainty using MC Dropout.")
    parser.add_argument("--run-name", required=True, help="Name of the trained run.")
    parser.add_argument("--passes", type=int, default=10, help="Number of Monte Carlo passes.")
    parser.add_argument("--device", default="cpu", help="Device to run inference on.")
    parser.add_argument("--output-json", type=Path, default=Path("outputs/reports/mc_dropout_uncertainty.json"), help="Output path.")
    return parser.parse_args()

def main():
    args = parse_args()
    settings = get_app_settings()
    
    run_root = settings.outputs_root / "runs" / "oasis2" / args.run_name
    checkpoint_path = run_root / "checkpoints" / "best_model.pt"
    
    if not checkpoint_path.exists():
        print(f"Error: Checkpoint not found at {checkpoint_path}")
        sys.exit(1)
        
    print(f"Loading model from {checkpoint_path}...")
    checkpoint = load_oasis_checkpoint(checkpoint_path, device=args.device)
    config_path = run_root / "model_config.yaml"
    model_cfg = load_oasis_model_config(config_path if config_path.exists() else None)
    
    model = build_model(model_cfg).to(args.device)
    model.load_state_dict(checkpoint.model_state_dict)
    
    # CRITICAL: We set eval() but then re-enable dropout
    model.eval()
    enable_dropout(model)
    
    print("Building Data Loader...")
    transform_cfg = load_oasis_transform_config()
    loader_cfg = OASIS2LoaderConfig(batch_size=1, transform_config=transform_cfg)
    dataloaders = build_oasis2_dataloaders(loader_cfg)
    test_loader = dataloaders.test_loader
    
    print(f"Running {args.passes} Monte Carlo passes on the Test Set...")
    
    # We will just run standard evaluation multiple times and collect probabilities
    import torch
    import torch.nn.functional as F
    
    uncertainty_results = []
    
    with torch.no_grad():
        for batch_idx, batch in enumerate(test_loader):
            inputs = batch["image"].to(args.device)
            sample_ids = batch.get("sample_id", [f"sample_{batch_idx}"])
            
            # Collect probabilities for N passes
            pass_probs = []
            for _ in range(args.passes):
                logits = model(inputs)
                probs = F.softmax(logits, dim=1).cpu().numpy()
                pass_probs.append(probs[:, 1]) # Probability of class 1 (Demented)
                
            pass_probs = np.array(pass_probs) # Shape: (passes, batch_size)
            
            means = np.mean(pass_probs, axis=0)
            variances = np.var(pass_probs, axis=0)
            
            for i, sample_id in enumerate(sample_ids):
                uncertainty_results.append({
                    "sample_id": sample_id,
                    "mean_probability": float(means[i]),
                    "variance": float(variances[i]),
                    "uncertainty_flag": "HIGH" if variances[i] > 0.05 else "LOW"
                })
                
            if batch_idx > 50:
                print("Stopping early for demo purposes (limit 50 batches)...")
                break
                
    # Sort by variance
    uncertainty_results.sort(key=lambda x: x["variance"], reverse=True)
    
    payload = {
        "run_name": args.run_name,
        "mc_passes": args.passes,
        "results": uncertainty_results
    }
    
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    
    print(f"\nReport saved to {args.output_json}")
    print("\nTop 3 Most Uncertain Scans (High variance implies model is guessing):")
    for r in uncertainty_results[:3]:
        print(f"- {r['sample_id']}: Mean Prob={r['mean_probability']:.4f}, Variance={r['variance']:.4f}")

if __name__ == "__main__":
    main()
