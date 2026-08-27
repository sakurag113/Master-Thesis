#!/usr/bin/env python3

import os
import pandas as pd
import numpy as np


# ============================================================
# Paths
# ============================================================

INPUT_FILE = (
    "/home/yuxsun/phase3/logs/"
    "online_prediction_log_v2.csv"
)

OUTPUT_DIR = (
    "/home/yuxsun/phase3/data"
)

OUTPUT_FILE = (
    "/home/yuxsun/phase3/data/"
    "online_prediction_summary.csv"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# Load data
# ============================================================

df = pd.read_csv(
    INPUT_FILE
)


print()
print(
    "=== Phase 3 Online Prediction Analysis ==="
)
print()

print(
    f"Total prediction records = {len(df)}"
)

print(
    f"Experiment duration = "
    f"{df['time_s'].max():.1f} s"
)

print()


# ============================================================
# Basic flow-count check
# ============================================================

print(
    "=== Active Flow Distribution ==="
)
print()

flow_counts = (
    df["active_flows"]
    .value_counts()
    .sort_index()
)

print(
    flow_counts.to_string()
)

print()


# ============================================================
# Group by active flow count
# ============================================================

summary = (
    df.groupby(
        "active_flows"
    )
    .agg(
        samples=(
            "active_flows",
            "size"
        ),

        mean_overlimits_rate=(
            "mean_overlimits_rate",
            "mean"
        ),

        max_overlimits_rate=(
            "max_overlimits_rate",
            "max"
        ),

        mean_risk=(
            "future_high_probability",
            "mean"
        ),

        max_risk=(
            "future_high_probability",
            "max"
        ),

        warning_ratio=(
            "prediction",
            "mean"
        )
    )
    .reset_index()
)


print(
    "=== Prediction Summary by Active Flows ==="
)
print()

print(
    summary.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)

print()


# ============================================================
# Traffic-only records
# ============================================================

traffic_df = df[
    df["active_flows"] > 0
].copy()


if len(traffic_df) == 0:

    print(
        "WARNING:"
    )

    print(
        "No records with active_flows > 0 "
        "were found."
    )

    print(
        "The predictor may not have detected "
        "the traffic generator."
    )

else:

    print(
        "=== Traffic-period Records ==="
    )
    print()

    print(
        f"Records with active traffic = "
        f"{len(traffic_df)}"
    )

    print(
        f"First detected traffic at predictor "
        f"time = {traffic_df['time_s'].min():.1f} s"
    )

    print(
        f"Last detected traffic at predictor "
        f"time = {traffic_df['time_s'].max():.1f} s"
    )

    print()

    print(
        f"Mean risk during traffic = "
        f"{traffic_df['future_high_probability'].mean():.4f}"
    )

    print(
        f"Maximum risk during traffic = "
        f"{traffic_df['future_high_probability'].max():.4f}"
    )

    print(
        f"Warning ratio during traffic = "
        f"{traffic_df['prediction'].mean():.4f}"
    )

    print(
        f"Mean overlimits rate during traffic = "
        f"{traffic_df['mean_overlimits_rate'].mean():.2f}/s"
    )

    print()


# ============================================================
# Baseline records
# ============================================================

baseline_df = df[
    df["active_flows"] == 0
].copy()


if len(baseline_df) > 0:

    print(
        "=== Baseline Records ==="
    )
    print()

    print(
        f"Mean risk at 0 flows = "
        f"{baseline_df['future_high_probability'].mean():.4f}"
    )

    print(
        f"Maximum risk at 0 flows = "
        f"{baseline_df['future_high_probability'].max():.4f}"
    )

    print(
        f"Warning ratio at 0 flows = "
        f"{baseline_df['prediction'].mean():.4f}"
    )

    print()


# ============================================================
# Show high-risk samples
# ============================================================

high_risk = (
    df.sort_values(
        "future_high_probability",
        ascending=False
    )
    .head(15)
)


print(
    "=== Top 15 Highest-risk Predictions ==="
)
print()

columns_to_show = [
    "time_s",
    "active_flows",
    "mean_overlimits_rate",
    "max_overlimits_rate",
    "future_high_probability",
    "prediction"
]

print(
    high_risk[
        columns_to_show
    ].to_string(
        index=False,
        float_format=lambda x: f"{x:.3f}"
    )
)

print()


# ============================================================
# Detect flow-state changes
# ============================================================

df["previous_flows"] = (
    df["active_flows"]
    .shift(1)
)

changes = df[
    df["active_flows"]
    != df["previous_flows"]
].copy()


print(
    "=== Detected Flow-state Changes ==="
)
print()

if len(changes) > 0:

    print(
        changes[
            [
                "time_s",
                "previous_flows",
                "active_flows",
                "future_high_probability"
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}"
        )
    )

else:

    print(
        "No flow-state changes detected."
    )

print()


# ============================================================
# Save summary
# ============================================================

summary.to_csv(
    OUTPUT_FILE,
    index=False
)

print(
    "Summary saved to:"
)

print(
    OUTPUT_FILE
)

print()