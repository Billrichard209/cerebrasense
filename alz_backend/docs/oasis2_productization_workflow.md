# OASIS-2 Productization Workflow

Canonical path for training, evaluating, importing, and demoing OASIS-2 runs.

## Cloud source of truth

```text
Cerebrasensecloud/backend_runtime/
  outputs/runs/oasis2/<run_name>/
  outputs/model_registry/oasis2_current_baseline.json
```

## Train (Colab or local GPU)

```powershell
cd archive (1)
.\train_oasis2_improved.cmd --run-name oasis2_mri_baseline_v2 --device auto
```

Cohort ablations:

```powershell
.\train_oasis2_stable_only.cmd --run-name oasis2_stable_only_v2 --device auto
.\train_oasis2_visit_filter.cmd --run-name oasis2_visit_filter_v2 --device auto
```

## Post-train suite

```powershell
.\run_oasis2_eval_suite.cmd --run-name oasis2_mri_baseline_v2 --device cuda
```

This runs: evaluate + calibrate, paradox audit, ONNX export (via post_train_pipeline), mixed-label error analysis, leaderboard refresh.

## Import from Drive

```powershell
.\import_promoted_oasis2_run.cmd --source-runtime-root "C:\path\to\Cerebrasensecloud\backend_runtime" --overwrite
```

## Alignment check

```powershell
.\check_oasis2_productization.cmd --expected-run-name oasis2_mri_baseline_v2
```

## Promote (gates: test AUROC >= 0.80, specificity >= 0.70, zero paradoxes)

```powershell
.\promote_oasis2_run.cmd --run-name oasis2_mri_baseline_v2
```

## Demo bundle

```powershell
.\build_oasis2_demo_bundle.cmd --run-name oasis2_mri_baseline_v2
```

## API + UI

```powershell
cd alz_backend
.\.venv\Scripts\python.exe -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

- Dashboard: http://127.0.0.1:8000/dashboard/
- Frontend demo: http://127.0.0.1:8000/demo/
- API docs: http://127.0.0.1:8000/docs

## Multi-seed validation

```powershell
.\run_oasis2_multiseed_eval.cmd --base-run-name oasis2_mri_baseline_v2 --device auto --dry-run-train
```

Use without `--dry-run-train` only when you intend to launch three full training jobs.
