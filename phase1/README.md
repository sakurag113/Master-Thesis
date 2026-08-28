# Phase 1 – Environment and Data Collection

## Purpose

Phase 1 establishes the experimental network environment and verifies that controlled traffic can reproduce congestion-related latency spikes.

The main objective is to create a reliable data-collection pipeline that can later be used for feature analysis and prediction.

---

## Experimental Workflow

```text
Network Testbed
      ↓
Traffic Generation
      ↓
Controlled Bottleneck
      ↓
RTT and Queue Measurements
      ↓
Latency / Queue Analysis
```

---

## Main Tasks

Phase 1 includes:

- Network testbed setup
- Linux network namespace configuration
- FRR and EVPN/VXLAN-related configuration
- Traffic generation using iperf3
- Bottleneck creation using Linux Traffic Control
- End-to-end RTT measurement
- Queue-related signal collection
- Baseline experiments
- Single-flow experiments
- Multi-flow experiments
- Repeated-run analysis
- High-latency and queue-signal comparison

---

## Directory Structure

```text
phase1/
├── data/
├── logs/
├── notes/
├── plots/
└── scripts/
```

### `data/`

Contains raw and processed experimental datasets generated during Phase 1.

### `logs/`

Contains execution logs and supporting experiment outputs.

### `notes/`

Contains experiment notes and supporting documentation.

### `plots/`

Contains figures generated from Phase 1 datasets, including latency and queue-related visualisations.

### `scripts/`

Contains scripts for network setup, experiment execution, data collection, and analysis.

---

## Main Outcome

Phase 1 demonstrates that controlled traffic and bottleneck conditions can reproducibly produce measurable latency degradation.

Queue-related activity increases during high-latency periods, providing the basis for the feature and prediction analysis performed in Phase 2.

---

## Relationship to Phase 2

The Phase 1 results establish the feasibility of the experimental approach.

Phase 2 extends this workflow by:

- automating repeated experiments,
- generating a larger dataset,
- constructing sliding-window features,
- labelling future latency conditions,
- and evaluating prediction models.