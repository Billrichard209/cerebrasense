"""
CerebraSense Model Optimization Engine
Quantization and local inference acceleration (ONNX INT8).
"""

import os
from pathlib import Path
import torch
import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType

def optimize_checkpoint_for_local_inference(
    checkpoint_path: Path,
    output_onnx_path: Path,
    model_config_path: Path | None = None,
    quantize: bool = True
) -> Path:
    """
    Exports a PyTorch checkpoint to ONNX and optionally applies INT8 dynamic quantization.
    Reduces model size and improves CPU inference speed by ~3-4x.
    """
    from src.models.factory import build_model, load_oasis_model_config
    from src.evaluation.oasis_run import load_oasis_checkpoint

    # 1. Load Model
    model_cfg = load_oasis_model_config(model_config_path)
    model = build_model(model_cfg)
    checkpoint = load_oasis_checkpoint(checkpoint_path, device="cpu")
    model.load_state_dict(checkpoint.model_state_dict)
    model.eval()

    # 2. Prepare Dummy Inputs (MRI + Clinical)
    image_size = tuple(model_cfg.image_size) if model_cfg.image_size else (64, 64, 64)
    dummy_mri = torch.randn(1, 1, *image_size)
    dummy_clinical = torch.randn(1, 3)

    # 3. Export to ONNX (FP32)
    temp_fp32_path = output_onnx_path.with_suffix(".fp32.onnx")
    torch.onnx.export(
        model,
        (dummy_mri, dummy_clinical),
        str(temp_fp32_path),
        input_names=["mri", "clinical"],
        output_names=["logits"],
        dynamic_axes={
            "mri": {0: "batch_size"},
            "clinical": {0: "batch_size"},
            "logits": {0: "batch_size"}
        },
        opset_version=14
    )

    if not quantize:
        if temp_fp32_path != output_onnx_path:
            os.rename(temp_fp32_path, output_onnx_path)
        return output_onnx_path

    # 4. Apply INT8 Dynamic Quantization
    quantize_dynamic(
        model_input=str(temp_fp32_path),
        model_output=str(output_onnx_path),
        weight_type=QuantType.QUInt8
    )

    # Cleanup temp FP32
    if temp_fp32_path.exists():
        os.remove(temp_fp32_path)

    return output_onnx_path

if __name__ == "__main__":
    # Example usage script
    from src.configs.runtime import get_app_settings
    settings = get_app_settings()
    
    ckpt = settings.outputs_root / "runs/oasis2/oasis2_colab_improved_v1/checkpoints/best_model.pt"
    out = settings.project_root / "best_model_optimized.onnx"
    
    if ckpt.exists():
        print(f"Optimizing {ckpt.name}...")
        optimize_checkpoint_for_local_inference(ckpt, out)
        print(f"Success! Optimized model saved to: {out}")
    else:
        print(f"Checkpoint not found at {ckpt}")
