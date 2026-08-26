import os
import glob
import pandas as pd
import numpy as np


# ==========================================
# Configuration
# ==========================================

DATA_DIR = "/home/yuxsun/phase2/data"

OUTPUT_FILE = (
    "/home/yuxsun/phase2/data/"
    "final_prediction_dataset.csv"
)

OBS_WINDOW = 2.0
PRED_WINDOW = 2.0
STRIDE = 1.0

RTT_THRESHOLD = 75.0
HIGH_RATIO_THRESHOLD = 0.5


# ==========================================
# Helper: slope
# ==========================================

def calculate_slope(time_values, values):

    x = np.asarray(
        time_values,
        dtype=float
    )

    y = np.asarray(
        values,
        dtype=float
    )

    valid = (
        np.isfinite(x)
        &
        np.isfinite(y)
    )

    x = x[valid]
    y = y[valid]

    if len(x) < 2:
        return 0.0

    if np.allclose(
        x,
        x[0]
    ):
        return 0.0

    return float(
        np.polyfit(
            x,
            y,
            1
        )[0]
    )


# ==========================================
# Find files
# ==========================================

pilot_files = sorted(
    glob.glob(
        os.path.join(
            DATA_DIR,
            "pilot_*m_run*.csv"
        )
    )
)

formal_files = sorted(
    glob.glob(
        os.path.join(
            DATA_DIR,
            "formal_*m_run*.csv"
        )
    )
)


pilot_files = [
    f
    for f in pilot_files
    if not f.endswith(
        "_metadata.csv"
    )
]

formal_files = [
    f
    for f in formal_files
    if not f.endswith(
        "_metadata.csv"
    )
]


files = (
    pilot_files
    +
    formal_files
)


print()
print(
    "=== Building Final Prediction Dataset ==="
)
print()

print(
    "Pilot runs =",
    len(pilot_files)
)

print(
    "Formal runs =",
    len(formal_files)
)

print(
    "Total runs =",
    len(files)
)

print()


# ==========================================
# Process one run
# ==========================================

all_samples = []


