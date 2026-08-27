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
    "mitigation_on_v2_log.csv"
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
# Bottleneck / mitigation configuration
# ============================================================

BASE_RATE_MBIT = 10.0
MITIGATION_RATE_MBIT = 20.0

BURST_BYTES = 65536
TBF_LATENCY_MS = 50


# ============================================================
# Prediction configuration
# ============================================================

OBSERVATION_WINDOW = 2.0

SAMPLE_INTERVAL = 0.2

PREDICTION_INTERVAL = 1.0

WARNING_THRESHOLD = 0.50


# ============================================================
# Mitigation controller
# ============================================================

MITIGATION_DURATION = 4.0

COOLDOWN_DURATION = 3.0


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
# Run command
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
# Set TBF rate
# ============================================================

def set_tbf_rate(rate_mbit):

    cmd = (
        f"sudo ip netns exec {SPINE_NS} "
        f"tc qdisc replace dev {BOTTLENECK_DEV} root "
        f"tbf rate {rate_mbit}mbit "
        f"burst {BURST_BYTES} "
        f"latency {TBF_LATENCY_MS}ms"
    )

    code, _, stderr = run_command(
        cmd
    )

    if code != 0:

        print(
            f"ERROR: failed to set TBF "
            f"to {rate_mbit} Mbit/s"
        )

        if stderr:
            print(
                stderr.strip()
            )

        return False

    return True


# ============================================================
# Read overlimits counter
# ============================================================

def get_overlimits():

    cmd = (
        f"sudo ip netns exec {SPINE_NS} "
        f"tc -s qdisc show dev {BOTTLENECK_DEV}"
    )

    _, output, _ = run_command(
        cmd
    )

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
# Count active iperf3 data streams
#
# iperf3 -P N normally creates
# N data connections + one control connection.
# ============================================================

def get_active_flows():

    cmd = (
        f"sudo ip netns exec {H1_NS} "
        f"ss -tnH state established"
    )

    _, output, _ = run_command(
        cmd
    )

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
# RTT measurement
# ============================================================

def get_rtt():

    cmd = (
        f"sudo ip netns exec {H1_NS} "
        f"ping -n -c 1 -W 1 {TARGET_IP}"
    )

    _, output, _ = run_command(
        cmd
    )

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
# Linear slope
# ============================================================

def calculate_slope(
    times,
    values
):

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
    "=== Phase 3 Prediction-driven Mitigation V2 ==="
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
    f"Baseline rate = "
    f"{BASE_RATE_MBIT:.1f} Mbit/s"
)

print(
    f"Mitigation rate = "
    f"{MITIGATION_RATE_MBIT:.1f} Mbit/s"
)

print(
    f"Warning threshold = "
    f"{WARNING_THRESHOLD:.2f}"
)

print(
    f"Mitigation duration = "
    f"{MITIGATION_DURATION:.1f} s"
)

print(
    f"Cooldown = "
    f"{COOLDOWN_DURATION:.1f} s"
)

print(
    "Additional trigger condition: "
    "active_flows > 0"
)

print()


# ============================================================
# Restore initial baseline rate
# ============================================================

if not set_tbf_rate(
    BASE_RATE_MBIT
):

    raise SystemExit(1)


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

current_rate_mbit = (
    BASE_RATE_MBIT
)

mitigation_active = False

mitigation_end_time = None

last_mitigation_end = (
    -9999.0
)

trigger_count = 0

blocked_zero_flow_count = 0


# ============================================================
# CSV log
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

    "current_rate_mbit",

    "mean_overlimits_rate",
    "max_overlimits_rate",
    "std_overlimits_rate",
    "overlimits_rate_slope",

    "future_high_probability",
    "prediction",

    "mitigation_active",
    "mitigation_triggered",

    "trigger_allowed",
    "blocked_zero_flow",

    "trigger_count"
])


print(
    " time(s) | flows | RTT(ms) | "
    "rate | overlimits/s | risk | "
    "state | mitigation"
)

