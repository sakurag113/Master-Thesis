# Master Thesis Project

## Telemetry-driven Latency Prediction and Mitigation in EVPN/VXLAN Datacenter Networks

This repository contains the experimental implementation, datasets, analysis scripts, models, and results developed for my Master's thesis project.

The project investigates whether network telemetry can provide early indicators of congestion-related latency spikes, whether machine-learning models can predict such events in advance, and whether prediction-driven mitigation can improve latency performance in a controlled EVPN/VXLAN datacenter-network testbed.

The experimental work is organised into three phases.

---

## Project Overview

Transient traffic bursts can create temporary queue buildup and substantial latency degradation in datacenter networks.

The project follows the general workflow:

```text
Network Traffic
      ↓
Telemetry Collection
      ↓
Latency / Queue Analysis
      ↓
Feature Extraction
      ↓
Latency-risk Prediction
      ↓
Online Prediction
      ↓
Prediction-driven Mitigation
      ↓
Performance Evaluation
```

The current implementation uses a software-based network testbed built with:

- Linux network namespaces
- FRR
- BGP EVPN
- VXLAN
- Linux Traffic Control (`tc`)
- iperf3
- Python
- Scikit-learn

The objective is to study a lightweight telemetry-driven latency early-warning and mitigation pipeline rather than to build a production-ready datacenter networking platform.

---

## Repository Structure

```text
Master-Thesis/
├── README.md
├── PROJECT_SUMMARY.md
├── phase1/
├── phase2/
└── phase3/
```

---

# Phase 1 – Environment and Data Collection

Phase 1 focuses on building the experimental network environment and verifying that congestion-related latency spikes can be reproduced and measured.

The main work includes:

- Building the software-based network testbed
- Configuring the EVPN/VXLAN environment
- Generating controlled network traffic
- Creating bottleneck conditions using Linux Traffic Control
- Measuring end-to-end RTT
- Collecting queue-related signals
- Comparing baseline, single-flow, and multi-flow traffic conditions
- Verifying the relationship between queue activity and high-latency periods

The results from this phase establish the experimental and data-collection pipeline used in the later phases.

---

# Phase 2 – Feature Analysis and Prediction

Phase 2 focuses on constructing a larger labelled dataset and investigating whether traffic, bottleneck, queue, and latency-related features can be used to predict future high-latency events.

The main work includes:

- Automated repeated experiment execution
- Dataset construction and validation
- Sliding-window feature extraction
- Future latency-state labelling
- Feature analysis
- Training and evaluation of prediction models
- Early-warning prediction
- Feature-ablation experiments
- Run-grouped cross-validation
- Out-of-fold prediction analysis
- ROC, Precision-Recall, and confusion-matrix evaluation

The final Phase 2 dataset contains:

- 60 independent experiment runs
- 4,543 prediction windows
- 2,623 early-warning samples
- 381 NORMAL-to-HIGH transitions
- 14.53% positive prevalence in the early-warning subset

The evaluated models include:

- Persistence baseline
- Logistic Regression
- Random Forest

The final selected online model is a Queue + Traffic Random Forest using seven traffic, bottleneck, and queue-dynamics features.

Using 5-fold run-grouped cross-validation, the selected model achieved approximately:

- F1: `0.483 ± 0.067`
- ROC-AUC: `0.792 ± 0.041`
- PR-AUC: `0.556 ± 0.060`

Using pooled out-of-fold predictions, the selected model achieved approximately:

- Accuracy: `0.884`
- Precision: `0.692`
- Recall: `0.365`
- F1: `0.478`
- ROC-AUC: `0.787`
- PR-AUC: `0.547`

The positive-class prevalence baseline for the early-warning subset is approximately `0.145`, so the pooled PR-AUC is substantially above the random baseline.

---

# Phase 3 – Online Prediction and Mitigation

Phase 3 integrates the selected prediction model into an online prediction and mitigation pipeline.

The main work includes:

