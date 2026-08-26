#!/usr/bin/env python3

import os
import time
import shutil
import subprocess
import signal


# ============================================================
# Paths
# ============================================================

PHASE3_DIR = "/home/yuxsun/phase3"

SCRIPT_DIR = f"{PHASE3_DIR}/scripts"
LOG_DIR = f"{PHASE3_DIR}/logs"

OFF_PREDICTOR = (
    f"{SCRIPT_DIR}/online_predictor_with_rtt.py"
)

ON_PREDICTOR = (
    f"{SCRIPT_DIR}/online_predictor_mitigation_v2.py"
)

TRAFFIC_SCRIPT = (
    f"{SCRIPT_DIR}/run_online_traffic.py"
)

OFF_SOURCE_LOG = (
    f"{LOG_DIR}/online_validation_log.csv"
)

ON_SOURCE_LOG = (
    f"{LOG_DIR}/mitigation_on_v2_log.csv"
)


# ============================================================
# Experiment configuration
# ============================================================

NUM_RUNS = 5

BASELINE_BEFORE_TRAFFIC = 5
RECOVERY_AFTER_TRAFFIC = 5

BETWEEN_RUN_COOLDOWN = 5


# ============================================================
# Helper
# ============================================================

def run_command(cmd):

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    return (
        result.returncode,
        result.stdout,
        result.stderr
    )


# ============================================================
# Ensure iperf server
# ============================================================

def ensure_iperf_server():

    cmd = (
        "sudo ip netns exec h2 "
        "ss -ltnH | grep ':5201 '"
    )

    code, _, _ = run_command(cmd)

    if code == 0:

        print(
            "iperf3 server already running."
        )

        return True


    print(
        "Starting iperf3 server..."
    )

    cmd = (
        "sudo ip netns exec h2 "
        "iperf3 -s -D -p 5201"
    )

    code, _, stderr = run_command(cmd)

    if code != 0:

        print(
            "ERROR: failed to start iperf3 server."
        )

        if stderr:
            print(stderr)

        return False


    time.sleep(1)

    return True


# ============================================================
# Reset bottleneck
# ============================================================

def reset_bottleneck():

    cmd = (
        "sudo ip netns exec spine "
        "tc qdisc replace dev sp-l2 root "
        "tbf rate 10mbit "
        "burst 65536 "
        "latency 50ms"
    )

    code, _, stderr = run_command(cmd)

    if code != 0:

        print(
            "ERROR: failed to reset bottleneck."
        )

        if stderr:
            print(stderr)

        return False

    return True


# ============================================================
# Kill residual iperf clients
# ============================================================

