# Phase 3 – Online Prediction and Mitigation

## Purpose

Phase 3 integrates the prediction model selected in Phase 2 into an online network-control pipeline.

The main objective is to determine whether predicted latency risk can be used to trigger mitigation and improve network performance.

---

## Online Workflow

```text
Traffic Generation
       ↓
Live Telemetry
       ↓
Feature Window
       ↓
Random Forest Prediction
       ↓
Latency-risk Warning
       ↓
Mitigation Controller
       ↓
Performance Evaluation
```

---

## Online Prediction

The selected Queue-and-Traffic Random Forest model is loaded by the online prediction system.

The model continuously processes live traffic and queue-related measurements and estimates the risk of a future high-latency event.

The online implementation validates that the model trained using Phase 2 datasets can operate on live experimental data.

---

## Traffic Generation

The online traffic generator produces repeated periods of:

- No traffic
- Moderate traffic
- Heavy traffic
- Recovery

Parallel iperf3 streams are used so that multiple traffic flows can be generated reliably during each traffic period.

---

## Mitigation Controller

When the predicted risk exceeds the configured warning threshold, the mitigation controller temporarily increases the available bottleneck capacity.

After the mitigation period, the original bottleneck configuration is restored.

A refined controller also checks whether active traffic flows are present before triggering mitigation.

This prevents outdated prediction windows from causing unnecessary mitigation during zero-traffic recovery periods.

---

## Online Validation

Before the formal mitigation experiment, the online prediction system was evaluated independently.

The proof-of-concept online validation produced an early-warning F1-score of approximately:

```text
0.462
```

The number of positive transition samples in this individual run was small, so this result is mainly used to demonstrate online feasibility.

---

## Formal A/B Evaluation

The final evaluation compares:

```text
Mitigation OFF
      vs
Mitigation ON
```

Five repeated runs are performed for each condition using the same traffic pattern.

The main evaluation metrics include:

- Mean RTT
- Median RTT
- P95 RTT
- P99 RTT
- Maximum RTT
- High-latency sample ratio
- Mitigation trigger count
- Mitigation active ratio

---

## Main Results

Across the five repeated OFF/ON experiments:

### Mean RTT

```text
OFF ≈ 90.8 ms
ON  ≈ 77.2 ms
```

This corresponds to an average reduction of approximately:

```text
15%
```

### High-latency Ratio

```text
OFF ≈ 0.906
ON  ≈ 0.466
```

This corresponds to a reduction of approximately:

```text
48.6%
```

The reduction in mean RTT and high-latency exposure is relatively consistent across the repeated experiments.

However, P99 and maximum RTT show considerably larger variability and are not consistently improved.

The current mitigation controller therefore appears more effective at reducing sustained high-latency exposure than eliminating rare extreme latency events.

---

## Directory Structure

```text
phase3/
├── data/
├── logs/
├── models/
├── plots/
└── scripts/
```

### `data/`

Contains online validation results, formal A/B comparison results, and summary statistics.

### `logs/`

Contains raw online prediction and mitigation experiment logs.

### `models/`

Contains the prediction model and corresponding online feature definition.

Current model artifacts include:

```text
online_rf_queue_traffic.joblib
online_feature_list.txt
```

### `plots/`

Contains final Phase 3 evaluation figures, including:

- Mean RTT comparison
- High-latency ratio comparison
- Paired mitigation reduction
- Tail-latency comparison

### `scripts/`

Contains:

- Online traffic generation
- Online prediction
- Prediction validation
- Mitigation controller
- Formal A/B experiment automation
- Final result analysis
- Plot generation

---

## Current Conclusion

Phase 3 demonstrates that an offline-trained prediction model can be incorporated into an online mitigation controller.

Repeated A/B experiments indicate that prediction-driven mitigation can reduce average latency and substantially reduce the amount of time the network spends in a high-latency state.

At the same time, extreme tail-latency behaviour remains more variable, indicating that further controller refinement would be required to consistently suppress rare extreme latency events.

---

## Future Extensions

Future work includes:

- EVPN/VXLAN forwarding-path verification
- eBPF-based telemetry integration and validation
- CPU overhead evaluation
- Additional latency-spike metrics
- Packet-loss evaluation
- Limited robustness testing under additional traffic conditions

These extensions are intended to strengthen the current experimental system rather than replace the completed Phase 1–3 workflow.