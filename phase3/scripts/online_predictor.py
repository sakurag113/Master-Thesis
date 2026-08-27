#!/usr/bin/env python3

import os
import re
import time
import csv
import subprocess
from collections import deque

import joblib
import numpy as np
import pandas as pd


# ============================================================
# Phase 3 paths
# ============================================================

MODEL_FILE = (
    "/home/yuxsun/phase3/models/"
    "online_rf_queue_traffic.joblib"
)

LOG_DIR = "/home/yuxsun/phase3/logs"

LOG_FILE = (
    "/home/yuxsun/phase3/logs/"
    "online_prediction_log_v2.csv"
)

os.makedirs(
    LOG_DIR,
    exist_ok=True
)


# ============================================================
# Network configuration
# ============================================================

SPINE_NS = "spine"
BOTTLENECK_DEV = "sp-l2"

H1_NS = "h1"

IPERF_SERVER_IP = "192.168.100.22"
IPERF_SERVER_PORT = 5201

# Make sure this matches the current TBF bottleneck
BOTTLENECK_MBIT = 10.0


# ============================================================
# Online prediction configuration
# ============================================================

OBSERVATION_WINDOW = 2.0

SAMPLE_INTERVAL = 0.2

PREDICTION_INTERVAL = 1.0

WARNING_THRESHOLD = 0.50


# ============================================================
# Feature list
# ============================================================

FEATURES = [
    "bottleneck_mbit",
    "requested_flows_mean",
    "active_flows_mean",
    "mean_overlimits_rate",
    "max_overlimits_rate",
    "std_overlimits_rate",
    "overlimits_rate_slope"
]


# ============================================================
# Helper: run shell command
# ============================================================

def run_command(cmd):

    try:

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=3
        )

        return result.stdout

    except Exception:

        return ""


# ============================================================
# Read TBF overlimits counter
# ============================================================

def get_overlimits():

    cmd = (
        f"sudo ip netns exec {SPINE_NS} "
        f"tc -s qdisc show dev {BOTTLENECK_DEV}"
    )

    output = run_command(cmd)

    match = re.search(
        r"overlimits\s+(\d+)",
        output
    )

    if match:

        return int(
            match.group(1)
        )

    return None


# ============================================================
# Count active iperf3 TCP flows
#
# Instead of using pgrep, inspect established TCP
# connections inside h1's network namespace.
# ============================================================

def get_active_flows():

    cmd = (
        f"sudo ip netns exec {H1_NS} "
        f"ss -tnH state established"
    )

    output = run_command(cmd)

    target = (
        f"{IPERF_SERVER_IP}:"
        f"{IPERF_SERVER_PORT}"
    )

    connections = 0

    for line in output.splitlines():

        if target in line:
            connections += 1

    # iperf3 -P N normally creates
    # N data connections + 1 control connection
    if connections == 0:
        return 0

    return max(
        connections - 1,
        0
    )


# ============================================================
# Calculate linear slope
# ============================================================

def calculate_slope(times, values):

    if len(values) < 2:

        return 0.0

    x = np.array(
        times,
        dtype=float
    )

    y = np.array(
        values,
        dtype=float
    )

    x = x - x[0]

    if np.allclose(
        x,
        0
    ):

        return 0.0

    slope = np.polyfit(
        x,
        y,
        1
    )[0]

    return float(
        slope
    )


# ============================================================
# Load model
# ============================================================

print()
print(
    "=== Phase 3 Online Predictor V2 ==="
)
print()

print(
    "Loading model:"
)

print(
    MODEL_FILE
)

model = joblib.load(
    MODEL_FILE
)

print()
print(
    "Model loaded successfully."
)

print(
    f"Observation window = "
    f"{OBSERVATION_WINDOW:.1f} s"
)

print(
    f"Prediction interval = "
    f"{PREDICTION_INTERVAL:.1f} s"
)

print(
    f"Warning threshold = "
    f"{WARNING_THRESHOLD:.2f}"
)

print(
    f"Bottleneck = "
    f"{BOTTLENECK_MBIT:.1f} Mbit/s"
)

print()


# ============================================================
# Rolling buffer
# ============================================================

buffer = deque()

previous_overlimits = None
previous_timestamp = None

start_time = time.monotonic()

last_prediction_time = (
    -PREDICTION_INTERVAL
)


# ============================================================
# Open CSV log
# ============================================================

csv_file = open(
    LOG_FILE,
    "w",
    newline=""
)

writer = csv.writer(
    csv_file
)

writer.writerow([
    "timestamp",
    "time_s",
    "bottleneck_mbit",
    "active_flows",
    "overlimits",
    "overlimits_rate",
    "mean_overlimits_rate",
    "max_overlimits_rate",
    "std_overlimits_rate",
    "overlimits_rate_slope",
    "future_high_probability",
    "prediction"
])


print(
    " time(s) | flows | overlimits/s | risk  | state"
)

print(
    "------------------------------------------------"
)