def cleanup_clients():

    subprocess.run(
        (
            "sudo pkill -f "
            "\"iperf3.*-c.*192.168.100.22\" "
            "|| true"
        ),
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(1)


# ============================================================
# Stop predictor gracefully
# ============================================================

def stop_process(proc):

    if proc is None:
        return

    if proc.poll() is not None:
        return

    try:

        proc.send_signal(
            signal.SIGINT
        )

        proc.wait(
            timeout=5
        )

    except Exception:

        try:
            proc.terminate()
            proc.wait(timeout=2)

        except Exception:

            try:
                proc.kill()
            except Exception:
                pass


# ============================================================
# Run one experiment
# ============================================================

def run_one_experiment(
    mode,
    run_id
):

    print()
    print(
        "============================================"
    )

    print(
        f"{mode} RUN {run_id}"
    )

    print(
        "============================================"
    )

    print()


    cleanup_clients()

    if not reset_bottleneck():

        raise RuntimeError(
            "Failed to reset bottleneck."
        )


    if mode == "OFF":

        predictor_script = (
            OFF_PREDICTOR
        )

        source_log = (
            OFF_SOURCE_LOG
        )

        destination_log = (
            f"{LOG_DIR}/"
            f"formal_off_run{run_id}.csv"
        )

    else:

        predictor_script = (
            ON_PREDICTOR
        )

        source_log = (
            ON_SOURCE_LOG
        )

        destination_log = (
            f"{LOG_DIR}/"
            f"formal_on_run{run_id}.csv"
        )


    # Remove stale source log
    if os.path.exists(
        source_log
    ):

        os.remove(
            source_log
        )


    # --------------------------------------------------------
    # Start predictor/controller
    # --------------------------------------------------------

    print(
        f"Starting {mode} predictor..."
    )

    predictor_proc = subprocess.Popen(
        [
            "python3",
            predictor_script
        ]
    )


    # --------------------------------------------------------
    # Baseline before traffic
    # --------------------------------------------------------

    print(
        f"Baseline for "
        f"{BASELINE_BEFORE_TRAFFIC} s..."
    )

    time.sleep(
        BASELINE_BEFORE_TRAFFIC
    )


    # --------------------------------------------------------
    # Run traffic schedule
    # --------------------------------------------------------

    print(
        "Starting traffic schedule..."
    )

    traffic_proc = subprocess.Popen(
        [
            "python3",
            TRAFFIC_SCRIPT
        ]
    )

    traffic_return = (
        traffic_proc.wait()
    )


    if traffic_return != 0:

        print(
            "WARNING: traffic generator "
            "returned non-zero status."
        )


    # --------------------------------------------------------
    # Recovery
    # --------------------------------------------------------

    print(
        f"Recovery for "
        f"{RECOVERY_AFTER_TRAFFIC} s..."
    )

    time.sleep(
        RECOVERY_AFTER_TRAFFIC
    )


    # --------------------------------------------------------
    # Stop predictor
    # --------------------------------------------------------

    print(
        "Stopping predictor..."
    )

    stop_process(
        predictor_proc
    )


    cleanup_clients()

    reset_bottleneck()


    # --------------------------------------------------------
    # Save log
    # --------------------------------------------------------

    if not os.path.exists(
        source_log
    ):

        raise RuntimeError(
            f"Expected log not found: "
            f"{source_log}"
        )


    shutil.move(
        source_log,
        destination_log
    )


    print(
        "Run saved to:"
    )

    print(
        destination_log
    )


# ============================================================
# Main
# ============================================================

os.makedirs(
    LOG_DIR,
    exist_ok=True
)


print()
print(
    "=== Phase 3 Formal A/B Batch ==="
)
print()

print(
    f"OFF runs = {NUM_RUNS}"
)

print(
    f"ON runs  = {NUM_RUNS}"
)

print()


if not ensure_iperf_server():

    raise SystemExit(1)


# ============================================================
# OFF runs first
# ============================================================

for run_id in range(
    1,
    NUM_RUNS + 1
):

    run_one_experiment(
        "OFF",
        run_id
    )

    print(
        f"Cooldown "
        f"{BETWEEN_RUN_COOLDOWN} s..."
    )

    time.sleep(
        BETWEEN_RUN_COOLDOWN
    )


# ============================================================
# ON runs
# ============================================================

for run_id in range(
    1,
    NUM_RUNS + 1
):

    run_one_experiment(
        "ON",
        run_id
    )

    if run_id < NUM_RUNS:

        print(
            f"Cooldown "
            f"{BETWEEN_RUN_COOLDOWN} s..."
        )

        time.sleep(
            BETWEEN_RUN_COOLDOWN
        )


print()
print(
    "============================================"
)

print(
    "Formal A/B batch completed."
)

print(
    "============================================"
)

print()

print(
    "Expected files:"
)

for run_id in range(
    1,
    NUM_RUNS + 1
):

    print(
        f"{LOG_DIR}/formal_off_run{run_id}.csv"
    )

for run_id in range(
    1,
    NUM_RUNS + 1
):

    print(
        f"{LOG_DIR}/formal_on_run{run_id}.csv"
    )

print()