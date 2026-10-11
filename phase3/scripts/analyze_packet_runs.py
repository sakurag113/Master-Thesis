#!/usr/bin/env python3

import pandas as pd
from pathlib import Path


PHASE3_DIR = Path.home() / "phase3"

INPUT_FILE = (
    PHASE3_DIR
    / "data"
    / "packet_stats"
    / "measured_runs.csv"
)

OUTPUT_FILE = (
    PHASE3_DIR
    / "data"
    / "packet_stats"
    / "paper_packet_statistics.csv"
)


def main():

    df = pd.read_csv(INPUT_FILE)

    # Only use successfully completed experiments
    df = df[
        df["traffic_return_code"] == 0
    ].copy()

    if df.empty:
        print("No successful runs found.")
        return

    metrics = [
        "duration_s",
        "h1_tx_packets",
        "spine_tx_packets",
        "h2_rx_packets",
        "spine_packet_rate_pps",
        "spine_throughput_mbps",
        "delivery_ratio",
    ]

    rows = []

    for metric in metrics:

        series = df[metric].dropna()

        rows.append({
            "metric": metric,
            "n_runs": len(series),
            "mean": series.mean(),
            "std": series.std(),
            "median": series.median(),
            "min": series.min(),
            "max": series.max(),
        })

    result = pd.DataFrame(rows)

    result.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("==========================================")
    print(" Phase 3 Packet Statistics")
    print("==========================================")
    print()

    print(
        result.to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}",
        )
    )

    print()
    print(
        f"Number of successful runs = {len(df)}"
    )

    print()
    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()