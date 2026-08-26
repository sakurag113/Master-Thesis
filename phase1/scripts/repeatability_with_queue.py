import pandas as pd
import numpy as np
import os

# ==========================================
# Configuration
# ==========================================

RTT_THRESHOLD = 75
WINDOW_SECONDS = 2
RATIO_THRESHOLD = 0.5

files = {
    "Single-flow Run 1":
        "/home/yuxsun/phase1/data/evpn_sync_singleflow.csv",

    "Single-flow Run 2":
        "/home/yuxsun/phase1/data/evpn_sync_singleflow_run2.csv",

    "Single-flow Run 3":
        "/home/yuxsun/phase1/data/evpn_sync_singleflow_run3.csv",

    "Dual-flow Run 1":
        "/home/yuxsun/phase1/data/evpn_sync_dualflow.csv",

    "Dual-flow Run 2":
        "/home/yuxsun/phase1/data/evpn_sync_dualflow_run2.csv",

    "Dual-flow Run 3":
        "/home/yuxsun/phase1/data/evpn_sync_dualflow_run3.csv"
}


# ==========================================
# Analyze one run
# ==========================================

def analyze_run(file, run_name):

    if not os.path.exists(file):
        print("Missing file:", file)
        return None, None

    df = pd.read_csv(file)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Relative time
    df["time_s"] = (
        df["timestamp"] -
        df["timestamp"].iloc[0]
    ).dt.total_seconds()

    # Sampling interval
    df["delta_t"] = (
        df["time_s"]
        .diff()
    )

    # Change in cumulative overlimits counter
    df["delta_overlimits"] = (
        df["overlimits"]
        .diff()
        .fillna(0)
    )

    # Protect against counter reset
    df.loc[
        df["delta_overlimits"] < 0,
        "delta_overlimits"
    ] = 0

    # Overlimits increase rate per second
    df["overlimits_rate"] = (
        df["delta_overlimits"] /
        df["delta_t"]
    )

    df["overlimits_rate"] = (
        df["overlimits_rate"]
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
    )

    # Assign samples to 2-second windows
    df["window_id"] = (
        df["time_s"] //
        WINDOW_SECONDS
    ).astype(int)

    # Candidate high-latency sample
    df["high_sample"] = (
        df["rtt_ms"] >
        RTT_THRESHOLD
    )

    window_results = []

    for window_id, group in df.groupby("window_id"):

        spike_ratio = (
            group["high_sample"].mean()
        )

        is_high = (
            spike_ratio >=
            RATIO_THRESHOLD
        )

        result = {
            "run": run_name,

            "window_id": window_id,

            "start_time_s":
                window_id * WINDOW_SECONDS,

            "end_time_s":
                (window_id + 1) * WINDOW_SECONDS,

            "mean_rtt_ms":
                group["rtt_ms"].mean(),

            "max_rtt_ms":
                group["rtt_ms"].max(),

            "spike_ratio":
                spike_ratio,

            "high_latency":
                int(is_high),

            "mean_delta_overlimits":
                group["delta_overlimits"].mean(),

            "max_delta_overlimits":
                group["delta_overlimits"].max(),

            "mean_overlimits_rate":
                group["overlimits_rate"].mean(),

            "max_overlimits_rate":
                group["overlimits_rate"].max()
        }

        window_results.append(result)

    window_df = pd.DataFrame(window_results)

    # ------------------------------------------
    # Run-level summary
    # ------------------------------------------

    high_windows = window_df[
        window_df["high_latency"] == 1
    ]

    normal_windows = window_df[
        window_df["high_latency"] == 0
    ]

    run_summary = {
        "run":
            run_name,

        "total_windows":
            len(window_df),

        "high_windows":
            window_df["high_latency"].sum(),

        "high_latency_ratio":
            window_df["high_latency"].mean(),

        "all_mean_overlimits_rate":
            window_df["mean_overlimits_rate"].mean(),

        "all_max_overlimits_rate":
            window_df["max_overlimits_rate"].max(),

        "high_window_mean_overlimits_rate":
            (
                high_windows[
                    "mean_overlimits_rate"
                ].mean()
                if len(high_windows) > 0
                else np.nan
            ),

        "normal_window_mean_overlimits_rate":
            (
                normal_windows[
                    "mean_overlimits_rate"
                ].mean()
                if len(normal_windows) > 0
                else np.nan
            )
    }

    return window_df, run_summary


# ==========================================
# Run all experiments
# ==========================================

all_windows = []
run_summaries = []

for run_name, file in files.items():

    windows, summary = analyze_run(
        file,
        run_name
    )

    if windows is not None:
        all_windows.append(windows)

    if summary is not None:
        run_summaries.append(summary)


windows_df = pd.concat(
    all_windows,
    ignore_index=True
)

summary_df = pd.DataFrame(
    run_summaries
)


# ==========================================
# Print run-level results
# ==========================================

print()
print("=== Queue-aware Repeatability Analysis ===")
print()

columns = [
    "run",
    "high_latency_ratio",
    "all_mean_overlimits_rate",
    "all_max_overlimits_rate",
    "high_window_mean_overlimits_rate",
    "normal_window_mean_overlimits_rate"
]

print(
    summary_df[columns]
    .to_string(index=False)
)


# ==========================================
# Group summary
# ==========================================

summary_df["condition"] = np.where(
    summary_df["run"].str.startswith("Single"),
    "Single-flow",
    "Dual-flow"
)

print()
print("=== Group Summary ===")
print()

for condition in [
    "Single-flow",
    "Dual-flow"
]:

    group = summary_df[
        summary_df["condition"] == condition
    ]

    print(condition)

    print(
        "Mean high-latency ratio =",
        f"{group['high_latency_ratio'].mean():.2%}"
    )

    print(
        "Mean overlimits rate "
        "(all windows) =",
        f"{group['all_mean_overlimits_rate'].mean():.2f}/s"
    )

    print(
        "Mean overlimits rate "
        "(HIGH windows) =",
        f"{group['high_window_mean_overlimits_rate'].mean():.2f}/s"
    )

    print(
        "Mean overlimits rate "
        "(normal windows) =",
        f"{group['normal_window_mean_overlimits_rate'].mean():.2f}/s"
    )

    print()


# ==========================================
# Compare HIGH vs normal windows globally
# ==========================================

high = windows_df[
    windows_df["high_latency"] == 1
]

normal = windows_df[
    windows_df["high_latency"] == 0
]

print("=== HIGH vs Normal Windows ===")
print()

print(
    "HIGH windows mean overlimits rate =",
    f"{high['mean_overlimits_rate'].mean():.2f}/s"
)

print(
    "Normal windows mean overlimits rate =",
    f"{normal['mean_overlimits_rate'].mean():.2f}/s"
)


# ==========================================
# Save outputs
# ==========================================

window_output = (
    "/home/yuxsun/phase1/data/"
    "queue_window_analysis.csv"
)

summary_output = (
    "/home/yuxsun/phase1/data/"
    "queue_repeatability_summary.csv"
)

windows_df.to_csv(
    window_output,
    index=False
)

summary_df.to_csv(
    summary_output,
    index=False
)

print()
print("Saved window-level results to:")
print(window_output)

print()
print("Saved run-level summary to:")
print(summary_output)