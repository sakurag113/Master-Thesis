#!/usr/bin/env python3

import os
import glob
import numpy as np
import pandas as pd


# ============================================================
# Paths
# ============================================================

LOG_DIR = "/home/yuxsun/phase3/logs"
DATA_DIR = "/home/yuxsun/phase3/data"

RUN_LEVEL_FILE = (
    "/home/yuxsun/phase3/data/"
    "formal_ab_run_level_results.csv"
)

SUMMARY_FILE = (
    "/home/yuxsun/phase3/data/"
    "formal_ab_summary.csv"
)

PAIRED_FILE = (
    "/home/yuxsun/phase3/data/"
    "formal_ab_paired_reduction.csv"
)

os.makedirs(
    DATA_DIR,
    exist_ok=True
)


# ============================================================
# Configuration
# ============================================================

RTT_THRESHOLD = 75.0


# ============================================================
# Helper: calculate one run
# ============================================================

def calculate_run_metrics(
    file_path,
    mode,
    run_id
):

    df = pd.read_csv(
        file_path
    )

    df["rtt_ms"] = pd.to_numeric(
        df["rtt_ms"],
        errors="coerce"
    )

    df["active_flows"] = pd.to_numeric(
        df["active_flows"],
        errors="coerce"
    )


    # --------------------------------------------------------
    # Only use active-traffic samples
    # --------------------------------------------------------

    active = df[
        (
            df["active_flows"] > 0
        )
        &
        (
            df["rtt_ms"].notna()
        )
    ].copy()


    if len(active) == 0:

        raise RuntimeError(
            f"No active-traffic RTT samples "
            f"in {file_path}"
        )


    rtt = (
        active["rtt_ms"]
        .astype(float)
    )


    high_mask = (
        rtt > RTT_THRESHOLD
    )


    result = {

        "mode":
            mode,

        "run":
            run_id,

        "samples":
            len(active),

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


    # --------------------------------------------------------
    # ON-specific controller statistics
    # --------------------------------------------------------

    if mode == "ON":

        if (
            "mitigation_triggered"
            in df.columns
        ):

            result[
                "mitigation_triggers"
            ] = int(
                pd.to_numeric(
                    df[
                        "mitigation_triggered"
                    ],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

        else:

            result[
                "mitigation_triggers"
            ] = np.nan


        if (
            "blocked_zero_flow"
            in df.columns
        ):

            result[
                "blocked_zero_flow"
            ] = int(
                pd.to_numeric(
                    df[
                        "blocked_zero_flow"
                    ],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

        else:

            result[
                "blocked_zero_flow"
            ] = np.nan


        if (
            "mitigation_active"
            in df.columns
        ):

            result[
                "mitigation_active_ratio"
            ] = float(
                pd.to_numeric(
                    df[
                        "mitigation_active"
                    ],
                    errors="coerce"
                )
                .fillna(0)
                .mean()
            )

        else:

            result[
                "mitigation_active_ratio"
            ] = np.nan


    else:

        result[
            "mitigation_triggers"
        ] = 0

        result[
            "blocked_zero_flow"
        ] = 0

        result[
            "mitigation_active_ratio"
        ] = 0.0


    return result


# ============================================================
# Collect files
# ============================================================

off_files = sorted(
    glob.glob(
        f"{LOG_DIR}/formal_off_run*.csv"
    )
)

on_files = sorted(
    glob.glob(
        f"{LOG_DIR}/formal_on_run*.csv"
    )
)


print()
print(
    "=== Phase 3 Formal A/B Analysis ==="
)
print()

print(
    f"OFF files = {len(off_files)}"
)

print(
    f"ON files  = {len(on_files)}"
)

print()


if len(off_files) == 0:

    raise RuntimeError(
        "No formal OFF files found."
    )


if len(on_files) == 0:

    raise RuntimeError(
        "No formal ON files found."
    )


# ============================================================
# Per-run results
# ============================================================

results = []


for i, file_path in enumerate(
    off_files,
    start=1
):

    results.append(
        calculate_run_metrics(
            file_path,
            "OFF",
            i
        )
    )


for i, file_path in enumerate(
    on_files,
    start=1
):

    results.append(
        calculate_run_metrics(
            file_path,
            "ON",
            i
        )
    )


run_df = pd.DataFrame(
    results
)

run_df.to_csv(
    RUN_LEVEL_FILE,
    index=False
)


print(
    "=== Run-level Results ==="
)
print()

print(
    run_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.3f}"
    )
)

print()


# ============================================================
# Group summary: mean ± std
# ============================================================

metric_columns = [
    "mean_rtt_ms",
    "median_rtt_ms",
    "p95_rtt_ms",
    "p99_rtt_ms",
    "max_rtt_ms",
    "high_ratio"
]


summary_rows = []


for mode in [
    "OFF",
    "ON"
]:

    subset = run_df[
        run_df["mode"] == mode
    ]


    for metric in metric_columns:

        summary_rows.append({

            "mode":
                mode,

            "metric":
                metric,

            "mean":
                float(
                    subset[
                        metric
                    ].mean()
                ),

            "std":
                float(
                    subset[
                        metric
                    ].std(
                        ddof=1
                    )
                )
        })


summary_df = pd.DataFrame(
    summary_rows
)

summary_df.to_csv(
    SUMMARY_FILE,
    index=False
)


print(
    "=== Mean ± Std Summary ==="
)
print()


for metric in metric_columns:

    off_row = summary_df[
        (
            summary_df["mode"]
            == "OFF"
        )
        &
        (
            summary_df["metric"]
            == metric
        )
    ].iloc[0]

    on_row = summary_df[
        (
            summary_df["mode"]
            == "ON"
        )
        &
        (
            summary_df["metric"]
            == metric
        )
    ].iloc[0]


    off_mean = float(
        off_row["mean"]
    )

    off_std = float(
        off_row["std"]
    )

    on_mean = float(
        on_row["mean"]
    )

    on_std = float(
        on_row["std"]
    )


    if off_mean != 0:

        reduction = (
            (
                off_mean
                - on_mean
            )
            /
            off_mean
            * 100.0
        )

    else:

        reduction = np.nan


    print(
        f"{metric:16s} | "
        f"OFF = {off_mean:.3f} ± {off_std:.3f} | "
        f"ON = {on_mean:.3f} ± {on_std:.3f} | "
        f"reduction = {reduction:.2f}%"
    )


print()


# ============================================================
# Paired OFF vs ON run comparison
# ============================================================

paired_rows = []

number_of_pairs = min(
    len(off_files),
    len(on_files)
)


for run_id in range(
    1,
    number_of_pairs + 1
):

    off_row = run_df[
        (
            run_df["mode"]
            == "OFF"
        )
        &
        (
            run_df["run"]
            == run_id
        )
    ].iloc[0]

    on_row = run_df[
        (
            run_df["mode"]
            == "ON"
        )
        &
        (
            run_df["run"]
            == run_id
        )
    ].iloc[0]


    row = {
        "run":
            run_id
    }


    for metric in metric_columns:

        off_value = float(
            off_row[
                metric
            ]
        )

        on_value = float(
            on_row[
                metric
            ]
        )


        if off_value != 0:

            reduction = (
                (
                    off_value
                    - on_value
                )
                /
                off_value
                * 100.0
            )

        else:

            reduction = np.nan


        row[
            f"{metric}_off"
        ] = off_value

        row[
            f"{metric}_on"
        ] = on_value

        row[
            f"{metric}_reduction_pct"
        ] = reduction


    paired_rows.append(
        row
    )


paired_df = pd.DataFrame(
    paired_rows
)

paired_df.to_csv(
    PAIRED_FILE,
    index=False
)


print(
    "=== Paired Reduction by Run ==="
)
print()


paired_columns = [
    "mean_rtt_ms_reduction_pct",
    "p95_rtt_ms_reduction_pct",
    "p99_rtt_ms_reduction_pct",
    "max_rtt_ms_reduction_pct",
    "high_ratio_reduction_pct"
]


for _, row in paired_df.iterrows():

    print(
        f"Run {int(row['run'])}: "
        f"mean={row['mean_rtt_ms_reduction_pct']:.2f}% | "
        f"p95={row['p95_rtt_ms_reduction_pct']:.2f}% | "
        f"p99={row['p99_rtt_ms_reduction_pct']:.2f}% | "
        f"max={row['max_rtt_ms_reduction_pct']:.2f}% | "
        f"HIGH ratio={row['high_ratio_reduction_pct']:.2f}%"
    )


print()


# ============================================================
# Average paired reduction
# ============================================================

print(
    "=== Mean Paired Reduction ==="
)
print()


for column in paired_columns:

    mean_value = float(
        paired_df[
            column
        ].mean()
    )

    std_value = float(
        paired_df[
            column
        ].std(
            ddof=1
        )
    )


    print(
        f"{column:32s}: "
        f"{mean_value:.2f}% "
        f"± {std_value:.2f}%"
    )


print()


# ============================================================
# Controller summary
# ============================================================

on_only = run_df[
    run_df["mode"] == "ON"
]


print(
    "=== Controller Summary ==="
)
print()

print(
    "Mitigation triggers per run:"
)

print(
    on_only[
        [
            "run",
            "mitigation_triggers",
            "blocked_zero_flow",
            "mitigation_active_ratio"
        ]
    ].to_string(
        index=False,
        float_format=lambda x: f"{x:.3f}"
    )
)

print()

print(
    f"Mean triggers/run = "
    f"{on_only['mitigation_triggers'].mean():.2f}"
)

print(
    f"Mean blocked zero-flow warnings/run = "
    f"{on_only['blocked_zero_flow'].mean():.2f}"
)

print(
    f"Mean mitigation-active ratio = "
    f"{on_only['mitigation_active_ratio'].mean():.3f}"
)


print()
print(
    "Files saved:"
)

print(
    RUN_LEVEL_FILE
)

print(
    SUMMARY_FILE
)

print(
    PAIRED_FILE
)

print()