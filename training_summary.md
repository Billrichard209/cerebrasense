# Training Accuracy Summary

## OASIS-2 Leaderboard (auto-generated)

Compare runs on **held-out test AUROC**, not validation F1 alone.

| rank | run_name | val_auroc | val_accuracy | val_f1 | test_auroc | test_accuracy | test_balanced_acc | test_sensitivity | test_specificity | test_f1 | threshold | review_required_count | subject_consensus_auroc | best_val_auroc_training | mixed_group_error_rate | has_test_predictions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | oasis2_multimodal_v1 | 0.6927297668038409 | 0.6851851851851852 | 0.7301587301587301 | 0.7250293772032903 | 0.6333333333333333 | 0.6533490011750881 | 0.7391304347826086 | 0.5675675675675675 | 0.6071428571428571 | 0.47 | 31.0 | 0.6818181818181818 | 0.6934156378600823 |  | True |
| 2 | oasis2_bias_stability_v1 | 0.663923182441701 | 0.6481481481481481 | 0.732394366197183 | 0.6545240893066979 | 0.5166666666666667 | 0.6392479435957696 | 0.5217391304347826 | 0.7567567567567568 | 0.5454545454545454 | 0.7 | 15.0 | 0.6287878787878788 | 0.6310013717421125 |  | True |
| 3 | oasis2_colab_improved_v1 | 0.4595336076817558 | 0.5185185185185185 | 0.07142857142857142 | 0.399529964747356 | 0.6 | 0.42244418331374856 | 0.30434782608695654 | 0.5405405405405406 | 0.2978723404255319 | 0.02 | 6.0 | 0.40151515151515144 |  |  | True |
| 4 | oasis2_local_gpu_smoke |  |  |  |  |  |  |  |  |  |  |  |  |  |  | False |
| 5 | oasis2_path_check |  |  |  |  |  |  |  |  |  |  |  |  | 0.0 |  | False |
| 6 | oasis2_research_baseline |  |  |  |  |  |  |  |  |  |  |  |  |  |  | False |

## OASIS-1 (reference)

- **Model**: DenseNet121 (MONAI)
- **Test Accuracy**: 0.8611
- **Test AUROC**: 0.8794
- **Test F1-Score**: 0.8485

---
*Regenerate with: `python scripts/build_oasis2_leaderboard.py`*
