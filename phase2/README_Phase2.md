# Phase 2 – Feature Analysis and Prediction

## Purpose

Phase 2 investigates whether traffic, bottleneck, queue, and latency-related measurements can be used to predict future high-latency events.

The Phase 1 workflow is extended with automated traffic generation, larger-scale repeated experiments, sliding-window feature extraction, future-state labelling, machine-learning evaluation, run-grouped cross-validation, feature ablation, and out-of-fold prediction analysis.

---

## Dataset Construction

The final Phase 2 dataset contains:

- 60 independent experiment runs
- 4,543 prediction samples
- 1,761 future HIGH samples
- 2,782 future NORMAL samples
- 381 NORMAL-to-HIGH transition samples

The early-warning subset contains only samples where the current state is NORMAL:

- 2,623 early-warning samples
- 381 positive NORMAL-to-HIGH transitions
- Positive prevalence: approximately 14.53%

---

## Prediction Task

Each prediction sample uses a recent observation window to estimate whether the following future window will contain a HIGH-latency condition.

Features include:

- Bottleneck configuration
- Requested traffic-flow statistics
- Active traffic-flow statistics
- RTT statistics
- Queue-overlimit statistics
- Current latency-state indicators

---

## Models

- Persistence baseline
- Logistic Regression
- Random Forest

---

## Evaluation Method

Evaluation uses 5-fold run-grouped cross-validation.

This keeps complete experiment runs together and avoids placing correlated windows from the same run in both training and test subsets.

Two scenarios are evaluated:

### General Prediction

Predict whether the future observation window will be in a HIGH-latency state.

### Early-warning Prediction

Evaluate only samples where the current latency state is NORMAL and determine whether the network transitions to HIGH in the future window.

---

## Feature Sets

### All Features

- `bottleneck_mbit`
- `requested_flows_mean`
- `active_flows_mean`
- `mean_rtt`
- `std_rtt`
- `min_rtt`
- `max_rtt`
- `median_rtt`
- `p95_rtt`
- `rtt_slope`
- `mean_overlimits_rate`
- `max_overlimits_rate`
- `std_overlimits_rate`
- `overlimits_rate_slope`
- `current_high_ratio`

### No Current High Ratio

The full feature set except `current_high_ratio`.

### Queue + Traffic Only

- `bottleneck_mbit`
- `requested_flows_mean`
- `active_flows_mean`
- `mean_overlimits_rate`
- `max_overlimits_rate`
- `std_overlimits_rate`
- `overlimits_rate_slope`

This configuration removes all RTT-derived features and direct current-latency-state information.

---

## Feature Ablation

| Feature Set | F1 | ROC-AUC | PR-AUC |
|---|---:|---:|---:|
| All Features | 0.473 | 0.793 | 0.561 |
| No Current High Ratio | 0.480 | 0.796 | 0.564 |
| Queue + Traffic Only | 0.483 | 0.792 | 0.556 |

The Queue + Traffic Random Forest is selected for online deployment because it provides comparable predictive performance while avoiding direct RTT-derived state information.

---

## Final Early-warning Cross-validation Results

| Metric | Mean ± Standard Deviation |
|---|---:|
| Accuracy | 0.885 ± 0.020 |
| Precision | 0.704 ± 0.108 |
| Recall | 0.369 ± 0.057 |
| F1 | 0.483 ± 0.067 |
| ROC-AUC | 0.792 ± 0.041 |
| PR-AUC | 0.556 ± 0.060 |

---

## Out-of-Fold Metrics Interpretation

Pooled out-of-fold dataset:

- 2,623 samples
- 381 positive samples
- 2,242 negative samples
- Positive prevalence: 14.53%

Pooled metrics:

| Metric | Value |
|---|---:|
| Accuracy | 0.884 |
| Precision | 0.692 |
| Recall | 0.365 |
| F1 | 0.478 |
| ROC-AUC | 0.787 |
| PR-AUC | 0.547 |

Confusion matrix:

| | Predicted NORMAL | Predicted HIGH |
|---|---:|---:|
| Actual NORMAL | 2180 | 62 |
| Actual HIGH | 242 | 139 |

The model therefore generates relatively few false warnings but misses a considerable fraction of future HIGH transitions.

The positive-class prevalence baseline is approximately `0.145`, while pooled PR-AUC is approximately `0.547`.

---

## Interpretation of Evaluation Metrics

### F1

F1 is the harmonic mean of precision and recall and is not equivalent to accuracy.

### ROC-AUC

The pooled ROC-AUC of approximately `0.787` indicates useful discrimination between future HIGH and future NORMAL samples.

### PR-AUC

PR-AUC is especially relevant under class imbalance. The model's `0.547` is substantially above the prevalence baseline of approximately `0.145`.

### Precision / Recall Trade-off

The current operating point favours precision over recall. Lowering the threshold could increase recall at the cost of more false warnings.

---

## Pooled and Fold-based Results

The main comparison tables report 5-fold mean ± standard deviation.

ROC, PR, confusion-matrix, and pooled classification metrics are generated from combined out-of-fold predictions.

---

## Directory Structure

```text
phase2/
├── data/
├── plots/
└── scripts/
```

Important final evaluation files include:

```text
final_prediction_dataset.csv
final_general_cv_results.csv
final_early_warning_cv_results.csv
final_early_warning_oof_predictions.csv
final_model_summary.csv
feature_ablation_paper_table.csv
early_warning_metrics_interpretation.csv
```

Important final figures include:

```text
early_warning_roc_curve.png
early_warning_pr_curve.png
early_warning_confusion_matrix.png
```

---

## Model Export

The final selected model is:

```text
Queue + Traffic Random Forest
```

The exported online model and feature definition are stored under:

```text
phase3/models/
```

with:

```text
online_rf_queue_traffic.joblib
online_feature_list.txt
```

---

## Relationship to Phase 3

Phase 3 integrates the selected model into a live prediction pipeline using online queue telemetry, single-flow and dual-flow experiments, recovery analysis, and mitigation A/B testing.
