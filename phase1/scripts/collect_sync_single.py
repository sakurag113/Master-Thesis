import subprocess
import csv
import time
import re
from datetime import datetime

OUTPUT = "/home/yuxsun/phase1/data/evpn_sync_singleflow.csv"
TARGET = "192.168.100.22"

INTERVAL = 0.2
DURATION = 30


def get_rtt():
    cmd = [
        "ip", "netns", "exec", "h1",
        "ping", "-c", "1", "-W", "1", TARGET
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    match = re.search(r"time=([0-9.]+)", result.stdout)

    if match:
        return float(match.group(1))

    return None


def get_overlimits():
    cmd = [
        "ip", "netns", "exec", "spine",
        "tc", "-s", "qdisc", "show", "dev", "sp-l2"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    match = re.search(r"overlimits\s+(\d+)", result.stdout)

    if match:
        return int(match.group(1))

    return None


with open(OUTPUT, "w", newline="") as f:
    writer = csv.writer(f)

    writer.writerow([
        "timestamp",
        "rtt_ms",
        "overlimits"
    ])

    start = time.time()

    while time.time() - start < DURATION:

        timestamp = datetime.now().isoformat(
            timespec="milliseconds"
        )

        rtt = get_rtt()
        overlimits = get_overlimits()

        writer.writerow([
            timestamp,
            rtt,
            overlimits
        ])

        f.flush()

        print(
            timestamp,
            "RTT =", rtt,
            "overlimits =", overlimits
        )

        time.sleep(INTERVAL)


print("Saved to:", OUTPUT)
