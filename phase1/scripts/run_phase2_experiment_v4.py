import subprocess
import time
import csv
import re
import random
import os
import argparse
from datetime import datetime


# ==========================================
# Arguments
# ==========================================

parser = argparse.ArgumentParser()

parser.add_argument(
    "--run-name",
    required=True
)

parser.add_argument(
    "--rate",
    type=int,
    required=True
)

parser.add_argument(
    "--duration",
    type=int,
    default=120
)

parser.add_argument(
    "--seed",
    type=int,
    default=None
)

args = parser.parse_args()


# ==========================================
# Configuration
# ==========================================

RUN_NAME = args.run_name
BOTTLENECK_RATE = args.rate
DURATION = args.duration

TARGET_IP = "192.168.100.22"

DATA_DIR = "/home/yuxsun/phase2/data"

OUTPUT_CSV = f"{DATA_DIR}/{RUN_NAME}.csv"
META_CSV = f"{DATA_DIR}/{RUN_NAME}_metadata.csv"

SAMPLE_INTERVAL = 0.2
STATE_SWITCH_DELAY = 1.0

IPERF_BASE_PORT = 5201

# Shorter cycles to create more transitions
BASELINE_MIN = 5
BASELINE_MAX = 8

HEAVY_MIN = 6
HEAVY_MAX = 9

RECOVERY_MIN = 5
RECOVERY_MAX = 8

HEAVY_FLOW_CHOICES = [2, 3]


if args.seed is not None:
    random.seed(args.seed)


# ==========================================
# Helpers
# ==========================================

def run_cmd(cmd):
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )


def configure_bottleneck(rate_mbit):

    cmd = [
        "ip", "netns", "exec", "spine",
        "tc", "qdisc", "replace",
        "dev", "sp-l2",
        "root", "tbf",
        "rate", f"{rate_mbit}mbit",
        "burst", "65536",
        "latency", "50ms"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("Failed to configure bottleneck:")
        print(result.stderr)
        raise RuntimeError(
            "Bottleneck configuration failed"
        )

    print(
        f"Bottleneck configured: "
        f"{rate_mbit} Mbit/s"
    )


def get_rtt():

    cmd = [
        "ip", "netns", "exec", "h1",
        "ping", "-c", "1", "-W", "1",
        TARGET_IP
    ]

    result = run_cmd(cmd)

    match = re.search(
        r"time=([0-9.]+)",
        result.stdout
    )

    if match:
        return float(match.group(1))

    return None


def get_overlimits():

    cmd = [
        "ip", "netns", "exec", "spine",
        "tc", "-s", "qdisc",
        "show", "dev", "sp-l2"
    ]

    result = run_cmd(cmd)

    match = re.search(
        r"overlimits\s+(\d+)",
        result.stdout
    )

    if match:
        return int(match.group(1))

    return None


# ==========================================
# iperf servers / clients
# ==========================================

def start_iperf_servers():

    processes = []

    for i in range(3):

        port = IPERF_BASE_PORT + i

        cmd = [
            "ip", "netns", "exec", "h2",
            "iperf3",
            "-s",
            "-p", str(port)
        ]

        p = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        processes.append(p)

    return processes


def start_flows(flow_count):

    processes = []

    for i in range(flow_count):

        port = IPERF_BASE_PORT + i

        cmd = [
            "ip", "netns", "exec", "h1",
            "iperf3",
            "-c", TARGET_IP,
            "-p", str(port),
            "-t", "3600"
        ]

        p = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        processes.append(p)

    return processes


def stop_processes(processes):

    for p in processes:
        try:
            p.terminate()
        except Exception:
            pass

    for p in processes:
        try:
            p.wait(timeout=2)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass


def count_active_processes(processes):

    return sum(
        1
        for p in processes
        if p.poll() is None
    )


# ==========================================
# Schedule
# ==========================================

def add_state(
    schedule,
    start,
    duration,
    flows
):

    end = min(
        start + duration,
        DURATION
    )

    if end <= start:
        return start

    schedule.append({
        "start": start,
        "end": end,
        "flows": flows
    })

    return end


def build_schedule():

    schedule = []

    elapsed = 0.0

    # Initial baseline
    elapsed = add_state(
        schedule,
        elapsed,
        random.randint(
            BASELINE_MIN,
            BASELINE_MAX
        ),
        0
    )

    # Repeated transition cycles:
    # 0 -> heavy -> 0 -> heavy -> ...

    while elapsed < DURATION:

        # Heavy load
        heavy_flows = random.choice(
            HEAVY_FLOW_CHOICES
        )

        elapsed = add_state(
            schedule,
            elapsed,
            random.randint(
                HEAVY_MIN,
                HEAVY_MAX
            ),
            heavy_flows
        )

        if elapsed >= DURATION:
            break

        # Recovery / normal
        elapsed = add_state(
            schedule,
            elapsed,
            random.randint(
                RECOVERY_MIN,
                RECOVERY_MAX
            ),
            0
        )

    return schedule


# ==========================================
# Setup
# ==========================================

os.makedirs(
    DATA_DIR,
    exist_ok=True
)

configure_bottleneck(
    BOTTLENECK_RATE
)

schedule = build_schedule()


# ==========================================
# Print schedule
# ==========================================

print()
print(
    "=== Phase 2 Transition-focused "
    "Experiment v4 ==="
)
print()

print("Run:", RUN_NAME)
print("Duration:", DURATION, "s")
print(
    "Bottleneck:",
    BOTTLENECK_RATE,
    "Mbit/s"
)
print("Seed:", args.seed)

print()
print("Traffic schedule:")

for item in schedule:

    print(
        f"{item['start']:6.1f} - "
        f"{item['end']:6.1f} s : "
        f"{item['flows']} flow(s)"
    )


# ==========================================
# Save metadata
# ==========================================

with open(
    META_CSV,
    "w",
    newline=""
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "run",
        "bottleneck_mbit",
        "start_s",
        "end_s",
        "requested_flows"
    ])

    for item in schedule:

        writer.writerow([
            RUN_NAME,
            BOTTLENECK_RATE,
            item["start"],
            item["end"],
            item["flows"]
        ])


