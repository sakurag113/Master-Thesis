# Project Summary

## Project Title

**eBPF-driven Fine-grained Telemetry and Machine Learning for EVPN/VXLAN Datacenter Networks**

---

## 1. Project Overview

This project investigates whether network telemetry can provide early indicators of congestion-related latency spikes in a software-based datacenter network testbed.

The project focuses on three main questions:

1. Whether congestion and queue-related signals can be associated with future latency spikes.
2. Whether machine-learning models can predict high-latency events before they occur.
3. Whether prediction-driven mitigation can reduce latency degradation.

The experimental work is divided into three phases:

```text
Phase 1
Environment and Data Collection
        ↓
Phase 2
Feature Analysis and Prediction
        ↓
Phase 3
Online Prediction and Mitigation
```

---

## 2. Phase 1 – Environment and Data Collection

Phase 1 establishes the experimental environment and verifies that controlled traffic can produce measurable queue activity and latency degradation.

The testbed uses Linux network namespaces, FRR, EVPN/VXLAN-related network configuration, Linux Traffic Control, iperf3, and end-to-end RTT measurements.

Experiments include:

- Baseline traffic
- Single-flow traffic
- Multiple-flow traffic
- Controlled bottleneck conditions
- RTT measurements
- Queue-related signal collection
- Repeated experiment runs

The Phase 1 results confirm that congestion-related latency increases can be reproduced consistently and that queue activity is associated with high-latency periods.

---

## 3. Phase 2 – Feature Analysis and Prediction

Phase 2 extends the Phase 1 experiments into a larger and more systematic dataset.

Traffic conditions and bottleneck configurations are automatically varied across repeated experiment runs.

Sliding observation and prediction windows are used to construct a labelled prediction dataset.

The main features include:

- Traffic load information
- Bottleneck configuration
- RTT statistics
- Queue-related statistics

Several prediction approaches are evaluated, including:

- Persistence baseline
- Logistic Regression
- Random Forest

Evaluation is performed using run-grouped cross-validation to avoid mixing correlated windows from the same experiment between training and test sets.

The final dataset contains:

- 60 experiment runs
- 4,543 prediction samples
- 381 NORMAL-to-HIGH transition samples

The results show that machine-learning models provide useful predictive information beyond a simple persistence baseline.

For early-warning prediction, the Queue-and-Traffic Random Forest achieved approximately:

- F1-score: 0.483
- ROC-AUC: 0.792
- PR-AUC: 0.556

The selected Random Forest model is exported for online use in Phase 3.

---

## 4. Phase 3 – Online Prediction and Mitigation

Phase 3 integrates the selected prediction model into an online experimental pipeline.

The online system performs:

```text
Live Traffic
     ↓
Telemetry Collection
     ↓
Feature Window
     ↓
Prediction Model
     ↓
Risk Warning
     ↓
Mitigation Controller
```

The mitigation controller dynamically changes the bottleneck configuration when a high-risk condition is detected.

A refined controller also prevents mitigation from being triggered when there are no active traffic flows.

---

## 5. Online Validation

The online prediction system was first evaluated independently before mitigation was enabled.

The validation experiment demonstrated that the offline-trained prediction model could operate on live telemetry.

The early-warning evaluation produced an F1-score of approximately 0.462 in the proof-of-concept online run.

Because the number of positive transition events in this individual run was small, the result is treated as an online feasibility validation rather than a statistically strong standalone conclusion.

---

## 6. Formal Mitigation Evaluation

The final mitigation experiment uses repeated A/B testing:

```text
5 runs – Mitigation OFF
5 runs – Mitigation ON
```

The same traffic pattern is used for both experimental conditions.

Across the repeated runs:

- Mean RTT was reduced by approximately **15%**
- High-latency sample ratio was reduced by approximately **48.6%**

The improvement in mean RTT and high-latency exposure was relatively consistent across paired runs.

However, P99 and maximum RTT showed larger variability and were not consistently improved.

The results therefore suggest that the current controller is more effective at reducing sustained high-latency exposure than eliminating rare extreme latency events.

---

## 7. Main Findings

The main findings of the project so far are:

1. Controlled congestion can reproducibly generate high-latency events in the software-based testbed.

2. Queue and traffic-related measurements contain useful information for predicting future latency conditions.

3. Machine-learning prediction performs better than simply assuming that the current latency state will continue.

4. Early-warning prediction is possible, although it remains more difficult than general high-latency prediction.

5. An offline-trained model can be integrated into an online prediction pipeline.

6. Prediction-driven mitigation can significantly reduce average latency and high-latency exposure.

7. Extreme tail-latency events remain more variable and are not consistently eliminated by the current mitigation strategy.

---

## 8. Current Limitations

The current implementation is a controlled software-based research prototype.

Several limitations remain:

- The telemetry pipeline currently relies mainly on Linux traffic-control and network statistics rather than a complete eBPF-based telemetry implementation.
- Additional verification of the EVPN/VXLAN forwarding path is planned.
- CPU overhead has not yet been fully evaluated.
- Some additional metrics, such as spike duration, packet loss, and P999 latency, may be added.
- The testbed is small compared with a production datacenter network.
- The prediction and mitigation approaches are intentionally lightweight.

---

## 9. Future Work

The remaining work focuses on extending and validating the current system rather than rebuilding the completed Phase 1–3 experiments.

Planned work includes:

1. Verify that the experimental traffic follows the intended EVPN/VXLAN forwarding path.
2. Add an eBPF-based telemetry proof of concept.
3. Compare eBPF telemetry with the existing congestion and latency signals.
4. Measure CPU overhead introduced by telemetry, prediction, and mitigation.
5. Add selected evaluation metrics such as latency-spike frequency and duration.
6. Perform limited robustness testing under additional traffic and bottleneck conditions.
7. Integrate the final results into the thesis documentation.

---

## 10. Repository Organisation

The repository is organised as:

```text
Master-Thesis/
├── README.md
├── PROJECT_SUMMARY.md
├── phase1/
├── phase2/
└── phase3/
```

Each phase contains its own README describing the corresponding experiments, scripts, datasets, and outputs.