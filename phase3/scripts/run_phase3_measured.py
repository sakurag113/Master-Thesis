#!/usr/bin/env python3

import csv
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


# ============================================================
# Paths
# ============================================================

PHASE3_DIR = Path.home() / "phase3"

TRAFFIC_SCRIPT = (
    PHASE3_DIR
    / "scripts"
    / "run_online_traffic.py"
)

OUTPUT_DIR = (
    PHASE3_DIR
    / "data"
    / "packet_stats"
)

RUN_SUMMARY_FILE = (
    OUTPUT_DIR
    / "measured_runs.csv"
)

SNAPSHOT_FILE = (
    OUTPUT_DIR
    / "measured_snapshots.csv"
)


# ============================================================
# Monitor points
# ============================================================

MONITOR_POINTS = [
    ("h1", "h1-eth0"),
    ("spine", "sp-l2"),
    ("h2", "h2-eth0"),
]


# ============================================================
# Interface statistics
# ============================================================

def get_interface_stats(namespace, interface):

    cmd = [
        "sudo",
        "ip",
        "netns",
        "exec",
        namespace,
        "ip",
        "-s",
        "link",
        "show",
        interface,
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )

    lines = result.stdout.splitlines()

    rx_bytes = None
    rx_packets = None
    tx_bytes = None
    tx_packets = None

    for i, line in enumerate(lines):

        stripped = line.strip()

        if stripped.startswith("RX:"):

            values = lines[i + 1].split()

            rx_bytes = int(values[0])
            rx_packets = int(values[1])

        if stripped.startswith("TX:"):

            values = lines[i + 1].split()

            tx_bytes = int(values[0])
            tx_packets = int(values[1])

    if None in [
        rx_bytes,
        rx_packets,
        tx_bytes,
        tx_packets,
    ]:

        raise RuntimeError(
            f"Failed to parse interface stats: "
            f"{namespace}/{interface}"
        )

    return {
        "rx_bytes": rx_bytes,
        "rx_packets": rx_packets,
        "tx_bytes": tx_bytes,
        "tx_packets": tx_packets,
    }


# ============================================================
# Snapshot
# ============================================================

def take_snapshot():

    snapshot = {}

    for namespace, interface in MONITOR_POINTS:

        stats = get_interface_stats(
            namespace,
            interface,
        )

        key = f"{namespace}/{interface}"

        snapshot[key] = stats

    return snapshot


# ============================================================
# Save raw snapshot
# ============================================================