# ==========================================
# Start servers
# ==========================================

server_processes = (
    start_iperf_servers()
)

time.sleep(2)


# ==========================================
# Main experiment
# ==========================================

current_flows = []
current_state_index = -1


with open(
    OUTPUT_CSV,
    "w",
    newline=""
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "timestamp",
        "time_s",
        "rtt_ms",
        "overlimits",
        "requested_flows",
        "active_flows",
        "bottleneck_mbit"
    ])

    experiment_start = time.time()

    while True:

        elapsed = (
            time.time()
            - experiment_start
        )

        if elapsed >= DURATION:
            break

        state_index = None

        for i, item in enumerate(schedule):

            if (
                elapsed >= item["start"]
                and
                elapsed < item["end"]
            ):

                state_index = i
                break

        if state_index is None:
            break


        # ==================================
        # State change
        # ==================================

        if state_index != current_state_index:

            requested_flows = (
                schedule[
                    state_index
                ]["flows"]
            )

            print()
            print(
                f"[{elapsed:6.2f}s] "
                f"Switching to "
                f"{requested_flows} flow(s)"
            )

            stop_processes(
                current_flows
            )

            current_flows = []

            time.sleep(
                STATE_SWITCH_DELAY
            )

            if requested_flows > 0:

                current_flows = (
                    start_flows(
                        requested_flows
                    )
                )

                time.sleep(0.5)

            current_state_index = (
                state_index
            )


        requested_flows = (
            schedule[
                state_index
            ]["flows"]
        )

        active_flows = (
            count_active_processes(
                current_flows
            )
        )


        # ==================================
        # Telemetry
        # ==================================

        timestamp = (
            datetime.now()
            .isoformat(
                timespec="milliseconds"
            )
        )

        rtt = get_rtt()
        overlimits = get_overlimits()


        writer.writerow([
            timestamp,
            elapsed,
            rtt,
            overlimits,
            requested_flows,
            active_flows,
            BOTTLENECK_RATE
        ])

        f.flush()

        print(
            f"{elapsed:6.2f}s",
            "| requested =",
            requested_flows,
            "| active =",
            active_flows,
            "| RTT =",
            rtt,
            "| overlimits =",
            overlimits
        )

        time.sleep(
            SAMPLE_INTERVAL
        )


# ==========================================
# Cleanup
# ==========================================

stop_processes(
    current_flows
)

stop_processes(
    server_processes
)


print()
print(
    "=== Experiment finished ==="
)

print()
print(
    "Data saved to:"
)
print(OUTPUT_CSV)

print()
print(
    "Metadata saved to:"
)
print(META_CSV)