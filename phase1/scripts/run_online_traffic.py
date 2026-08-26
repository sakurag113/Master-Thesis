#!/usr/bin/env python3

import time
import subprocess
import signal
import sys


# ============================================================
# Configuration
# ============================================================

H1_NS = "h1"
H2_NS = "h2"

SERVER_IP = "192.168.100.22"
SERVER_PORT = 5201

# duration, parallel TCP streams
SCHEDULE = [
    (6, 0),
    (8, 2),
    (6, 0),
    (8, 3),
    (6, 0),
    (8, 2),
    (6, 0),
    (8, 3),
    (4, 0),
]

traffic_process = None


# ============================================================
# Command helper
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
# Check iperf3 server
# ============================================================

def check_server():

    cmd = (
        f"sudo ip netns exec {H2_NS} "
        f"ss -ltnH | grep ':{SERVER_PORT} '"
    )

    code, _, _ = run_command(cmd)

    return code == 0


# ============================================================
# Count TCP connections to iperf3 server
#
# With iperf3 -P N there is normally:
# N data connections + 1 control connection.
# Therefore active data streams = connections - 1.
# ============================================================

def count_active_streams():

    cmd = (
        f"sudo ip netns exec {H1_NS} "
        f"ss -tnH state established"
    )

    code, stdout, _ = run_command(cmd)

    if code != 0:
        return 0

    target = (
        f"{SERVER_IP}:{SERVER_PORT}"
    )

    connections = 0

    for line in stdout.splitlines():

        if target in line:
            connections += 1

    if connections == 0:
        return 0

    return max(
        connections - 1,
        0
    )


# ============================================================
# Stop current iperf3 process
# ============================================================

def stop_traffic():

    global traffic_process

    if traffic_process is not None:

        try:
            traffic_process.terminate()
        except Exception:
            pass

        try:
            traffic_process.wait(
                timeout=2
            )
        except Exception:

            try:
                traffic_process.kill()
            except Exception:
                pass

        traffic_process = None

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

    time.sleep(0.5)


# ============================================================
# Start N parallel streams
# ============================================================

def start_parallel_streams(streams):

    global traffic_process

    stop_traffic()

    if streams == 0:

        print(
            "         requested streams = 0, "
            "active streams = 0"
        )

        return True

    cmd = [
        "sudo",
        "ip",
        "netns",
        "exec",
        H1_NS,
        "iperf3",
        "-c",
        SERVER_IP,
        "-p",
        str(SERVER_PORT),
        "-P",
        str(streams),
        "-t",
        "3600"
    ]

    traffic_process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True
    )

    # Allow TCP sessions to establish
    time.sleep(1.2)

    if traffic_process.poll() is not None:

        error = ""

        try:
            error = (
                traffic_process
                .stderr
                .read()
                .strip()
            )
        except Exception:
            pass

        print(
            "ERROR: iperf3 terminated."
        )

        if error:
            print(
                "iperf3 error:",
                error
            )

        return False

    active = count_active_streams()

    print(
        f"         requested streams = {streams}, "
        f"active streams = {active}"
    )

    if active != streams:

        print(
            "WARNING: requested and active "
            "stream counts do not match."
        )

        return False

    return True


# ============================================================
# Cleanup
# ============================================================

def cleanup(signum=None, frame=None):

    print()
    print(
        "Stopping traffic..."
    )

    stop_traffic()

    print(
        "Traffic stopped."
    )

    sys.exit(0)


signal.signal(
    signal.SIGINT,
    cleanup
)

signal.signal(
    signal.SIGTERM,
    cleanup
)


# ============================================================
# Main
# ============================================================

print()
print(
    "=== Phase 3 Parallel Traffic Generator ==="
)
print()

print(
    "Checking iperf3 server..."
)

if not check_server():

    print()
    print(
        "ERROR: iperf3 server is not running."
    )

    print(
        "Start it with:"
    )

    print(
        f"sudo ip netns exec {H2_NS} "
        f"iperf3 -s -D -p {SERVER_PORT}"
    )

    sys.exit(1)


print(
    "iperf3 server OK."
)

print()

print(
    "Traffic schedule:"
)

schedule_time = 0

for duration, streams in SCHEDULE:

    print(
        f"{schedule_time:4d}s - "
        f"{schedule_time + duration:4d}s : "
        f"{streams} streams"
    )

    schedule_time += duration


print()
print(
    f"Total duration = {schedule_time} s"
)
print()

print(
    "Starting experiment..."
)
print()


experiment_start = time.monotonic()


try:

    for duration, streams in SCHEDULE:

        stage_start = time.monotonic()

        elapsed = (
            stage_start
            - experiment_start
        )

        print(
            f"[{elapsed:6.1f}s] "
            f"Set traffic to "
            f"{streams} stream(s)"
        )

        success = start_parallel_streams(
            streams
        )

        if not success:

            print()
            print(
                "Traffic validation failed."
            )

            print(
                "Experiment aborted."
            )

            break

        while (
            time.monotonic()
            - stage_start
            < duration
        ):

            time.sleep(0.2)


finally:

    stop_traffic()


print()
print(
    "Experiment finished."
)