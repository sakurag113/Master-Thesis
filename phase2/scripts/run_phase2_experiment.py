import subprocess
import time
import csv
import re
import random
import os
import argparse
from datetime import datetime


# ==========================================
# Command-line arguments
# ==========================================

parser = argparse.ArgumentParser()

parser.add_argument(
    "--run-name",
    required=True,
    help="Name of this experiment run"
)

parser.add_argument(
    "--rate",
    type=int,
    required=True,
    help="Bottleneck rate in Mbit/s"
)

parser.add_argument(
    "--duration",
    type=int,
    default=90,
    help="Experiment duration in seconds"
)

parser.add_argument(
    "--seed",
    type=int,
    default=None,
    help="Random seed for reproducible traffic schedule"
)

args = parser.parse_args()


# ==========================================
# Configuration
# ==========================================

RUN_NAME = args.run_name

BOTTLENECK_RATE = args.rate

DURATION = args.duration

SAMPLE_INTERVAL = 0.2

TARGET_IP = "192.168.100.22"

DATA_DIR = "/home/yuxsun/phase2/data"

OUTPUT_CSV = (
    f"{DATA_DIR}/{RUN_NAME}.csv"
)

META_CSV = (
    f"{DATA_DIR}/{RUN_NAME}_metadata.csv"
)

FLOW_STATES = [
    0,
    1,
    2,
    3
]

MIN_STATE_DURATION = 8
MAX_STATE_DURATION = 18

INITIAL_BASELINE_MIN = 8
INITIAL_BASELINE_MAX = 15

IPERF_BASE_PORT = 5201

STATE_SWITCH_DELAY = 1.0


# ==========================================
# Random seed
# ==========================================

if args.seed is not None:

    random.seed(
        args.seed
    )


# ==========================================
# Basic command helper
# ==========================================

def run_cmd(cmd):

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )


# ==========================================
# Configure bottleneck
# ==========================================

