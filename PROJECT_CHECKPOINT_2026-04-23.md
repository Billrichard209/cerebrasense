# Project Checkpoint: 2026-04-23

## Current State

- Primary active path: `OASIS-1` local workflow
- Paused path: `OASIS-2` Colab training
- Reason OASIS-2 is paused: Google Drive storage/upload capacity, not a code-path failure

## Stable Working Artifacts

- Local workflow summary:
  - `alz_backend/outputs/reports/workflows/oasis_local_workflow/workflow_summary.md`
- Local presentation summary:
  - `alz_backend/outputs/reports/presentation/oasis_local_path_summary.md`
- Review pack:
  - `alz_backend/outputs/reports/review/oasis_review_pack/`
- Reviewer decision log:
  - `alz_backend/outputs/reports/review/oasis_review_decision_log/`
- Reviewer learning report:
  - `alz_backend/outputs/reports/reviewer_learning/oasis_reviewer_learning_report/`
- Specialist handoff pack:
  - `alz_backend/outputs/reports/review/oasis_specialist_handoff_pack/`
- Hard-case benchmark:
  - `alz_backend/outputs/reports/benchmark/oasis_hard_case_benchmark/`

## Active OASIS-1 Baseline

- Run name: `oasis_baseline_rtx2050_gpu_seed42_split42`
- Test accuracy: `0.8611`
- Test AUROC: `0.8794`
- Test F1: `0.8485`

Interpretation:
- The model is solid for a research prototype.
- The main operational weakness is uncertainty/review burden, not collapse in raw performance.

## Flagged-Case Policy

- `8` low-confidence OASIS cases were isolated.
- They are now treated as:
  - `triaged`
  - `escalated`
  - uncertainty benchmark only
- They are **not** confirmed labels.
- They should **not** be used for retraining or threshold-learning unless qualified review becomes available later.

## Recommended Commands

- Build the local OASIS workflow:
  - `.\build_oasis_local_workflow.cmd --scan-root "<path>" --device cpu`
- Open key local outputs:
  - `.\open_oasis_local_outputs.cmd`
- Open the specialist handoff pack:
  - `.\build_oasis_specialist_handoff_open.cmd`
- Refresh the hard-case benchmark:
  - `.\build_oasis_hard_case_benchmark.cmd`

## Best Pre-OASIS-2 Prep

Do **not** spend time on a major architecture refactor right now.

Best option:
1. Keep the current MONAI/PyTorch OASIS-1 path unchanged.
2. Preserve the hard-case benchmark as the uncertainty stress test.
3. Wait until storage is available.
4. Resume the `OASIS-2` lane with the existing hardened notebook/script flow.

Only worthwhile polish before OASIS-2 restart:
- make sure the full Drive bundle can upload cleanly
- keep the current docs/checkpoint summaries current
- avoid new OASIS-1 hyperparameter churn unless it answers a specific question

## Resume Plan When Storage Is Available

1. Free/buy Drive storage.
2. Re-upload or repair the full `OASIS-2` Drive bundle.
3. Reopen `oasis2_train.ipynb`.
4. Run the hardened OASIS-2 flow again.
5. Continue only after the bundle integrity check passes.

## Bottom Line

The project is in a good pause state.

- `OASIS-1` is stable and usable locally.
- `OASIS-2` is blocked by storage, not by core engineering.
- The best next major move is to restart `OASIS-2` when storage is available, not to rework architecture now.
