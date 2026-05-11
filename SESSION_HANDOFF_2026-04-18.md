# Session Handoff

Date: `2026-04-18`

## Current State

- Local OASIS inference is working through the active registry-backed model.
- A real local prediction was run successfully on:
  - `alz_backend/outputs/exports/oasis1_upload_bundle/OASIS/disc2/OAS1_0044_MR1/PROCESSED/MPRAGE/T88_111/OAS1_0044_MR1_mpr_n4_anon_111_t88_masked_gfc.hdr`
- Prediction output was written to:
  - `alz_backend/outputs/predictions/scan_prediction/prediction.json`
- Combined evidence report was regenerated:
  - `alz_backend/outputs/reports/evidence/scope_aligned_evidence_report.json`
  - `alz_backend/outputs/reports/evidence/scope_aligned_evidence_report.md`

## Most Important Results

- Active local OASIS baseline:
  - `oasis_baseline_rtx2050_gpu_seed42_split42`
- OASIS test metrics from active registry:
  - `accuracy = 0.8611111111111112`
  - `auroc = 0.8793650793650795`
  - `recommended_threshold = 0.45`
- Kaggle comparison run from evidence report:
  - `kaggle_baseline_rtx2050_scope`
  - `test_macro_ovr_auroc = 0.9888276291609625`

## Important Findings

- The local backend is usable right now with the existing active registry.
- Google Drive currently exposes exported `oasis_colab_full_v1`, not the later `oasis_colab_full_v3_auroc_monitor`.
- If cloud and local baselines need to match, rerun the hardened Colab OASIS notebook and export/promote the chosen `v3` run.

## Useful Commands For Next Time

Regenerate the evidence report:

```powershell
.\build_scope_evidence_report.cmd
```

Run a local OASIS prediction:

```powershell
.\predict_scan.cmd `
  --scan-path "C:\path\to\scan.hdr" `
  --device cpu `
  --use-registry-threshold
```

Import a promoted Colab OASIS run after Drive sync:

```powershell
.\import_promoted_oasis_run.cmd `
  --source-run-root "C:\path\to\Drive\...\training_runs\oasis\<run_name>" `
  --source-registry-path "C:\path\to\Drive\...\model_registry\oasis_current_baseline.json" `
  --overwrite
```

## Best Next Step

The best next engineering move is:

1. Rerun the hardened Colab OASIS notebook only if you want Drive to reflect the chosen `v3` baseline.
2. Otherwise, keep using the current local baseline for more inference/demo checks.
3. After that, only do more training if you are specifically moving into repeated-split OASIS validation or external 3D validation.
