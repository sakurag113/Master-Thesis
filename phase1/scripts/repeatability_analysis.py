import pandas as pd
import numpy as np
import os

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


def analyze_run(file, name):

    if not os.path.exists(file):
        print("Missing file:", file)
        return None

    df = pd.read_csv(file)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df["time_s"] = (
        df["timestamp"] - df["timestamp"].iloc[0]
    ).dt.total_seconds()

    df["window_id"] = (
        df["time_s"] // WINDOW_SECONDS
    ).astype(int)

    df["high_sample"] = (
        df["rtt_ms"] > RTT_THRESHOLD
    )

    total_windows = 0
    high_windows = 0

    for _, group in df.groupby("window_id"):

        spike_ratio = group["high_sample"].mean()

        total_windows += 1

        if spike_ratio >= RATIO_THRESHOLD:
            high_windows += 1

    high_window_ratio = (
        high_windows / total_windows
        if total_windows > 0
        else 0
    )

    return {
        "run": name,
        "high_windows": high_windows,
        "total_windows": total_windows,
        "high_latency_ratio": high_window_ratio
    }


results = []

for name, file in files.items():

    result = analyze_run(file, name)

    if result is not None:
        results.append(result)


results_df = pd.DataFrame(results)

print()
print("=== Repeatability Analysis ===")
print()

print(
    results_df.to_string(
        index=False
    )
)

print()
print("=== Group Summary ===")
print()


single = results_df[
    results_df["run"].str.startswith("Single")
]

dual = results_df[
    results_df["run"].str.startswith("Dual")
]


def print_summary(df, name):

    values = df["high_latency_ratio"]

    print(name)
    print(
        "Runs:",
        [
            f"{x:.2%}"
            for x in values
        ]
    )

    print(
        "Mean high-latency ratio =",
        f"{values.mean():.2%}"
    )

    print(
        "Std =",
        f"{values.std(ddof=1):.2%}"
    )

    print(
        "Min =",
        f"{values.min():.2%}"
    )

    print(
        "Max =",
        f"{values.max():.2%}"
    )

    print()


print_summary(
    single,
    "Single-flow"
)

print_summary(
    dual,
    "Dual-flow"
)


difference = (
    dual["high_latency_ratio"].mean()
    -
    single["high_latency_ratio"].mean()
)

print(
    "Difference in mean ratio "
    "(Dual - Single) =",
    f"{difference:.2%}"
)


output = (
    "/home/yuxsun/phase1/data/"
    "repeatability_analysis.csv"
)

results_df.to_csv(
    output,
    index=False
)

print()
print("Saved to:")
print(output)