for file in files:

    run_name = (
        os.path.basename(file)
        .replace(
            ".csv",
            ""
        )
    )

    if run_name.startswith(
        "pilot_"
    ):
        dataset_type = "pilot"

    else:
        dataset_type = "formal"


    print(
        "Processing:",
        run_name
    )


    df = pd.read_csv(
        file
    )

    df = (
        df.sort_values(
            "time_s"
        )
        .reset_index(
            drop=True
        )
    )


    # ======================================
    # Counter-derived telemetry
    # ======================================

    df["delta_t"] = (
        df["time_s"]
        .diff()
    )

    df[
        "delta_overlimits"
    ] = (
        df["overlimits"]
        .diff()
    )

    df.loc[
        df["delta_overlimits"] < 0,
        "delta_overlimits"
    ] = 0

    df[
        "delta_overlimits"
    ] = (
        df[
            "delta_overlimits"
        ]
        .fillna(0)
    )


    df[
        "overlimits_rate"
    ] = (
        df[
            "delta_overlimits"
        ]
        /
        df[
            "delta_t"
        ]
    )

    df[
        "overlimits_rate"
    ] = (
        df[
            "overlimits_rate"
        ]
        .replace(
            [
                np.inf,
                -np.inf
            ],
            np.nan
        )
        .fillna(0)
    )


    max_time = (
        df["time_s"]
        .max()
    )

    start = 0.0


    # ======================================
    # Sliding prediction windows
    # ======================================

    while (
        start
        + OBS_WINDOW
        + PRED_WINDOW
        <= max_time
    ):

        obs_start = start
        obs_end = (
            obs_start
            + OBS_WINDOW
        )

        future_start = (
            obs_end
        )

        future_end = (
            future_start
            + PRED_WINDOW
        )


        observation = df[
            (
                df["time_s"]
                >= obs_start
            )
            &
            (
                df["time_s"]
                < obs_end
            )
        ]


        future = df[
            (
                df["time_s"]
                >= future_start
            )
            &
            (
                df["time_s"]
                < future_end
            )
        ]


        if (
            len(observation) < 2
            or
            len(future) < 2
        ):

            start += STRIDE
            continue


        # ==================================
        # Current state
        # ==================================

        current_high_ratio = (
            observation[
                "rtt_ms"
            ]
            .gt(
                RTT_THRESHOLD
            )
            .mean()
        )

        current_high = int(
            current_high_ratio
            >= HIGH_RATIO_THRESHOLD
        )


        # ==================================
        # Future state / label
        # ==================================

        future_high_ratio = (
            future[
                "rtt_ms"
            ]
            .gt(
                RTT_THRESHOLD
            )
            .mean()
        )

        future_high = int(
            future_high_ratio
            >= HIGH_RATIO_THRESHOLD
        )


        # ==================================
        # RTT features
        # ==================================

        mean_rtt = (
            observation[
                "rtt_ms"
            ].mean()
        )

        std_rtt = (
            observation[
                "rtt_ms"
            ].std(
                ddof=0
            )
        )

        min_rtt = (
            observation[
                "rtt_ms"
            ].min()
        )

        max_rtt = (
            observation[
                "rtt_ms"
            ].max()
        )

        median_rtt = (
            observation[
                "rtt_ms"
            ].median()
        )

        p95_rtt = float(
            np.percentile(
                observation[
                    "rtt_ms"
                ],
                95
            )
        )

        rtt_slope = (
            calculate_slope(
                observation[
                    "time_s"
                ],
                observation[
                    "rtt_ms"
                ]
            )
        )


        # ==================================
        # Queue features
        # ==================================

        mean_overlimits_rate = (
            observation[
                "overlimits_rate"
            ].mean()
        )

        max_overlimits_rate = (
            observation[
                "overlimits_rate"
            ].max()
        )

        std_overlimits_rate = (
            observation[
                "overlimits_rate"
            ].std(
                ddof=0
            )
        )

        overlimits_rate_slope = (
            calculate_slope(
                observation[
                    "time_s"
                ],
                observation[
                    "overlimits_rate"
                ]
            )
        )


        # ==================================
        # Traffic features
        # ==================================

        requested_flows_mean = (
            observation[
                "requested_flows"
            ].mean()
        )

        active_flows_mean = (
            observation[
                "active_flows"
            ].mean()
        )

        bottleneck_mbit = (
            observation[
                "bottleneck_mbit"
            ].iloc[0]
        )


        # ==================================
        # Transition
        # ==================================

        if (
            current_high == 0
            and
            future_high == 0
        ):

            transition = (
                "NORMAL_TO_NORMAL"
            )

        elif (
            current_high == 0
            and
            future_high == 1
        ):

            transition = (
                "NORMAL_TO_HIGH"
            )

        elif (
            current_high == 1
            and
            future_high == 1
        ):

            transition = (
                "HIGH_TO_HIGH"
            )

        else:

            transition = (
                "HIGH_TO_NORMAL"
            )


        # ==================================
        # Store sample
        # ==================================

        all_samples.append({

            "dataset_type":
                dataset_type,

            "run":
                run_name,

            "obs_start_s":
                obs_start,

            "obs_end_s":
                obs_end,

            "future_start_s":
                future_start,

            "future_end_s":
                future_end,

            "bottleneck_mbit":
                bottleneck_mbit,

            "requested_flows_mean":
                requested_flows_mean,

            "active_flows_mean":
                active_flows_mean,

            "mean_rtt":
                mean_rtt,

            "std_rtt":
                std_rtt,

            "min_rtt":
                min_rtt,

            "max_rtt":
                max_rtt,

            "median_rtt":
                median_rtt,

            "p95_rtt":
                p95_rtt,

            "rtt_slope":
                rtt_slope,

            "mean_overlimits_rate":
                mean_overlimits_rate,

            "max_overlimits_rate":
                max_overlimits_rate,

            "std_overlimits_rate":
                std_overlimits_rate,

            "overlimits_rate_slope":
                overlimits_rate_slope,

            "current_high_ratio":
                current_high_ratio,

            "current_high":
                current_high,

            "future_high_ratio":
                future_high_ratio,

            "label":
                future_high,

            "transition":
                transition
        })


        start += STRIDE