- Online traffic generation
- Real-time telemetry processing
- Online latency-risk prediction
- Prediction-driven mitigation
- Mitigation-controller refinement
- Repeated mitigation OFF/ON experiments
- Single-flow and dual-flow validation
- Queue-pressure analysis
- Risk-recovery analysis
- Packet-scale validation
- EVPN/VXLAN control-plane verification
- VXLAN data-plane verification

The online model uses:

```text
2 s observation window
        ↓
Queue + Traffic feature extraction
        ↓
Random Forest prediction
        ↓
Future HIGH-latency probability
        ↓
Warning / mitigation decision
```

### Formal Mitigation Evaluation

Across five repeated runs for each condition:

- Mean RTT was reduced by approximately 15%
- High-latency sample ratio was reduced by approximately 48.6%

P99 and maximum RTT remain more variable and are not consistently improved.

### Single-flow and Dual-flow Validation

| Condition | Mean Risk | Mean Overlimits Rate |
|---|---:|---:|
| Single flow | 0.791 | 112.9 events/s |
| Dual flow | 0.828 | 177.2 events/s |

The dual-flow condition generated substantially stronger queue pressure and moderately higher predicted risk.

### Risk Recovery

After traffic termination:

- Mean time for predicted risk to fall below the warning threshold (`0.5`): approximately `1.73 s`
- Mean time to return to the low-risk baseline: approximately `2.36 s`

### Packet-scale Validation

Across six measured Phase 3 runs:

- Mean bottleneck packets per run: approximately `2,885`
- Mean spine packet rate: approximately `44.55 packets/s`
- Mean spine throughput: approximately `4.17 Mbit/s`
- Mean delivery ratio: approximately `0.984`

### EVPN/VXLAN Verification

Control-plane verification confirmed:

- Established BGP EVPN sessions
- EVPN Type-2 MAC advertisement routes
- EVPN Type-3 IMET routes

Data-plane verification confirmed:

- VXLAN interface `vxlan100`
- VNI `100`
- UDP destination port `4789`
- leaf1 VTEP: `1.1.1.1`
- leaf2 VTEP: `2.2.2.2`
- Encapsulated traffic between `192.168.100.11` and `192.168.100.22`

Packet capture on the spine showed the original host-to-host traffic encapsulated inside VXLAN packets, confirming that experimental traffic traverses the intended EVPN/VXLAN overlay.

---

# Main Findings

1. Controlled congestion can reproducibly generate measurable queue activity and high-latency periods.
2. Traffic and queue-related features contain predictive information about future latency degradation.
3. Removing direct current-latency information does not substantially reduce early-warning performance.
4. A Queue + Traffic Random Forest can provide meaningful early-warning capability under class imbalance.
5. The selected model favours precision over recall at the current operating threshold.
6. Offline-trained prediction can be deployed in an online telemetry pipeline.
7. Prediction-driven mitigation can reduce mean RTT and high-latency exposure.
8. Dual-flow traffic produces stronger queue pressure than single-flow traffic in the evaluated online scenario.
9. Elevated prediction risk after traffic termination is consistent with the finite sliding observation window.
10. The testbed forwarding path has been verified as an operational BGP EVPN/VXLAN overlay using both control-plane and packet-capture evidence.

---

# Future Work

Potential extensions include:

- eBPF-based telemetry integration and validation
- Comparison between eBPF telemetry and the current queue / traffic signals
- CPU-overhead evaluation for telemetry, prediction, and mitigation
- Additional latency-spike duration and frequency metrics
- Packet-loss evaluation
- Limited robustness testing under additional traffic conditions and bottleneck configurations
- Further controller-threshold optimisation
- Final thesis integration and documentation

---

# Tools and Technologies

- Linux
- Linux Network Namespaces
- FRR
- BGP EVPN
- VXLAN
- Linux Traffic Control (`tc`)
- iperf3
- tcpdump
- Python
- Scikit-learn
- Pandas
- NumPy
- Matplotlib

eBPF-based telemetry remains a future extension of the current telemetry implementation.

---

## Notes

This repository represents an experimental research prototype developed in a controlled software-based environment.

The objective is to investigate the feasibility of telemetry-driven latency prediction and prediction-based mitigation rather than to provide a production-ready datacenter networking system.