def configure_bottleneck(
    rate_mbit
):

    cmd = [
        "ip",
        "netns",
        "exec",
        "spine",

        "tc",
        "qdisc",
        "replace",

        "dev",
        "sp-l2",

        "root",
        "tbf",

        "rate",
        f"{rate_mbit}mbit",

        "burst",
        "65536",

        "latency",
        "50ms"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        print()
        print(
            "Failed to configure bottleneck:"
        )

        print(
            result.stderr
        )

        raise RuntimeError(
            "Bottleneck configuration failed"
        )

    print()
    print(
        f"Bottleneck configured: "
        f"{rate_mbit} Mbit/s"
    )


# ==========================================
# RTT measurement
# ==========================================

def get_rtt():

    cmd = [
        "ip",
        "netns",
        "exec",
        "h1",

        "ping",
        "-c",
        "1",
        "-W",
        "1",

        TARGET_IP
    ]

    result = run_cmd(
        cmd
    )

    match = re.search(
        r"time=([0-9.]+)",
        result.stdout
    )

    if match:

        return float(
            match.group(1)
        )

    return None


# ==========================================
# TBF overlimits
# ==========================================

def get_overlimits():

    cmd = [
        "ip",
        "netns",
        "exec",
        "spine",

        "tc",
        "-s",
        "qdisc",
        "show",

        "dev",
        "sp-l2"
    ]

    result = run_cmd(
        cmd
    )

    match = re.search(
        r"overlimits\s+(\d+)",
        result.stdout
    )

    if match:

        return int(
            match.group(1)
        )

    return None


# ==========================================
# Start iperf3 servers
# ==========================================

def start_iperf_servers():

    processes = []

    for i in range(3):

        port = (
            IPERF_BASE_PORT + i
        )

        cmd = [
            "ip",
            "netns",
            "exec",
            "h2",

            "iperf3",
            "-s",

            "-p",
            str(port)
        ]

        p = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        processes.append(
            p
        )

    return processes


# ==========================================
# Start iperf3 clients
# ==========================================

def start_flows(
    flow_count
):

    processes = []

    for i in range(
        flow_count
    ):

        port = (
            IPERF_BASE_PORT + i
        )

        cmd = [
            "ip",
            "netns",
            "exec",
            "h1",

            "iperf3",
            "-c",
            TARGET_IP,

            "-p",
            str(port),

            "-t",
            "3600"
        ]

        p = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        processes.append(
            p
        )

    return processes


# ==========================================
# Stop processes safely
# ==========================================

def stop_processes(
    processes
):

    for p in processes:

        try:
            p.terminate()

        except Exception:
            pass

    for p in processes:

        try:
            p.wait(
                timeout=2
            )

        except Exception:

            try:
                p.kill()

            except Exception:
                pass


# ==========================================
# Count actually active flows
# ==========================================

def count_active_processes(
    processes
):

    active = 0

    for p in processes:

        if p.poll() is None:

            active += 1

    return active


# ==========================================
# Build randomized schedule
# ==========================================

def build_schedule():

    schedule = []

    # --------------------------------------
    # Initial baseline period
    # --------------------------------------

    first_duration = random.randint(
        INITIAL_BASELINE_MIN,
        INITIAL_BASELINE_MAX
    )

    schedule.append({
        "start": 0,
        "end": first_duration,
        "flows": 0
    })

    elapsed = first_duration

    previous_state = 0


    # --------------------------------------
    # Following randomized states
    # --------------------------------------

    while elapsed < DURATION:

        state_duration = random.randint(
            MIN_STATE_DURATION,
            MAX_STATE_DURATION
        )

        if (
            elapsed
            + state_duration
            > DURATION
        ):

            state_duration = (
                DURATION
                - elapsed
            )

        candidate_states = [
            state
            for state in FLOW_STATES
            if state != previous_state
        ]

        flow_count = random.choice(
            candidate_states
        )

        schedule.append({
            "start": elapsed,
            "end": elapsed + state_duration,
            "flows": flow_count
        })

        previous_state = (
            flow_count
        )

        elapsed += (
            state_duration
        )

    return schedule


# ==========================================
# Prepare directories
# ==========================================

os.makedirs(
    DATA_DIR,
    exist_ok=True
)


# ==========================================
# Configure bottleneck
# ==========================================

configure_bottleneck(
    BOTTLENECK_RATE
)


# ==========================================
# Build traffic schedule
# ==========================================

schedule = (
    build_schedule()
)


# ==========================================
# Print experiment information
# ==========================================

print()
print(
    "=== Phase 2 Pilot Experiment ==="
)

print()

print(
    "Run:",
    RUN_NAME
)

print(
    "Duration:",
    DURATION,
    "s"
)

print(
    "Bottleneck:",
    BOTTLENECK_RATE,
    "Mbit/s"
)

if args.seed is not None:

    print(
        "Random seed:",
        args.seed
    )

print()
print(
    "Traffic schedule:"
)

for item in schedule:

    print(
        f"{item['start']:5.1f} - "
        f"{item['end']:5.1f} s : "
        f"{item['flows']} flow(s)"
    )

print()


# ==========================================
# Save metadata
# ==========================================

with open(
    META_CSV,
    "w",
    newline=""
) as f:

    writer = csv.writer(
        f
    )

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
# Start iperf3 servers
# ==========================================

server_processes = (
    start_iperf_servers()
)

time.sleep(
    2
)


# ==========================================
# Main collection loop
# ==========================================

current_flows = []

current_state_index = -1


with open(
    OUTPUT_CSV,
    "w",
    newline=""
) as f:

    writer = csv.writer(
        f
    )

    writer.writerow([
        "timestamp",
        "time_s",
        "rtt_ms",
        "overlimits",
        "requested_flows",
        "active_flows",
        "bottleneck_mbit"
    ])

    experiment_start = (
        time.time()
    )

    while True:

        now = (
            time.time()
        )

        elapsed = (
            now
            - experiment_start
        )

        if elapsed >= DURATION:

            break


        # ----------------------------------
        # Find current schedule state
        # ----------------------------------

        state_index = None

        for i, item in enumerate(
            schedule
        ):

            if (
                elapsed
                >= item["start"]
                and
                elapsed
                < item["end"]
            ):

                state_index = i

                break


        if state_index is None:

            break


        # ==================================
        # Change traffic state
        # ==================================

        if (
            state_index
            != current_state_index
        ):

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


            # Stop previous clients

            stop_processes(
                current_flows
            )

            current_flows = []


            # Wait for old TCP sessions
            # and iperf processes to close

            time.sleep(
                STATE_SWITCH_DELAY
            )


            # Start new clients

            if requested_flows > 0:

                current_flows = (
                    start_flows(
                        requested_flows
                    )
                )

                # Allow processes to start

                time.sleep(
                    0.5
                )


            current_state_index = (
                state_index
            )


        # ==================================
        # Current flow information
        # ==================================

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
        # Collect telemetry
        # ==================================

        timestamp = (
            datetime.now()
            .isoformat(
                timespec="milliseconds"
            )
        )

        rtt = (
            get_rtt()
        )

        overlimits = (
            get_overlimits()
        )


        # ==================================
        # Save sample
        # ==================================

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


        # ==================================
        # Terminal output
        # ==================================

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


# ==========================================
# Finish
# ==========================================

print()
print(
    "=== Experiment finished ==="
)

print()

print(
    "Data saved to:"
)

print(
    OUTPUT_CSV
)

print()

print(
    "Metadata saved to:"
)

print(
    META_CSV
)