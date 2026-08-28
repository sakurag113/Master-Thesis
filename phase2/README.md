# Phase 2 – Feature Analysis and Prediction

## Purpose

Phase 2 investigates whether traffic and queue-related measurements can be used to predict future high-latency events.

The Phase 1 experimental workflow is extended with automated traffic generation, larger-scale repeated experiments, feature extraction, labelling, and machine-learning evaluation.

---

## Experimental Workflow

```text
Automated Experiments
        ↓
Raw Telemetry
        ↓
Sliding Windows
        ↓
Feature Extraction
        ↓
Future Latency Labels
        ↓
Model Training
        ↓
Cross-validation
        ↓
Prediction Evaluation
```

---

## Dataset Construction

The final Phase 2 dataset combines pilot and formal experiment runs.

It contains:

- 60 experiment runs
- 4,543 prediction samples
- 1,761 future HIGH samples
- 2,782 future NORMAL samples
- 381 NORMAL-to-HIGH transition samples

The NORMAL-to-HIGH transitions are particularly important for evaluating early-warning prediction.

---

## Prediction Task

Each prediction sample uses a recent observation window to estimate whether the following time window will contain a high-latency event.

Features are derived from:

- Bottleneck configuration
- Requested traffic flows
- Active traffic flows
- RTT statistics
- Queue-related statistics

The prediction models include:

- Persistence baseline
- Logistic Regression
- Random Forest

---

## Evaluation Method

Because multiple sliding windows are generated from the same experiment run, samples within one run are correlated.

Therefore, model evaluation uses run-grouped cross-validation instead of randomly splitting individual rows.

This prevents windows from the same experiment appearing in both training and test data.

Two main prediction scenarios are evaluated:

### General Prediction

Predict whether the future window will be in a HIGH-latency state.

### Early-warning Prediction

Evaluate only samples where the current state is NORMAL and determine whether a transition to HIGH will occur in the future window.

---

## Feature Evaluation

Multiple feature groups are compared, including:

- Full feature set
- Features without the current high-latency ratio
- Queue-and-Traffic features

The feature-ablation experiments show that useful predictive information remains even when direct current-state information is removed.

---

## Main Results

For early-warning prediction, the Queue-and-Traffic Random Forest achieved approximately:

- F1-score: 0.483
- ROC-AUC: 0.792
- PR-AUC: 0.556

The persistence baseline cannot provide meaningful NORMAL-to-HIGH early warnings because it simply assumes that the current state will continue.

The results support the feasibility of using traffic and queue-related information to predict future latency degradation.

---

## Directory Structure

```text
phase2/
├── data/
├── plots/
└── scripts/
```

### `data/`

Contains pilot datasets, formal experiment datasets, processed prediction datasets, and evaluation results.

### `plots/`

Contains model-comparison, early-warning, feature-ablation, and dataset-analysis figures.

### `scripts/`

Contains automated experiment runners, dataset-processing scripts, model-training scripts, cross-validation scripts, and result-analysis scripts.

---

## Model Export

Phase 2 performs model training, comparison, and evaluation.

The selected Queue-and-Traffic Random Forest model used for online experiments is exported and stored under:

```text
phase3/models/
```

This keeps the model artifact together with the online prediction and mitigation implementation that uses it.

---

## Relationship to Phase 3

Phase 3 takes the selected prediction model from Phase 2 and integrates it into a live prediction pipeline.

The model is then used to trigger an online mitigation controller and evaluate whether prediction-driven intervention improves network latency.