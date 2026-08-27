import pandas as pd
import numpy as np
import sys
import os


# ==========================================
# Configuration
# ==========================================

OBS_WINDOW = 2.0
PRED_WINDOW = 2.0
STRIDE = 1.0

RTT_THRESHOLD = 75.0
HIGH_RATIO_THRESHOLD = 0.5


# ==========================================
# Input
# ==========================================

if len(sys.argv) < 2:
    print("Usage:")
    print(
        "python3 analyze_transition_run.py "
        "/path/to/run.csv"
    )
    sys.exit(1)


file = sys.argv[1]


if not os.path.exists(file):
    print("File not found:")
    print(file)
    sys.exit(1)


# ==========================================
# Load
# ==========================================

df = pd.read_csv(file)

df = df.sort_values(
    "time_s"
).reset_index(drop=True)

max_time = df["time_s"].max()


# ==========================================
# Window analysis
# ==========================================

results = []

start = 0.0

while (
    start
    + OBS_WINDOW
    + PRED_WINDOW
    <= max_time
):

    obs_start = start
    obs_end = start + OBS_WINDOW

    future_start = obs_end
    future_end = (
        future_start + PRED_WINDOW
    )

    observation = df[
        (df["time_s"] >= obs_start)
        &
        (df["time_s"] < obs_end)
    ]

    future = df[
        (df["time_s"] >= future_start)
        &
        (df["time_s"] < future_end)
    ]

    if (
        len(observation) < 2
        or
        len(future) < 2
    ):
        start += STRIDE
        continue


    current_high_ratio = (
        observation["rtt_ms"]
        .gt(RTT_THRESHOLD)
        .mean()
    )

    future_high_ratio = (
        future["rtt_ms"]
        .gt(RTT_THRESHOLD)
        .mean()
    )

    current_high = int(
        current_high_ratio
        >= HIGH_RATIO_THRESHOLD
    )

    future_high = int(
        future_high_ratio
        >= HIGH_RATIO_THRESHOLD
    )


    if (
        current_high == 0
        and
        future_high == 0
    ):
        transition = "NORMAL_TO_NORMAL"

    elif (
        current_high == 0
        and
        future_high == 1
    ):
        transition = "NORMAL_TO_HIGH"

    elif (
        current_high == 1
        and
        future_high == 1
    ):
        transition = "HIGH_TO_HIGH"

    else:
        transition = "HIGH_TO_NORMAL"


    results.append({
        "obs_start_s":
            obs_start,

        "obs_end_s":
            obs_end,

        "future_start_s":
            future_start,

        "future_end_s":
            future_end,

        "current_high_ratio":
            current_high_ratio,

        "future_high_ratio":
            future_high_ratio,

        "current_high":
            current_high,

        "future_high":
            future_high,

        "transition":
            transition
    })

    start += STRIDE


# ==========================================
# Summary
# ==========================================

result_df = pd.DataFrame(results)

print()
print("=== Transition Analysis ===")
print()

print(
    "Total prediction samples =",
    len(result_df)
)

print()

counts = (
    result_df["transition"]
    .value_counts()
)

print(counts)

print()

normal_to_high = (
    result_df["transition"]
    == "NORMAL_TO_HIGH"
).sum()

print(
    "NORMAL -> HIGH samples =",
    normal_to_high
)

print(
    "NORMAL -> HIGH ratio =",
    f"{normal_to_high / len(result_df):.2%}"
)

print()


# ==========================================
# Save
# ==========================================

output = file.replace(
    ".csv",
    "_transition_analysis.csv"
)

result_df.to_csv(
    output,
    index=False
)

print(
    "Saved to:"
)

print(output)