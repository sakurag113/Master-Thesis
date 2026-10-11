#!/usr/bin/env python3

import pandas as pd
from pathlib import Path


INPUT_FILE = (
    Path.home()
    / "phase3"
    / "data"
    / "packet_stats"
    / "packet_snapshots.csv"
)

OUTPUT_FILE = (
    Path.home()
    / "phase3"
    / "data"
    / "packet_stats"
    / "packet_summary.csv"
)


df = pd.read_csv(INPUT_FILE)

df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)

rows = []


for run_name, run_df in df.groupby("run_name"):

    start_df = run_df[
        run_df["stage"] == "start"
    ]

    end_df = run_df[
        run_df["stage"] == "end"
    ]

    if start_df.empty or end_df.empty:
        print(
            f"Skipping {run_name}: "
            f"missing start or end snapshot"
        )
        continue

    start_time = start_df[
        "timestamp"
    ].min()

    end_time = end_df[
        "timestamp"
    ].max()

    duration_s = (
        end_time - start_time
    ).total_seconds()


    def get_delta(
        namespace,
        interface,
        column,
    ):

        start = start_df[
            (start_df["namespace"] == namespace)
            &
            (start_df["interface"] == interface)
        ]

        end = end_df[
            (end_df["namespace"] == namespace)
            &
            (end_df["interface"] == interface)
        ]

        if start.empty or end.empty:
            return None

        return int(
            end.iloc[0][column]
            -
            start.iloc[0][column]
        )


    h1_tx_packets = get_delta(
        "h1",
        "h1-eth0",
        "tx_packets",
    )

    h1_tx_bytes = get_delta(
        "h1",
        "h1-eth0",
        "tx_bytes",
    )

    spine_tx_packets = get_delta(
        "spine",
        "sp-l2",
        "tx_packets",
    )

    spine_tx_bytes = get_delta(
        "spine",
        "sp-l2",
        "tx_bytes",
    )

    h2_rx_packets = get_delta(
        "h2",
        "h2-eth0",
        "rx_packets",
    )

    h2_rx_bytes = get_delta(
        "h2",
        "h2-eth0",
        "rx_bytes",
    )


    if (
        duration_s > 0
        and
        spine_tx_packets is not None
    ):
        packet_rate = (
            spine_tx_packets
            / duration_s
        )
    else:
        packet_rate = None


    rows.append({

        "run_name":
            run_name,

        "duration_s":
            duration_s,

        "h1_tx_packets":
            h1_tx_packets,

        "h1_tx_bytes":
            h1_tx_bytes,

        "spine_tx_packets":
            spine_tx_packets,

        "spine_tx_bytes":
            spine_tx_bytes,

        "h2_rx_packets":
            h2_rx_packets,

        "h2_rx_bytes":
            h2_rx_bytes,

        "spine_packet_rate_pps":
            packet_rate,
    })


summary = pd.DataFrame(rows)

summary.to_csv(
    OUTPUT_FILE,
    index=False,
)

print()
print(summary.to_string(index=False))

print()
print(
    f"Saved to: {OUTPUT_FILE}"
)