def save_snapshot(
    run_name,
    stage,
    timestamp,
    snapshot,
):

    write_header = not SNAPSHOT_FILE.exists()

    with SNAPSHOT_FILE.open(
        "a",
        newline="",
    ) as f:

        fieldnames = [
            "timestamp",
            "run_name",
            "stage",
            "namespace",
            "interface",
            "rx_bytes",
            "rx_packets",
            "tx_bytes",
            "tx_packets",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        if write_header:
            writer.writeheader()

        for namespace, interface in MONITOR_POINTS:

            key = f"{namespace}/{interface}"

            stats = snapshot[key]

            writer.writerow({
                "timestamp": timestamp,
                "run_name": run_name,
                "stage": stage,
                "namespace": namespace,
                "interface": interface,
                "rx_bytes": stats["rx_bytes"],
                "rx_packets": stats["rx_packets"],
                "tx_bytes": stats["tx_bytes"],
                "tx_packets": stats["tx_packets"],
            })


# ============================================================
# Calculate delta
# ============================================================

def delta(
    start_snapshot,
    end_snapshot,
    namespace,
    interface,
    field,
):

    key = f"{namespace}/{interface}"

    return (
        end_snapshot[key][field]
        -
        start_snapshot[key][field]
    )


# ============================================================
# Save run summary
# ============================================================

def save_summary(row):

    write_header = not RUN_SUMMARY_FILE.exists()

    with RUN_SUMMARY_FILE.open(
        "a",
        newline="",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=list(row.keys()),
        )

        if write_header:
            writer.writeheader()

        writer.writerow(row)


# ============================================================
# Main
# ============================================================

def main():

    if len(sys.argv) != 2:

        print()
        print(
            "Usage:"
        )

        print(
            "python3 run_phase3_measured.py "
            "<run_name>"
        )

        print()

        sys.exit(1)

    run_name = sys.argv[1]

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print(
        "=============================================="
    )

    print(
        " Phase 3 Measured Run"
    )

    print(
        "=============================================="
    )

    print(
        f"Run name: {run_name}"
    )

    print()

    # --------------------------------------------------------
    # Warm up sudo credentials
    # --------------------------------------------------------

    print(
        "Checking sudo access..."
    )

    subprocess.run(
        ["sudo", "-v"],
        check=True,
    )

    print(
        "sudo access OK."
    )

    print()

    # --------------------------------------------------------
    # Start snapshot
    # --------------------------------------------------------

    print(
        "Taking START packet snapshot..."
    )

    start_wall_time = datetime.now()
    start_monotonic = time.monotonic()

    start_snapshot = take_snapshot()

    save_snapshot(
        run_name,
        "start",
        start_wall_time.isoformat(),
        start_snapshot,
    )

    print(
        "START snapshot recorded."
    )

    print()

    # --------------------------------------------------------
    # Run traffic experiment
    # --------------------------------------------------------

    print(
        "Starting Phase 3 traffic experiment..."
    )

    print()

    traffic_return_code = None

    try:

        result = subprocess.run(
            [
                "python3",
                str(TRAFFIC_SCRIPT),
            ]
        )

        traffic_return_code = (
            result.returncode
        )

    except KeyboardInterrupt:

        print()
        print(
            "Experiment interrupted by user."
        )

        traffic_return_code = -1

    finally:

        # ----------------------------------------------------
        # End snapshot
        # ----------------------------------------------------

        end_monotonic = time.monotonic()
        end_wall_time = datetime.now()

        print()
        print(
            "Taking END packet snapshot..."
        )

        end_snapshot = take_snapshot()

        save_snapshot(
            run_name,
            "end",
            end_wall_time.isoformat(),
            end_snapshot,
        )

        print(
            "END snapshot recorded."
        )

    # --------------------------------------------------------
    # Duration
    # --------------------------------------------------------

    duration_s = (
        end_monotonic
        -
        start_monotonic
    )

    # --------------------------------------------------------
    # Important packet counters
    # --------------------------------------------------------

    h1_tx_packets = delta(
        start_snapshot,
        end_snapshot,
        "h1",
        "h1-eth0",
        "tx_packets",
    )

    h1_tx_bytes = delta(
        start_snapshot,
        end_snapshot,
        "h1",
        "h1-eth0",
        "tx_bytes",
    )

    spine_tx_packets = delta(
        start_snapshot,
        end_snapshot,
        "spine",
        "sp-l2",
        "tx_packets",
    )

    spine_tx_bytes = delta(
        start_snapshot,
        end_snapshot,
        "spine",
        "sp-l2",
        "tx_bytes",
    )

    h2_rx_packets = delta(
        start_snapshot,
        end_snapshot,
        "h2",
        "h2-eth0",
        "rx_packets",
    )

    h2_rx_bytes = delta(
        start_snapshot,
        end_snapshot,
        "h2",
        "h2-eth0",
        "rx_bytes",
    )

    # --------------------------------------------------------
    # Rates
    # --------------------------------------------------------

    if duration_s > 0:

        spine_packet_rate_pps = (
            spine_tx_packets
            /
            duration_s
        )

        spine_throughput_mbps = (
            spine_tx_bytes
            * 8
            /
            duration_s
            /
            1_000_000
        )

    else:

        spine_packet_rate_pps = 0.0
        spine_throughput_mbps = 0.0

    # --------------------------------------------------------
    # Delivery difference
    # --------------------------------------------------------

    packet_difference = (
        h1_tx_packets
        -
        h2_rx_packets
    )

    if h1_tx_packets > 0:

        delivery_ratio = (
            h2_rx_packets
            /
            h1_tx_packets
        )

    else:

        delivery_ratio = 0.0

    # --------------------------------------------------------
    # Summary row
    # --------------------------------------------------------

    row = {
        "run_name":
            run_name,

        "start_time":
            start_wall_time.isoformat(),

        "end_time":
            end_wall_time.isoformat(),

        "duration_s":
            round(duration_s, 3),

        "traffic_return_code":
            traffic_return_code,

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
            round(
                spine_packet_rate_pps,
                3,
            ),

        "spine_throughput_mbps":
            round(
                spine_throughput_mbps,
                3,
            ),

        "packet_difference_h1_h2":
            packet_difference,

        "delivery_ratio":
            round(
                delivery_ratio,
                6,
            ),
    }

    save_summary(row)

    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    print()
    print(
        "=============================================="
    )

    print(
        " Run Summary"
    )

    print(
        "=============================================="
    )

    print(
        f"Run              : {run_name}"
    )

    print(
        f"Duration         : "
        f"{duration_s:.2f} s"
    )

    print()

    print(
        f"h1 TX packets    : "
        f"{h1_tx_packets}"
    )

    print(
        f"spine TX packets : "
        f"{spine_tx_packets}"
    )

    print(
        f"h2 RX packets    : "
        f"{h2_rx_packets}"
    )

    print()

    print(
        f"spine packet rate: "
        f"{spine_packet_rate_pps:.2f} pkt/s"
    )

    print(
        f"spine throughput : "
        f"{spine_throughput_mbps:.2f} Mbit/s"
    )

    print()

    print(
        f"h1-h2 difference : "
        f"{packet_difference}"
    )

    print(
        f"delivery ratio   : "
        f"{delivery_ratio:.4f}"
    )

    print()

    print(
        "Saved summary:"
    )

    print(
        RUN_SUMMARY_FILE
    )

    print()

    print(
        "Saved raw snapshots:"
    )

    print(
        SNAPSHOT_FILE
    )

    print(
        "=============================================="
    )

    print()


if __name__ == "__main__":
    main()