# ============================================================
# Main loop
# ============================================================

try:

    while True:

        now = time.monotonic()

        elapsed = (
            now
            - start_time
        )


        # ----------------------------------------------------
        # Read live telemetry
        # ----------------------------------------------------

        overlimits = get_overlimits()

        active_flows = get_active_flows()


        # ----------------------------------------------------
        # Calculate overlimits rate
        # ----------------------------------------------------

        overlimits_rate = 0.0

        if (
            previous_overlimits is not None
            and
            overlimits is not None
            and
            previous_timestamp is not None
        ):

            dt = (
                now
                - previous_timestamp
            )

            delta = (
                overlimits
                - previous_overlimits
            )

            if (
                dt > 0
                and
                delta >= 0
            ):

                overlimits_rate = (
                    delta / dt
                )


        if overlimits is not None:

            previous_overlimits = (
                overlimits
            )

            previous_timestamp = (
                now
            )


        # ----------------------------------------------------
        # Save raw live sample in rolling buffer
        # ----------------------------------------------------

        sample = {
            "time":
                elapsed,

            "active_flows":
                active_flows,

            "overlimits_rate":
                overlimits_rate
        }

        buffer.append(
            sample
        )


        # ----------------------------------------------------
        # Keep only last 2 seconds
        # ----------------------------------------------------

        while (
            buffer
            and
            (
                elapsed
                - buffer[0]["time"]
                > OBSERVATION_WINDOW
            )
        ):

            buffer.popleft()


        # ----------------------------------------------------
        # Run prediction approximately every 1 second
        # ----------------------------------------------------

        if (
            elapsed
            - last_prediction_time
            >= PREDICTION_INTERVAL
        ):

            last_prediction_time = (
                elapsed
            )


            # Need a full observation history
            if (
                elapsed
                < OBSERVATION_WINDOW
                or
                len(buffer) < 3
            ):

                time.sleep(
                    SAMPLE_INTERVAL
                )

                continue


            # ------------------------------------------------
            # Extract rolling-window values
            # ------------------------------------------------

            times = [
                item["time"]
                for item in buffer
            ]

            flow_values = [
                item["active_flows"]
                for item in buffer
            ]

            rate_values = [
                item["overlimits_rate"]
                for item in buffer
            ]


            # ------------------------------------------------
            # Calculate Phase 2 compatible features
            # ------------------------------------------------

            mean_flows = float(
                np.mean(
                    flow_values
                )
            )

            mean_rate = float(
                np.mean(
                    rate_values
                )
            )

            max_rate = float(
                np.max(
                    rate_values
                )
            )

            std_rate = float(
                np.std(
                    rate_values
                )
            )

            rate_slope = (
                calculate_slope(
                    times,
                    rate_values
                )
            )


            # ------------------------------------------------
            # Build model input
            #
            # During Phase 2, requested_flows and active_flows
            # matched in the final dataset.
            #
            # For this first online test, use measured active
            # flow count for both.
            # ------------------------------------------------

            feature_dict = {

                "bottleneck_mbit":
                    BOTTLENECK_MBIT,

                "requested_flows_mean":
                    mean_flows,

                "active_flows_mean":
                    mean_flows,

                "mean_overlimits_rate":
                    mean_rate,

                "max_overlimits_rate":
                    max_rate,

                "std_overlimits_rate":
                    std_rate,

                "overlimits_rate_slope":
                    rate_slope
            }


            X_live = pd.DataFrame(
                [
                    feature_dict
                ],
                columns=FEATURES
            )


            # ------------------------------------------------
            # Random Forest inference
            # ------------------------------------------------

            probability = float(
                model.predict_proba(
                    X_live
                )[0, 1]
            )


            if (
                probability
                >= WARNING_THRESHOLD
            ):

                state = "WARNING"

                prediction = 1

            else:

                state = "NORMAL"

                prediction = 0


            # ------------------------------------------------
            # Terminal output
            # ------------------------------------------------

            print(
                f"{elapsed:8.1f} | "
                f"{active_flows:5d} | "
                f"{mean_rate:12.1f} | "
                f"{probability:5.2f} | "
                f"{state}"
            )


            # ------------------------------------------------
            # Write prediction log
            # ------------------------------------------------

            writer.writerow([
                time.time(),
                elapsed,
                BOTTLENECK_MBIT,
                active_flows,
                overlimits,
                overlimits_rate,
                mean_rate,
                max_rate,
                std_rate,
                rate_slope,
                probability,
                prediction
            ])

            csv_file.flush()


        # ----------------------------------------------------
        # Sampling interval
        # ----------------------------------------------------

        time.sleep(
            SAMPLE_INTERVAL
        )


# ============================================================
# Ctrl+C
# ============================================================

except KeyboardInterrupt:

    print()
    print()

    print(
        "Online predictor stopped."
    )

    print(
        "Log saved to:"
    )

    print(
        LOG_FILE
    )


finally:

    csv_file.close()