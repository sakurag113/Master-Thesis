#!/usr/bin/env python3

import os
import numpy as np
import pandas as pd


# ============================================================
# Paths
# ============================================================

OFF_FILE = (
    "/home/yuxsun/phase3/logs/"
    "online_validation_log.csv"
)

ON_FILE = (
    "/home/yuxsun/phase3/logs/"
    "mitigation_on_log.csv"
)

OUTPUT_DIR = (
    "/home/yuxsun/phase3/data"
)

SUMMARY_FILE = (
    "/home/yuxsun/phase3/data/"
    "mitigation_comparison_summary.csv"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# Configuration
# ============================================================

RTT_THRESHOLD = 75.0


# ============================================================
# Load datasets
# ============================================================

off = pd.read_csv(
    OFF_FILE
)

on = pd.read_csv(
    ON_FILE
)


print()
print(
    "=== Phase 3 Mitigation OFF vs ON ==="
)
print()


# ============================================================
# Clean RTT
# ============================================================

off["rtt_ms"] = pd.to_numeric(
    off["rtt_ms"],
    errors="coerce"
)

on["rtt_ms"] = pd.to_numeric(
    on["rtt_ms"],
    errors="coerce"
)

off["active_flows"] = pd.to_numeric(
    off["active_flows"],
    errors="coerce"
)

on["active_flows"] = pd.to_numeric(
    on["active_flows"],
    errors="coerce"
)


# ============================================================
# Evaluation function
# ============================================================

def calculate_metrics(
    df,
    experiment,
    subset_name
):

    valid = df[
        df["rtt_ms"].notna()
    ].copy()

    if len(valid) == 0:

        return None


    rtt = (
        valid["rtt_ms"]
        .astype(float)
    )


    high_mask = (
        rtt > RTT_THRESHOLD
    )


    result = {

        "experiment":
            experiment,

        "subset":
            subset_name,

        "samples":
            len(valid),

        "mean_rtt_ms":
            float(
                rtt.mean()
            ),

        "median_rtt_ms":
            float(
                rtt.median()
            ),

        "p95_rtt_ms":
            float(
                np.percentile(
                    rtt,
                    95
                )
            ),

        "p99_rtt_ms":
            float(
                np.percentile(
                    rtt,
                    99
                )
            ),

        "max_rtt_ms":
            float(
                rtt.max()
            ),

        "high_samples":
            int(
                high_mask.sum()
            ),

        "high_ratio":
            float(
                high_mask.mean()
            )
    }

    return result


# ============================================================
# Build subsets
# ============================================================

results = []


# ------------------------------------------------------------
# Entire recorded experiment
# ------------------------------------------------------------

result = calculate_metrics(
    off,
    "Mitigation OFF",
    "All Samples"
)

if result:
    results.append(result)


result = calculate_metrics(
    on,
    "Mitigation ON",
    "All Samples"
)

if result:
    results.append(result)


# ------------------------------------------------------------
# Active traffic only
#
# This is the most important comparison because long idle
# baseline periods otherwise dominate the RTT statistics.
# ------------------------------------------------------------

off_active = off[
    off["active_flows"] > 0
].copy()

on_active = on[
    on["active_flows"] > 0
].copy()


result = calculate_metrics(
    off_active,
    "Mitigation OFF",
    "Active Traffic"
)

if result:
    results.append(result)


result = calculate_metrics(
    on_active,
    "Mitigation ON",
    "Active Traffic"
)

if result:
    results.append(result)


# ------------------------------------------------------------
# 2-stream traffic
# ------------------------------------------------------------

off_2 = off[
    off["active_flows"] == 2
].copy()

on_2 = on[
    on["active_flows"] == 2
].copy()


result = calculate_metrics(
    off_2,
    "Mitigation OFF",
    "2 Streams"
)

if result:
    results.append(result)


result = calculate_metrics(
    on_2,
    "Mitigation ON",
    "2 Streams"
)

if result:
    results.append(result)


# ------------------------------------------------------------
# 3-stream traffic
# ------------------------------------------------------------

off_3 = off[
    off["active_flows"] == 3
].copy()

on_3 = on[
    on["active_flows"] == 3
].copy()


result = calculate_metrics(
    off_3,
    "Mitigation OFF",
    "3 Streams"
)

if result:
    results.append(result)


result = calculate_metrics(
    on_3,
    "Mitigation ON",
    "3 Streams"
)

if result:
    results.append(result)


# ============================================================
# Save summary
# ============================================================

summary = pd.DataFrame(
    results
)

summary.to_csv(
    SUMMARY_FILE,
    index=False
)


# ============================================================
# Print results
# ============================================================

print(
    summary.to_string(
        index=False,
        float_format=lambda x: f"{x:.3f}"
    )
)

print()


# ============================================================
# Calculate improvement for active traffic
# ============================================================

off_active_result = summary[
    (
        summary["experiment"]
        == "Mitigation OFF"
    )
    &
    (
        summary["subset"]
        == "Active Traffic"
    )
]

on_active_result = summary[
    (
        summary["experiment"]
        == "Mitigation ON"
    )
    &
    (
        summary["subset"]
        == "Active Traffic"
    )
]


if (
    len(off_active_result) == 1
    and
    len(on_active_result) == 1
):

    off_row = (
        off_active_result.iloc[0]
    )

    on_row = (
        on_active_result.iloc[0]
    )


    print(
        "=== Active-traffic Improvement ==="
    )

    print()


    metrics = [
        "mean_rtt_ms",
        "p95_rtt_ms",
        "p99_rtt_ms",
        "max_rtt_ms",
        "high_ratio"
    ]


    for metric in metrics:

        off_value = float(
            off_row[metric]
        )

        on_value = float(
            on_row[metric]
        )


        if off_value != 0:

            improvement = (
                (
                    off_value
                    - on_value
                )
                /
                off_value
                * 100.0
            )

        else:

            improvement = np.nan


        print(
            f"{metric:16s}: "
            f"OFF={off_value:.3f}   "
            f"ON={on_value:.3f}   "
            f"reduction={improvement:.2f}%"
        )


# ============================================================
# Mitigation statistics
# ============================================================

if "mitigation_triggered" in on.columns:

    triggers = int(
        pd.to_numeric(
            on["mitigation_triggered"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )

    print()
    print(
        "=== Mitigation Controller ==="
    )

    print()

    print(
        f"Total mitigation triggers = "
        f"{triggers}"
    )


if "mitigation_active" in on.columns:

    mitigation_ratio = (
        pd.to_numeric(
            on["mitigation_active"],
            errors="coerce"
        )
        .fillna(0)
        .mean()
    )

    print(
        f"Fraction of samples with mitigation active = "
        f"{mitigation_ratio:.3f}"
    )


print()
print(
    "Summary saved to:"
)

print(
    SUMMARY_FILE
)

print()