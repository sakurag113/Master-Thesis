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
# Paths
# ============================================================

MODEL_FILE = (
    "/home/yuxsun/phase3/models/"
    "online_rf_queue_traffic.joblib"
)

LOG_DIR = "/home/yuxsun/phase3/logs"

LOG_FILE = (
    "/home/yuxsun/phase3/logs/"
    "flow_comparison_log.csv"
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

TARGET_IP = "192.168.100.22"

IPERF_SERVER_IP = "192.168.100.22"
IPERF_SERVER_PORT = 5201


# ============================================================
# Experiment configuration
# ============================================================

BOTTLENECK_MBIT = 10.0

OBSERVATION_WINDOW = 2.0

SAMPLE_INTERVAL = 0.2

PREDICTION_INTERVAL = 1.0

WARNING_THRESHOLD = 0.50


# ============================================================
# Model features
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
# Command helper
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

        return (
            result.returncode,
            result.stdout,
            result.stderr
        )

    except Exception as exc:

        return (
            1,
            "",
            str(exc)
        )


# ============================================================
# Read overlimits
# ============================================================

def get_overlimits():

    cmd = (
        f"sudo ip netns exec {SPINE_NS} "
        f"tc -s qdisc show dev {BOTTLENECK_DEV}"
    )

    _, output, _ = run_command(cmd)

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
# Count active flows
# ============================================================

def get_active_flows():

    cmd = (
        f"sudo ip netns exec {H1_NS} "
        f"ss -tnH state established"
    )

    _, output, _ = run_command(cmd)

    target = (
        f"{IPERF_SERVER_IP}:"
        f"{IPERF_SERVER_PORT}"
    )

    connections = 0

    for line in output.splitlines():

        if target in line:
            connections += 1

    if connections == 0:
        return 0

    return max(
        connections - 1,
        0
    )


# ============================================================
# RTT
# ============================================================

def get_rtt():

    cmd = (
        f"sudo ip netns exec {H1_NS} "
        f"ping -n -c 1 -W 1 {TARGET_IP}"
    )

    _, output, _ = run_command(cmd)

    match = re.search(
        r"time[=<]([\d.]+)\s*ms",
        output
    )

    if match:

        return float(
            match.group(1)
        )

    return np.nan


# ============================================================
# Slope
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

    return float(
        np.polyfit(
            x,
            y,
            1
        )[0]
    )


# ============================================================
# Load model
# ============================================================

print()
print(
    "=== Phase 3 Flow Comparison Predictor ==="
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

print(
    "Model loaded successfully."
)

print()

print(
    f"Bottleneck rate = "
    f"{BOTTLENECK_MBIT:.1f} Mbit/s"
)

print(
    f"Observation window = "
    f"{OBSERVATION_WINDOW:.1f} s"
)

print(
    f"Warning threshold = "
    f"{WARNING_THRESHOLD:.2f}"
)

print()

print(
    "NO MITIGATION will be applied."
)

print()


# ============================================================
# Runtime state
# ============================================================

buffer = deque()

previous_overlimits = None
previous_timestamp = None

start_time = time.monotonic()

last_prediction_time = (
    -PREDICTION_INTERVAL
)


# ============================================================
# CSV
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

    "active_flows",
    "rtt_ms",

    "overlimits",
    "overlimits_rate",

    "mean_overlimits_rate",
    "max_overlimits_rate",
    "std_overlimits_rate",
    "overlimits_rate_slope",

    "mean_active_flows",

    "future_high_probability",
    "prediction",
])


print(
    " time(s) | flows | RTT(ms) | "
    "overlimits/s | risk | state"
)

print(
    "------------------------------------------------------------"
)


# ============================================================
# Main loop
# ============================================================

try:

    while True:

        now = time.monotonic()

        elapsed = (
            now
            -
            start_time
        )

        # ----------------------------------------------------
        # Telemetry
        # ----------------------------------------------------

        overlimits = get_overlimits()

        active_flows = get_active_flows()

        rtt_ms = get_rtt()


        # ----------------------------------------------------
        # overlimits rate
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
                -
                previous_timestamp
            )

            delta = (
                overlimits
                -
                previous_overlimits
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
        # Rolling buffer
        # ----------------------------------------------------

        buffer.append({
            "time":
                elapsed,

            "active_flows":
                active_flows,

            "overlimits_rate":
                overlimits_rate
        })


        while (
            buffer
            and
            (
                elapsed
                -
                buffer[0]["time"]
                >
                OBSERVATION_WINDOW
            )
        ):

            buffer.popleft()


        probability = np.nan
        prediction = np.nan

        mean_rate_log = np.nan
        max_rate_log = np.nan
        std_rate_log = np.nan
        slope_log = np.nan
        mean_flows_log = np.nan


        # ----------------------------------------------------
        # Prediction
        # ----------------------------------------------------

        if (
            elapsed
            -
            last_prediction_time
            >=
            PREDICTION_INTERVAL
        ):

            last_prediction_time = (
                elapsed
            )


            if (
                elapsed
                >=
                OBSERVATION_WINDOW
                and
                len(buffer)
                >=
                3
            ):

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

                slope = calculate_slope(
                    times,
                    rate_values
                )


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
                        slope
                }


                X_live = pd.DataFrame(
                    [feature_dict],
                    columns=FEATURES
                )


                probability = float(
                    model.predict_proba(
                        X_live
                    )[0, 1]
                )


                prediction = int(
                    probability
                    >=
                    WARNING_THRESHOLD
                )


                if prediction == 1:

                    state = "WARNING"

                else:

                    state = "NORMAL"


                if np.isnan(
                    rtt_ms
                ):

                    rtt_text = "N/A"

                else:

                    rtt_text = (
                        f"{rtt_ms:.1f}"
                    )


                print(
                    f"{elapsed:8.1f} | "
                    f"{active_flows:5d} | "
                    f"{rtt_text:>7} | "
                    f"{mean_rate:12.1f} | "
                    f"{probability:4.2f} | "
                    f"{state}"
                )


                mean_rate_log = mean_rate
                max_rate_log = max_rate
                std_rate_log = std_rate
                slope_log = slope
                mean_flows_log = mean_flows


        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        writer.writerow([
            time.time(),
            elapsed,

            active_flows,
            rtt_ms,

            overlimits,
            overlimits_rate,

            mean_rate_log,
            max_rate_log,
            std_rate_log,
            slope_log,

            mean_flows_log,

            probability,
            prediction,
        ])

        csv_file.flush()

        time.sleep(
            SAMPLE_INTERVAL
        )


# ============================================================
# Ctrl+C
# ============================================================

except KeyboardInterrupt:

    print()
    print(
        "Stopping flow comparison predictor..."
    )


finally:

    csv_file.close()

    print()
    print(
        "Log saved to:"
    )

    print(
        LOG_FILE
    )