# ==========================================
# Final DataFrame
# ==========================================

dataset = pd.DataFrame(
    all_samples
)


# ==========================================
# Main summary
# ==========================================

print()
print(
    "========================================"
)

print(
    "=== Final Prediction Dataset Summary ==="
)

print(
    "========================================"
)

print()

print(
    "Total prediction samples =",
    len(dataset)
)

print(
    "Positive labels =",
    int(
        dataset["label"].sum()
    )
)

print(
    "Negative labels =",
    int(
        len(dataset)
        -
        dataset["label"].sum()
    )
)

print(
    "Positive ratio =",
    f"{dataset['label'].mean():.2%}"
)


# ==========================================
# Dataset type
# ==========================================

print()
print(
    "=== Pilot / Formal Distribution ==="
)
print()

print(
    dataset[
        "dataset_type"
    ]
    .value_counts()
)


# ==========================================
# Transition distribution
# ==========================================

print()
print(
    "=== Transition Distribution ==="
)
print()

transition_counts = (
    dataset[
        "transition"
    ]
    .value_counts()
)

print(
    transition_counts
)


# ==========================================
# Important early-warning statistics
# ==========================================

normal_current = (
    dataset[
        "current_high"
    ] == 0
)

early_df = (
    dataset[
        normal_current
    ]
)

normal_to_high = (
    early_df[
        "label"
    ].sum()
)

print()
print(
    "=== Early-warning Dataset ==="
)
print()

print(
    "Current-NORMAL samples =",
    len(early_df)
)

print(
    "NORMAL -> HIGH samples =",
    int(
        normal_to_high
    )
)

print(
    "NORMAL -> NORMAL samples =",
    int(
        len(early_df)
        -
        normal_to_high
    )
)

print(
    "Early-warning positive ratio =",
    f"{early_df['label'].mean():.2%}"
)


# ==========================================
# Bottleneck summary
# ==========================================

print()
print(
    "=== Bottleneck Distribution ==="
)
print()

bottleneck_summary = (
    dataset
    .groupby(
        "bottleneck_mbit"
    )["label"]
    .agg(
        [
            "count",
            "sum",
            "mean"
        ]
    )
)

print(
    bottleneck_summary
)


# ==========================================
# Transition by bottleneck
# ==========================================

print()
print(
    "=== NORMAL -> HIGH by Bottleneck ==="
)
print()

normal_high_by_rate = (
    dataset[
        dataset[
            "transition"
        ]
        ==
        "NORMAL_TO_HIGH"
    ]
    .groupby(
        "bottleneck_mbit"
    )
    .size()
)

print(
    normal_high_by_rate
)


# ==========================================
# Run-level summary
# ==========================================

print()
print(
    "=== Run-level Summary ==="
)
print()

run_summary = (
    dataset
    .groupby(
        [
            "dataset_type",
            "run"
        ]
    )
    .agg(
        samples=(
            "label",
            "size"
        ),
        positive_labels=(
            "label",
            "sum"
        ),
        positive_ratio=(
            "label",
            "mean"
        ),
        normal_to_high=(
            "transition",
            lambda x:
                (
                    x
                    ==
                    "NORMAL_TO_HIGH"
                ).sum()
        )
    )
)

print(
    run_summary.to_string()
)


# ==========================================
# Save
# ==========================================

dataset.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print(
    "Final prediction dataset saved to:"
)

print(
    OUTPUT_FILE
)