# Master Thesis Project

## eBPF-driven Fine-grained Telemetry and Machine Learning for EVPN/VXLAN Datacenter Networks

This repository contains the experimental implementation, datasets, analysis scripts, models, and results developed for my Master's thesis project.

The project investigates whether fine-grained network telemetry can provide early indicators of congestion-related latency spikes, whether machine learning can predict such events in advance, and whether prediction-driven mitigation can improve network latency performance.

The experimental work is organised into three phases.

---

## Project Overview

Transient traffic bursts can cause temporary queue buildup and significant latency spikes in datacenter networks.

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
Latency Spike Prediction
      ↓
Online Prediction
      ↓
Prediction-driven Mitigation
      ↓
Performance Evaluation
```

The current implementation uses a software-based network testbed built with Linux network namespaces, traffic control, FRR, and EVPN/VXLAN components.

---

## Repository Structure

```text
Master-Thesis/
│
├── README.md
│
├── phase1/
│   ├── data/
│   ├── logs/
│   ├── notes/
│   ├── plots/
│   └── scripts/
│
├── phase2/
│   ├── data/
│   ├── plots/
│   └── scripts/
│
└── phase3/
    ├── data/
    ├── logs/
    ├── models/
    ├── plots/
    └── scripts/
```

---

# Phase 1 – Environment and Data Collection

Phase 1 focuses on building the experimental network environment and verifying that congestion-related latency spikes can be reproduced and measured.

The main work includes:

- Building the software-based network testbed
- Configuring the EVPN/VXLAN environment
- Generating controlled network traffic
- Creating bottleneck conditions using Linux traffic control
- Measuring end-to-end RTT
- Collecting queue-related signals
- Comparing baseline, single-flow, and multi-flow traffic conditions
- Verifying the relationship between queue activity and high-latency events

The results from this phase establish the experimental and data-collection pipeline used in the later phases.

### Directory

```text
phase1/
├── data/       # Experimental datasets
├── logs/       # Experiment logs
├── notes/      # Experiment notes
├── plots/      # Generated figures
└── scripts/    # Testbed, experiment and analysis scripts
```

---

# Phase 2 – Feature Analysis and Prediction

Phase 2 focuses on constructing a larger labelled dataset and investigating whether network and queue-related features can be used to predict future high-latency events.

The main work includes:

- Automated and repeated experiment execution
- Dataset construction and validation
- Sliding-window feature extraction
- Latency-spike labelling
- Feature analysis
- Training and evaluation of prediction models
- Early-warning prediction
- Feature ablation experiments
- Run-grouped cross-validation

The experiments compare multiple prediction approaches and evaluate whether useful warning signals exist before high-latency events occur.

The selected prediction model is subsequently exported for online use in Phase 3.

### Directory

```text
phase2/
├── data/       # Processed datasets and evaluation results
├── plots/      # Prediction and feature-analysis figures
└── scripts/    # Data processing, training and evaluation scripts
```

---

# Phase 3 – Online Prediction and Mitigation

Phase 3 integrates the selected prediction model into an online prediction and mitigation pipeline.

The main work includes:

- Online traffic generation
- Real-time telemetry processing
- Online latency-risk prediction
- Prediction-driven mitigation
- Mitigation controller refinement
- Online prediction validation
- Repeated mitigation OFF/ON experiments
- Latency performance comparison

The final evaluation compares network behaviour with mitigation disabled and enabled under controlled traffic conditions.

The results show that prediction-driven mitigation can reduce average latency and the amount of time spent in high-latency conditions. However, extreme tail-latency measurements remain more variable and are not consistently improved.

### Directory

```text
phase3/
├── data/       # Final evaluation and comparison results
├── logs/       # Online and A/B experiment logs
├── models/     # Model and feature definitions used online
├── plots/      # Final evaluation figures
└── scripts/    # Online prediction, mitigation and analysis scripts
```

---

# Current Experimental Workflow

The relationship between the three phases can be summarised as:

```text
Phase 1
Testbed + Controlled Congestion
            ↓
Latency and Queue Signals
            ↓
Phase 2
Dataset + Feature Analysis
            ↓
Prediction Model
            ↓
Phase 3
Online Prediction
            ↓
Mitigation Controller
            ↓
A/B Performance Evaluation
```

Phase 1 establishes the experimental environment and verifies measurable latency behaviour.

Phase 2 transforms the collected observations into a prediction problem and evaluates candidate models.

Phase 3 integrates the selected model into an online controller and evaluates whether prediction-driven mitigation improves network performance.

---

# Future Work

The remaining work will focus on extending and validating the current experimental system rather than rebuilding the existing Phase 1–3 pipeline.

Planned work includes:

- Further verification of the EVPN/VXLAN forwarding path
- Integration and validation of eBPF-based telemetry
- CPU overhead evaluation for telemetry, prediction, and mitigation
- Additional latency-spike and packet-level evaluation metrics
- Limited robustness experiments under different traffic and bottleneck conditions
- Final integration and documentation of the experimental results

---

# Tools and Technologies

The project mainly uses:

- Linux
- Linux Network Namespaces
- FRR
- BGP EVPN
- VXLAN
- Linux Traffic Control (`tc`)
- iperf3
- Python
- Scikit-learn
- Pandas
- NumPy
- Matplotlib

eBPF-based telemetry is planned as an extension of the current telemetry implementation.

---

## Notes

This repository represents an experimental research prototype developed in a controlled software-based environment.

The objective is to investigate the feasibility of telemetry-driven latency prediction and prediction-based mitigation rather than to provide a production-ready datacenter networking system.