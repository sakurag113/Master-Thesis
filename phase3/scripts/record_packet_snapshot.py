#!/usr/bin/env python3

import csv
import subprocess
import sys
from datetime import datetime
from pathlib import Path


MONITOR_POINTS = [
    ("h1", "h1-eth0"),
    ("spine", "sp-l2"),
    ("h2", "h2-eth0"),
]


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

        if line.strip().startswith("RX:"):
            values = lines[i + 1].split()

            rx_bytes = int(values[0])
            rx_packets = int(values[1])

        if line.strip().startswith("TX:"):
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
            f"Failed to parse {namespace}/{interface}"
        )

    return {
        "rx_bytes": rx_bytes,
        "rx_packets": rx_packets,
        "tx_bytes": tx_bytes,
        "tx_packets": tx_packets,
    }


def main():

    if len(sys.argv) != 3:
        print(
            "Usage: python3 record_packet_snapshot.py "
            "<run_name> <start|end>"
        )
        sys.exit(1)

    run_name = sys.argv[1]
    stage = sys.argv[2]

    if stage not in ["start", "end"]:
        print("Stage must be start or end")
        sys.exit(1)

    output_dir = (
        Path.home()
        / "phase3"
        / "data"
        / "packet_stats"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        output_dir
        / "packet_snapshots.csv"
    )

    write_header = not output_file.exists()

    with output_file.open(
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

            stats = get_interface_stats(
                namespace,
                interface,
            )

            row = {
                "timestamp":
                    datetime.now().isoformat(),

                "run_name":
                    run_name,

                "stage":
                    stage,

                "namespace":
                    namespace,

                "interface":
                    interface,

                **stats,
            }

            writer.writerow(row)

            print(
                f"{namespace:6s} "
                f"{interface:10s} "
                f"RX={stats['rx_packets']} "
                f"TX={stats['tx_packets']}"
            )

    print()
    print(
        f"Recorded {stage} snapshot "
        f"for {run_name}"
    )

    print(
        f"Saved to: {output_file}"
    )


if __name__ == "__main__":
    main()