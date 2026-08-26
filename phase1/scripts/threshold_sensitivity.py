import pandas as pd
import numpy as np

# =========================
# Input files
# =========================

files = {
    "Baseline": "/home/yuxsun/phase1/data/evpn_sync_baseline.csv",
    "Single-flow": "/home/yuxsun/phase1/data/evpn_sync_singleflow.csv",
    "Dual-flow": "/home/yuxsun/phase1/data/evpn_sync_dualflow.csv"
}

# Candidate RTT thresholds in ms
RTT_THRESHOLDS = [
    0.1293,   # baseline p99
    10,
    25,
    50,
    75
]

# Candidate window-level spike ratios
RATIO_THRESHOLDS = [
    0.2,
    0.3,
    0.5
]

WINDOW_SECONDS = 2.0


def analyze_condition(file, condition):

    df = pd.read_csv(file)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df["time_s"] = (
        df["timestamp"] - df["timestamp"].iloc[0]
    ).dt.total_seconds()

    df["window_id"] = (
        df["time_s"] // WINDOW_SECONDS
    ).astype(int)

    results = []

    for rtt_threshold in RTT_THRESHOLDS:

        df["spike_sample"] = (
            df["rtt_ms"] > rtt_threshold
        )

        for ratio_threshold in RATIO_THRESHOLDS:

            high_latency_windows = 0
            total_windows = 0

            for _, group in df.groupby("window_id"):

                total_samples = len(group)

                if total_samples == 0:
                    continue

                spike_ratio = (
                    group["spike_sample"].sum()
                    / total_samples
                )

                total_windows += 1

                if spike_ratio >= ratio_threshold:
                    high_latency_windows += 1

            high_latency_ratio = (
                high_latency_windows / total_windows
                if total_windows > 0
                else 0
            )

            results.append({
                "condition": condition,
                "rtt_threshold_ms": rtt_threshold,
                "window_ratio_threshold": ratio_threshold,
                "high_latency_windows": high_latency_windows,
                "total_windows": total_windows,
                "high_latency_window_ratio": high_latency_ratio
            })

    return results


all_results = []

for condition, file in files.items():
    all_results.extend(
        analyze_condition(file, condition)
    )

results = pd.DataFrame(all_results)


# =========================
# Print detailed results
# =========================

print("\n=== Threshold Sensitivity Analysis ===\n")

for rtt_threshold in RTT_THRESHOLDS:

    print(
        f"\n--- RTT Threshold = "
        f"{rtt_threshold} ms ---"
    )

    subset = results[
        results["rtt_threshold_ms"]
        == rtt_threshold
    ]

    for ratio_threshold in RATIO_THRESHOLDS:

        print(
            f"\nWindow spike ratio >= "
            f"{int(ratio_threshold * 100)}%"
        )

        temp = subset[
            subset["window_ratio_threshold"]
            == ratio_threshold
        ]

        for _, row in temp.iterrows():

            print(
                f"{row['condition']:12s}: "
                f"{int(row['high_latency_windows'])}"
                f"/{int(row['total_windows'])} windows "
                f"("
                f"{row['high_latency_window_ratio']:.2%}"
                f")"
            )


# =========================
# Create pivot table
# =========================

pivot = results.pivot_table(
    index=[
        "rtt_threshold_ms",
        "window_ratio_threshold"
    ],
    columns="condition",
    values="high_latency_window_ratio"
)

print("\n\n=== Summary Table ===\n")
print(pivot)


# =========================
# Save results
# =========================

output_detail = (
    "/home/yuxsun/phase1/data/"
    "threshold_sensitivity.csv"
)

output_summary = (
    "/home/yuxsun/phase1/data/"
    "threshold_sensitivity_summary.csv"
)

results.to_csv(
    output_detail,
    index=False
)

pivot.to_csv(
    output_summary
)

print("\nSaved detailed results to:")
print(output_detail)

print("\nSaved summary table to:")
print(output_summary)