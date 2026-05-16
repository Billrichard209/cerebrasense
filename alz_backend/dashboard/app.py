"""
CerebraSense High-Quality Backend API (FastAPI)
Professional, async-capable API with strict clinical guardrails.
"""

import os
import sys
import shutil
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.inference.pipeline import predict_scan, PredictScanOptions
from src.inference.dashboard_utils import load_dashboard_data
from src.explainability.gradcam import explain_scan, ExplainScanConfig
from src.configs.runtime import get_app_settings

# --- Models ---

class ClinicalInput(BaseModel):
    """Strict validation for multimodal clinical features."""
    age: float = Field(..., ge=0, le=120, description="Patient age in years (0-120)")
    sex: str = Field(..., pattern="^(m|f|male|female)$", description="Patient biological sex (m/f)")
    mmse: float = Field(..., ge=0, le=30, description="MMSE score (0-30)")

# --- API Configuration ---

app = FastAPI(
    title="CerebraSense Clinical API",
    description="Professional Multimodal Alzheimer's Monitoring Platform",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Endpoints ---

@app.get("/api/health")
async def health_check():
    """Verify system status and data availability."""
    settings = get_app_settings()
    data, err = load_dashboard_data(settings.project_root)
    return {
        "status": "optimal",
        "data_source_ok": err is None,
        "active_subjects": data["summary"]["total_subjects"] if data else 0
    }

@app.get("/api/data")
async def get_dashboard_data():
    """Retrieve longitudinal subject trends and summaries."""
    settings = get_app_settings()
    data, err = load_dashboard_data(settings.project_root)
    if err:
        raise HTTPException(status_code=500, detail=err)
    return data

@app.post("/api/predict")
async def analyze_mri(
    file: UploadFile = File(...),
    age: float = Form(...),
    sex: str = Form(...),
    mmse: float = Form(...),
):
    """
    Multimodal Inference Endpoint.
    Strictly validates clinical inputs and runs 3D MRI analysis + Grad-CAM.
    """
    # 1. Validation Guardrails (via Pydantic)
    try:
        clinical = ClinicalInput(age=age, sex=sex, mmse=mmse)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Clinical Validation Error: {str(e)}")

    settings = get_app_settings()
    temp_dir = settings.outputs_root / "temp" / "uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    temp_path = temp_dir / file.filename
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 2. Run High-Quality Inference
        # In a real setup, we'd resolve the best checkpoint from the registry
        checkpoint_path = settings.outputs_root / "runs/oasis2/oasis2_colab_improved_v1/checkpoints/best_model.pt"
        if not checkpoint_path.exists():
             # Fallback to current baseline if specific run not found
             checkpoint_path = settings.outputs_root / "model_registry/best_model.pt"

        options = PredictScanOptions(
            age=clinical.age,
            sex=clinical.sex,
            mmse=clinical.mmse,
            save_debug_slices=True
        )
        
        result = predict_scan(
            scan_path=str(temp_path),
            checkpoint_path=str(checkpoint_path),
            options=options,
            settings=settings
        )

        # 3. Generate Grad-CAM (XAI)
        explain_cfg = ExplainScanConfig(
            scan_path=temp_path,
            checkpoint_path=checkpoint_path,
            age=clinical.age,
            sex=clinical.sex,
            mmse=clinical.mmse,
            output_name=f"api_{file.filename}"
        )
        explanation = explain_scan(explain_cfg, settings=settings)
        
        # Convert first overlay to base64 for immediate dashboard preview
        gradcam_base64 = None
        if explanation.overlay_paths:
            with open(explanation.overlay_paths[0], "rb") as img_f:
                gradcam_base64 = base64.b64encode(img_f.read()).decode("utf-8")

        result["gradcam_base64"] = gradcam_base64
        result["explanation_report"] = explanation.payload
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference Engine Failure: {str(e)}")
    finally:
        # Cleanup
        if temp_path.exists():
            os.remove(temp_path)

@app.get("/logo.svg")
async def get_logo():
    """Serve the platform branding."""
    logo_path = Path(__file__).parent / "logo.svg"
    if logo_path.exists():
        return FileResponse(logo_path, media_type="image/svg+xml")
    raise HTTPException(status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
