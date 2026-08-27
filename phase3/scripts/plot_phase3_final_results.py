#!/usr/bin/env python3

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# Paths
# ============================================================

RUN_LEVEL_FILE = (
    "/home/yuxsun/phase3/data/"
    "formal_ab_run_level_results.csv"
)

PAIRED_FILE = (
    "/home/yuxsun/phase3/data/"
    "formal_ab_paired_reduction.csv"
)

PLOT_DIR = (
    "/home/yuxsun/phase3/plots"
)

os.makedirs(
    PLOT_DIR,
    exist_ok=True
)


# ============================================================
# Load data
# ============================================================

run_df = pd.read_csv(
    RUN_LEVEL_FILE
)

paired_df = pd.read_csv(
    PAIRED_FILE
)


print()
print(
    "=== Phase 3 Final Result Plotting ==="
)
print()


# ============================================================
# Helper
# ============================================================

def get_group_stats(metric):

    off = (
        run_df[
            run_df["mode"] == "OFF"
        ][metric]
        .astype(float)
    )

    on = (
        run_df[
            run_df["mode"] == "ON"
        ][metric]
        .astype(float)
    )

    return (
        off.mean(),
        off.std(ddof=1),
        on.mean(),
        on.std(ddof=1)
    )


# ============================================================
# Figure 1:
# Mean RTT OFF vs ON
# ============================================================

off_mean, off_std, on_mean, on_std = (
    get_group_stats(
        "mean_rtt_ms"
    )
)

labels = [
    "Mitigation OFF",
    "Mitigation ON"
]

values = [
    off_mean,
    on_mean
]

errors = [
    off_std,
    on_std
]


plt.figure(
    figsize=(7, 5)
)

plt.bar(
    labels,
    values,
    yerr=errors,
    capsize=6
)

plt.ylabel(
    "Mean RTT (ms)"
)

plt.title(
    "Mean RTT Under Active Traffic"
)

plt.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

file1 = (
    f"{PLOT_DIR}/"
    "phase3_mean_rtt_comparison.png"
)

plt.savefig(
    file1,
    dpi=300
)

plt.show()


# ============================================================
# Figure 2:
# HIGH-latency ratio OFF vs ON
# ============================================================

off_mean, off_std, on_mean, on_std = (
    get_group_stats(
        "high_ratio"
    )
)

labels = [
    "Mitigation OFF",
    "Mitigation ON"
]

values = [
    off_mean,
    on_mean
]

errors = [
    off_std,
    on_std
]


plt.figure(
    figsize=(7, 5)
)

plt.bar(
    labels,
    values,
    yerr=errors,
    capsize=6
)

plt.ylabel(
    "High-latency Sample Ratio"
)

plt.title(
    "High-latency Exposure Under Active Traffic"
)

plt.ylim(
    0,
    1.0
)

plt.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

file2 = (
    f"{PLOT_DIR}/"
    "phase3_high_ratio_comparison.png"
)

plt.savefig(
    file2,
    dpi=300
)

plt.show()


# ============================================================
# Figure 3:
# Paired reduction across 5 runs
# ============================================================

runs = (
    paired_df["run"]
    .astype(int)
    .values
)

mean_reduction = (
    paired_df[
        "mean_rtt_ms_reduction_pct"
    ]
    .astype(float)
    .values
)

high_reduction = (
    paired_df[
        "high_ratio_reduction_pct"
    ]
    .astype(float)
    .values
)


x = np.arange(
    len(runs)
)

width = 0.35


plt.figure(
    figsize=(8, 5)
)

plt.bar(
    x - width / 2,
    mean_reduction,
    width,
    label="Mean RTT reduction"
)

plt.bar(
    x + width / 2,
    high_reduction,
    width,
    label="HIGH-ratio reduction"
)

plt.xticks(
    x,
    [
        f"Run {run}"
        for run in runs
    ]
)

plt.ylabel(
    "Reduction (%)"
)

plt.title(
    "Paired Mitigation Improvement Across Runs"
)

plt.legend()

plt.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

file3 = (
    f"{PLOT_DIR}/"
    "phase3_paired_reduction.png"
)

plt.savefig(
    file3,
    dpi=300
)

plt.show()


# ============================================================
# Figure 4:
# Tail latency comparison
# ============================================================

metrics = [
    "p95_rtt_ms",
    "p99_rtt_ms",
    "max_rtt_ms"
]

metric_labels = [
    "p95 RTT",
    "p99 RTT",
    "Max RTT"
]

off_values = []
off_errors = []

on_values = []
on_errors = []


for metric in metrics:

    (
        off_mean,
        off_std,
        on_mean,
        on_std
    ) = get_group_stats(
        metric
    )

    off_values.append(
        off_mean
    )

    off_errors.append(
        off_std
    )

    on_values.append(
        on_mean
    )

    on_errors.append(
        on_std
    )


x = np.arange(
    len(metrics)
)

width = 0.35


plt.figure(
    figsize=(8, 5)
)

plt.bar(
    x - width / 2,
    off_values,
    width,
    yerr=off_errors,
    capsize=5,
    label="Mitigation OFF"
)

plt.bar(
    x + width / 2,
    on_values,
    width,
    yerr=on_errors,
    capsize=5,
    label="Mitigation ON"
)

plt.xticks(
    x,
    metric_labels
)

plt.ylabel(
    "RTT (ms)"
)

plt.title(
    "Tail Latency Comparison"
)

plt.legend()

plt.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

file4 = (
    f"{PLOT_DIR}/"
    "phase3_tail_latency_comparison.png"
)

plt.savefig(
    file4,
    dpi=300
)

plt.show()


# ============================================================
# Done
# ============================================================

print()
print(
    "Plots saved:"
)

print(
    file1
)

print(
    file2
)

print(
    file3
)

print(
    file4
)

print()