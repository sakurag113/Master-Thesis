# Project Summary

## Project Title

**Telemetry-driven Latency Prediction and Mitigation in EVPN/VXLAN Datacenter Networks**

---

## 1. Project Overview

This project investigates whether network telemetry can provide early indicators of congestion-related latency degradation in a software-based EVPN/VXLAN datacenter-network testbed.

The project focuses on three main questions:

1. Whether traffic and queue-related signals contain information about future latency degradation.
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

The testbed uses Linux network namespaces, FRR, BGP EVPN, VXLAN, Linux Traffic Control, iperf3, and end-to-end RTT measurements.

The Phase 1 results confirm that congestion-related latency increases can be reproduced and that queue activity is associated with high-latency periods.

---

## 3. Phase 2 – Feature Analysis and Prediction

Phase 2 extends the Phase 1 experiments into a larger and more systematic prediction dataset.

Evaluation uses 5-fold run-grouped cross-validation so that windows from the same experiment run do not appear in both training and test subsets.

The final dataset contains:

- 60 independent experiment runs
- 4,543 prediction windows
- 1,761 future HIGH samples
- 2,782 future NORMAL samples
- 2,623 early-warning samples
- 381 NORMAL-to-HIGH transition samples

The early-warning positive prevalence is `381 / 2623 ≈ 14.53%`.

---

## 4. Feature Ablation and Final Model Selection

Three feature configurations are compared:

1. All Features
2. No Current High Ratio
3. Queue + Traffic Only

The Queue + Traffic feature set contains:

- `bottleneck_mbit`
- `requested_flows_mean`
- `active_flows_mean`
- `mean_overlimits_rate`
- `max_overlimits_rate`
- `std_overlimits_rate`
- `overlimits_rate_slope`

| Feature Set | F1 | ROC-AUC | PR-AUC |
|---|---:|---:|---:|
| All Features | 0.473 | 0.793 | 0.561 |
| No Current High Ratio | 0.480 | 0.796 | 0.564 |
| Queue + Traffic Only | 0.483 | 0.792 | 0.556 |

The Queue + Traffic Random Forest is selected for online deployment because it retains comparable predictive performance while avoiding direct RTT-derived state information.

---

## 5. Early-warning Metrics Interpretation

For the selected Queue + Traffic Random Forest, the 5-fold early-warning results are approximately:

- F1: `0.483 ± 0.067`
- ROC-AUC: `0.792 ± 0.041`
- PR-AUC: `0.556 ± 0.060`

Pooled out-of-fold predictions produce:

| Metric | Value |
|---|---:|
| Accuracy | 0.884 |
| Precision | 0.692 |
| Recall | 0.365 |
| F1 | 0.478 |
| ROC-AUC | 0.787 |
| PR-AUC | 0.547 |

The pooled confusion matrix is:

| | Predicted NORMAL | Predicted HIGH |
|---|---:|---:|
| Actual NORMAL | 2180 | 62 |
| Actual HIGH | 242 | 139 |

The selected model favours precision over recall at the current operating threshold.

---

## 6. Phase 3 – Online Prediction and Mitigation

Phase 3 integrates the selected Queue + Traffic Random Forest into an online experimental pipeline.

The mitigation controller temporarily increases the bottleneck capacity when a high-risk condition is detected.

A refined controller also requires active traffic to be present before mitigation is triggered.

---

## 7. Formal Mitigation Evaluation

The final mitigation experiment uses repeated A/B testing:

```text
5 runs – Mitigation OFF
5 runs – Mitigation ON
```

Across the repeated runs:

- Mean RTT was reduced by approximately 15%
- High-latency sample ratio was reduced by approximately 48.6%

P99 and maximum RTT remain more variable.

---

## 8. Single-flow and Dual-flow Validation

| Condition | Mean Risk | Mean Overlimits Rate |
|---|---:|---:|
| Single flow | 0.791 | 112.9 events/s |
| Dual flow | 0.828 | 177.2 events/s |

The dual-flow condition produces substantially stronger queue pressure and moderately higher predicted risk.

---

## 9. Risk Recovery after Traffic Termination

Across the analysed traffic-stop transitions:

- Mean time to fall below the warning threshold (`0.5`): approximately `1.73 s`
- Mean time to return to the low-risk baseline: approximately `2.36 s`

This behaviour is consistent with the 2-second observation-window design.

---

## 10. Packet-scale Validation

Across six measured runs:

- Mean bottleneck packets per run: approximately `2,885`
- Mean spine packet rate: approximately `44.55 packets/s`
- Mean spine throughput: approximately `4.17 Mbit/s`
- Mean delivery ratio: approximately `0.984`

Packet measurements provide experiment-scale context but are not treated as machine-learning samples.

---

## 11. EVPN/VXLAN Overlay Verification

The experimental forwarding path was explicitly verified at both the control and data planes.

Confirmed configuration:

- VXLAN interface: `vxlan100`
- VNI: `100`
- UDP destination port: `4789`
- leaf1 VTEP: `1.1.1.1`
- leaf2 VTEP: `2.2.2.2`

Control plane:

- BGP EVPN sessions established
- EVPN Type-2 routes present
- EVPN Type-3 IMET routes present

Data plane:

- VXLAN encapsulation observed on the spine
- Inner traffic between `192.168.100.11` and `192.168.100.22`

This verifies that the host-to-host experiment traffic traverses the intended EVPN/VXLAN overlay.

---

## 12. Main Findings

1. Controlled congestion can reproducibly generate measurable high-latency periods.
2. Queue and traffic-related measurements contain useful information for predicting future latency conditions.
3. Removing direct current-latency information causes negligible degradation in early-warning performance.
4. The Queue + Traffic Random Forest provides meaningful early-warning capability under class imbalance.
5. The current operating point favours precision over recall.
6. An offline-trained model can be integrated into an online prediction pipeline.
7. Prediction-driven mitigation reduces average latency and high-latency exposure.
8. Dual-flow traffic creates stronger queue pressure than single-flow traffic in the evaluated online experiment.
9. Post-traffic risk persistence is consistent with the 2-second observation window.
10. The experimental data path has been verified as an operational BGP EVPN/VXLAN overlay.

---

## 13. Current Limitations

- Controlled software-based prototype
- Small testbed compared with a production datacenter
- Controlled traffic patterns
- No complete eBPF telemetry implementation yet
- CPU overhead not yet fully evaluated
- Relatively low recall at the current operating point
- Extreme tail-latency behaviour remains variable

---

## 14. Future Work

1. Add an eBPF-based telemetry proof of concept.
2. Compare eBPF telemetry with the existing traffic and queue signals.
3. Measure CPU overhead introduced by telemetry, prediction, and mitigation.
4. Add selected latency-spike frequency and duration metrics.
5. Add packet-loss evaluation.
6. Investigate alternative warning thresholds.
7. Perform limited robustness testing under additional traffic and bottleneck conditions.
8. Integrate the final experimental results into the thesis document.

---

## 15. Repository Organisation

```text
Master-Thesis/
├── README.md
├── PROJECT_SUMMARY.md
├── phase1/
├── phase2/
└── phase3/
```