print(
    "------------------------------------------------"
    "------------------------------"
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
        # End mitigation after 4 seconds
        # ----------------------------------------------------

        if (
            mitigation_active
            and
            mitigation_end_time is not None
            and
            now >= mitigation_end_time
        ):

            if set_tbf_rate(
                BASE_RATE_MBIT
            ):

                current_rate_mbit = (
                    BASE_RATE_MBIT
                )

                mitigation_active = False

                mitigation_end_time = None

                last_mitigation_end = (
                    time.monotonic()
                )

                print(
                    f"[{elapsed:6.1f}s] "
                    f"MITIGATION END -> "
                    f"{BASE_RATE_MBIT:.0f} Mbit/s"
                )


        # ----------------------------------------------------
        # Collect telemetry
        # ----------------------------------------------------

        overlimits = get_overlimits()

        active_flows = get_active_flows()

        rtt_ms = get_rtt()


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
        # Rolling observation buffer
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
                - buffer[0]["time"]
                > OBSERVATION_WINDOW
            )
        ):

            buffer.popleft()


        probability = np.nan
        prediction = np.nan

        mean_rate_log = np.nan
        max_rate_log = np.nan
        std_rate_log = np.nan
        slope_log = np.nan

        mitigation_triggered = 0
        trigger_allowed = 0
        blocked_zero_flow = 0


        # ----------------------------------------------------
        # Prediction
        # ----------------------------------------------------

        if (
            elapsed
            - last_prediction_time
            >= PREDICTION_INTERVAL
        ):

            last_prediction_time = (
                elapsed
            )


            if (
                elapsed >= OBSERVATION_WINDOW
                and
                len(buffer) >= 3
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


                # --------------------------------------------
                # Model input
                # --------------------------------------------

                feature_dict = {

                    "bottleneck_mbit":
                        current_rate_mbit,

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
                    >= WARNING_THRESHOLD
                )


                # --------------------------------------------
                # Controller conditions
                # --------------------------------------------

                cooldown_finished = (
                    now
                    - last_mitigation_end
                    >= COOLDOWN_DURATION
                )


                trigger_allowed = int(
                    prediction == 1
                    and
                    active_flows > 0
                    and
                    not mitigation_active
                    and
                    cooldown_finished
                )


                # --------------------------------------------
                # Record blocked false trigger
                #
                # Model says WARNING but there is currently
                # no active traffic.
                # --------------------------------------------

                if (
                    prediction == 1
                    and
                    active_flows == 0
                    and
                    not mitigation_active
                ):

                    blocked_zero_flow = 1

                    blocked_zero_flow_count += 1

                    print(
                        f"[{elapsed:6.1f}s] "
                        f"WARNING ignored: "
                        f"active_flows=0 "
                        f"(risk={probability:.2f})"
                    )


                # --------------------------------------------
                # Trigger mitigation
                # --------------------------------------------

                if trigger_allowed:

                    if set_tbf_rate(
                        MITIGATION_RATE_MBIT
                    ):

                        mitigation_active = True

                        mitigation_end_time = (
                            time.monotonic()
                            + MITIGATION_DURATION
                        )

                        current_rate_mbit = (
                            MITIGATION_RATE_MBIT
                        )

                        trigger_count += 1

                        mitigation_triggered = 1


                        print(
                            f"[{elapsed:6.1f}s] "
                            f"MITIGATION TRIGGER -> "
                            f"{MITIGATION_RATE_MBIT:.0f} Mbit/s "
                            f"(risk={probability:.2f}, "
                            f"flows={active_flows})"
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


                mitigation_text = (
                    "ON"
                    if mitigation_active
                    else "OFF"
                )


                print(
                    f"{elapsed:8.1f} | "
                    f"{active_flows:5d} | "
                    f"{rtt_text:>7} | "
                    f"{current_rate_mbit:4.0f} | "
                    f"{mean_rate:12.1f} | "
                    f"{probability:4.2f} | "
                    f"{state:7s} | "
                    f"{mitigation_text}"
                )


                mean_rate_log = mean_rate
                max_rate_log = max_rate
                std_rate_log = std_rate
                slope_log = slope


        # ----------------------------------------------------
        # Save sample
        # ----------------------------------------------------

        writer.writerow([
            time.time(),
            elapsed,

            active_flows,
            rtt_ms,
            overlimits,
            overlimits_rate,

            current_rate_mbit,

            mean_rate_log,
            max_rate_log,
            std_rate_log,
            slope_log,

            probability,
            prediction,

            int(
                mitigation_active
            ),

            mitigation_triggered,

            trigger_allowed,
            blocked_zero_flow,

            trigger_count
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
        "Stopping mitigation controller..."
    )


finally:

    # Always restore 10 Mbit/s
    set_tbf_rate(
        BASE_RATE_MBIT
    )

    csv_file.close()

    print()
    print(
        "Baseline TBF restored:"
    )

    print(
        f"{BASE_RATE_MBIT:.0f} Mbit/s"
    )

    print()

    print(
        f"Total mitigation triggers = "
        f"{trigger_count}"
    )

    print(
        f"Warnings blocked at zero flow = "
        f"{blocked_zero_flow_count}"
    )

    print()

    print(
        "Log saved to:"
    )

    print(
        LOG_FILE
    )