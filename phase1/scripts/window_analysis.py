import pandas as pd
import numpy as np

# -------------------------
# Configuration
# -------------------------

baseline_file = "/home/yuxsun/phase1/data/evpn_sync_baseline.csv"
single_file = "/home/yuxsun/phase1/data/evpn_sync_singleflow.csv"
dual_file = "/home/yuxsun/phase1/data/evpn_sync_dualflow.csv"

# Combined baseline p99 from previous analysis
RTT_THRESHOLD = 0.1293

# Analyze latency in 2-second windows
WINDOW_SECONDS = 2.0

# Candidate ratios for defining a high-latency window
RATIO_THRESHOLDS = [0.2, 0.3, 0.5]


def load_data(file):
    df = pd.read_csv(file)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df["time_s"] = (
        df["timestamp"] - df["timestamp"].iloc[0]
    ).dt.total_seconds()

    # Mark each RTT sample as above/below the candidate threshold
    df["spike_sample"] = df["rtt_ms"] > RTT_THRESHOLD

    return df


def analyze_windows(file, condition):
    df = load_data(file)

    # Assign each sample to a 2-second window
    df["window_id"] = (
        df["time_s"] // WINDOW_SECONDS
    ).astype(int)

    results = []

    for window_id, group in df.groupby("window_id"):

        total_samples = len(group)
        spike_samples = group["spike_sample"].sum()

        spike_ratio = (
            spike_samples / total_samples
            if total_samples > 0 else 0
        )

        result = {
            "condition": condition,
            "window_id": window_id,
            "start_time_s": window_id * WINDOW_SECONDS,
            "end_time_s": (window_id + 1) * WINDOW_SECONDS,
            "samples": total_samples,
            "mean_rtt_ms": group["rtt_ms"].mean(),
            "max_rtt_ms": group["rtt_ms"].max(),
            "spike_samples": spike_samples,
            "spike_ratio": spike_ratio
        }

        # Test several candidate high-latency definitions
        for ratio_threshold in RATIO_THRESHOLDS:
            name = f"high_latency_{int(ratio_threshold * 100)}pct"

            result[name] = int(
                spike_ratio >= ratio_threshold
            )

        results.append(result)

    return pd.DataFrame(results)


baseline = analyze_windows(
    baseline_file,
    "Baseline"
)

single = analyze_windows(
    single_file,
    "Single-flow"
)

dual = analyze_windows(
    dual_file,
    "Dual-flow"
)

all_results = pd.concat(
    [baseline, single, dual],
    ignore_index=True
)

print("\n=== Window-level Analysis ===\n")

print(
    all_results[
        [
            "condition",
            "start_time_s",
            "end_time_s",
            "mean_rtt_ms",
            "max_rtt_ms",
            "spike_ratio",
            "high_latency_20pct",
            "high_latency_30pct",
            "high_latency_50pct"
        ]
    ].to_string(index=False)
)

print("\n=== Summary ===\n")

for condition in [
    "Baseline",
    "Single-flow",
    "Dual-flow"
]:
    subset = all_results[
        all_results["condition"] == condition
    ]

    print(condition)

    print(
        "  total windows =",
        len(subset)
    )

    for ratio_threshold in RATIO_THRESHOLDS:
        column = (
            f"high_latency_"
            f"{int(ratio_threshold * 100)}pct"
        )

        count = subset[column].sum()

        ratio = count / len(subset)

        print(
            f"  >= {int(ratio_threshold * 100)}% spike ratio:",
            count,
            "windows,",
            f"{ratio:.2%}"
        )

    print()

output = (
    "/home/yuxsun/phase1/data/"
    "window_analysis.csv"
)

all_results.to_csv(
    output,
    index=False
)

print("Saved to:")
print(output)