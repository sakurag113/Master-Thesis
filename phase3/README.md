# Phase 3 – Online Prediction and Mitigation

## Purpose

Phase 3 integrates the prediction model selected in Phase 2 into an online network-control pipeline.

The main objectives are to determine whether:

1. The offline-trained model can operate on live telemetry.
2. Predicted latency risk can identify emerging congestion conditions.
3. Prediction-driven mitigation can improve latency behaviour.
4. The online model responds meaningfully to different traffic loads.
5. Prediction recovery after traffic termination is consistent with the sliding-window design.
6. The experimental traffic traverses the intended EVPN/VXLAN overlay.

---

## Selected Online Model

The selected model is:

```text
Queue + Traffic Random Forest
```

Features:

- `bottleneck_mbit`
- `requested_flows_mean`
- `active_flows_mean`
- `mean_overlimits_rate`
- `max_overlimits_rate`
- `std_overlimits_rate`
- `overlimits_rate_slope`

Online configuration:

- Observation window: `2.0 s`
- Telemetry sampling interval: `0.2 s`
- Prediction interval: `1.0 s`
- Warning threshold: `0.50`

---

## Mitigation Controller

Baseline bottleneck:

```text
10 Mbit/s
```

Mitigation rate:

```text
20 Mbit/s
```

The refined controller also requires `active_flows > 0` before mitigation can be triggered.

---

## Formal A/B Mitigation Evaluation

Five repeated runs are performed for each condition.

Mean RTT:

```text
OFF ≈ 90.8 ms
ON  ≈ 77.2 ms
```

Average reduction: approximately `15%`.

High-latency ratio:

```text
OFF ≈ 0.906
ON  ≈ 0.466
```

Reduction: approximately `48.6%`.

P99 RTT and maximum RTT remain more variable.

---

## Single-flow and Dual-flow Validation

| Condition | Mean Risk | Mean Overlimits Rate |
|---|---:|---:|
| Single flow | 0.791 | 112.9 events/s |
| Dual flow | 0.828 | 177.2 events/s |

The dual-flow condition produced stronger queue pressure and moderately higher predicted risk.

Mean RTT was not consistently higher under dual-flow traffic in this individual experiment.

---

## Risk Recovery after Traffic Termination

Observed recovery times:

- Mean time to risk below `0.5`: `1.73 s`
- Mean time to low-risk baseline: `2.36 s`

This is consistent with the 2-second sliding observation window.

---

## Packet-scale Validation

Six measured Phase 3 runs were analysed.

| Metric | Mean |
|---|---:|
| Bottleneck packets per run | 2885 |
| Spine packet rate | 44.55 pkt/s |
| Spine throughput | 4.17 Mbit/s |
| Delivery ratio | 0.984 |

Packet observations are distinct from machine-learning prediction-window samples.

---

## EVPN/VXLAN Overlay Verification

Confirmed VXLAN configuration:

```text
leaf1 VTEP = 1.1.1.1
leaf2 VTEP = 2.2.2.2
VXLAN interface = vxlan100
VNI = 100
UDP destination port = 4789
```

### Bridge / FDB Verification

The VXLAN forwarding entries confirmed the remote VTEP mappings between leaf1 and leaf2.

### BGP EVPN Control Plane

Confirmed:

- leaf1 BGP peer established
- spine BGP peers established
- leaf2 BGP peer established
- L2VPN EVPN address family active
- EVPN Type-2 routes present
- EVPN Type-3 routes present

AS numbers:

```text
spine  AS 65000
leaf1  AS 65001
leaf2  AS 65002
```

### VXLAN Data Plane

Packet capture on the spine showed:

```text
1.1.1.1 → 2.2.2.2
UDP destination port 4789
VXLAN VNI 100
```

and:

```text
2.2.2.2 → 1.1.1.1
UDP destination port 4789
VXLAN VNI 100
```

Inner traffic:

```text
192.168.100.11 ↔ 192.168.100.22
```

This verifies that h1-to-h2 traffic traverses the intended EVPN/VXLAN overlay.

---

## Final Queue + Traffic Feature Definition

| Feature | Category | Description |
|---|---|---|
| `bottleneck_mbit` | Configuration | Configured bottleneck link capacity |
| `requested_flows_mean` | Traffic | Mean requested flow count in the observation window |
| `active_flows_mean` | Traffic | Mean active TCP flow count in the observation window |
| `mean_overlimits_rate` | Queue | Mean TBF overlimit-event rate |
| `max_overlimits_rate` | Queue | Maximum overlimit-event rate |
| `std_overlimits_rate` | Queue | Variability of queue pressure |
| `overlimits_rate_slope` | Queue | Trend in queue pressure over the observation window |

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

Important data files include:

```text
flow_comparison_summary.csv
risk_recovery_summary.csv
thesis_key_results.csv
evpn_vxlan_verification_table.csv
online_feature_definition_table.csv
```

Packet statistics:

```text
packet_stats/
├── measured_runs.csv
├── measured_snapshots.csv
├── packet_snapshots.csv
├── packet_summary.csv
└── paper_packet_statistics.csv
```

Important newer scripts include:

```text
analyze_flow_comparison.py
analyze_packet_runs.py
analyze_risk_recovery.py
calculate_packet_summary.py
make_feature_ablation_paper.py
make_feature_definition_table.py
make_overlay_verification_table.py
make_thesis_key_results_summary.py
online_predictor_flow_comparison.py
plot_phase3_analysis.py
record_packet_snapshot.py
run_flow_comparison.py
run_phase3_batch.py
run_phase3_measured.py
```

---

## Current Conclusion

Phase 3 demonstrates that an offline-trained Queue + Traffic Random Forest can operate on live telemetry and be integrated into an online mitigation controller.

Repeated A/B experiments indicate that prediction-driven mitigation can reduce average latency and high-latency exposure.

Additional validation shows that:

- Dual-flow traffic creates greater queue pressure than single-flow traffic
- Risk recovery is consistent with the 2-second observation window
- Individual runs contain thousands of bottleneck-interface packet observations
- The evaluated traffic traverses a verified BGP EVPN/VXLAN overlay

---

## Current Limitations

- Small controlled software-based testbed
- Controlled traffic patterns
- No complete eBPF telemetry implementation yet
- CPU overhead not yet fully quantified
- Early-warning recall remains relatively low at the current threshold
- Extreme tail latency remains variable
- Production-like workload diversity has not been evaluated

---

## Future Extensions

- eBPF-based telemetry integration and validation
- Comparison between eBPF telemetry and existing queue / traffic signals
- CPU-overhead evaluation
- Additional latency-spike metrics
- Packet-loss evaluation
- Threshold optimisation
- Limited robustness testing under additional traffic and bottleneck conditions
