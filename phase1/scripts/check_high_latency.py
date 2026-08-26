import pandas as pd
import sys
import os

RTT_THRESHOLD = 75
WINDOW_SECONDS = 2
RATIO_THRESHOLD = 0.5


# -------------------------
# Check input argument
# -------------------------

if len(sys.argv) < 2:
    print("Error: Please provide a CSV file.")
    print()
    print("Usage:")
    print(
        "python3 check_high_latency.py "
        "/path/to/data.csv"
    )
    sys.exit(1)


file = sys.argv[1]


# -------------------------
# Check file existence
# -------------------------

if not os.path.exists(file):
    print("Error: File does not exist:")
    print(file)
    sys.exit(1)


# -------------------------
# Load data
# -------------------------

df = pd.read_csv(file)

df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)

df["time_s"] = (
    df["timestamp"]
    - df["timestamp"].iloc[0]
).dt.total_seconds()


# -------------------------
# Window assignment
# -------------------------

df["window_id"] = (
    df["time_s"] // WINDOW_SECONDS
).astype(int)


# -------------------------
# High-latency sample
# -------------------------

df["high_sample"] = (
    df["rtt_ms"] > RTT_THRESHOLD
)


# -------------------------
# Window analysis
# -------------------------

total = 0
high = 0

print()
print("=== High-latency Window Analysis ===")
print()

print(
    f"RTT threshold = {RTT_THRESHOLD} ms"
)

print(
    f"Window size = {WINDOW_SECONDS} s"
)

print(
    f"Window ratio threshold = "
    f"{RATIO_THRESHOLD:.0%}"
)

print()

for window_id, group in df.groupby(
    "window_id"
):

    ratio = group["high_sample"].mean()

    is_high = (
        ratio >= RATIO_THRESHOLD
    )

    start = (
        window_id * WINDOW_SECONDS
    )

    end = (
        (window_id + 1)
        * WINDOW_SECONDS
    )

    status = (
        "HIGH"
        if is_high
        else "normal"
    )

    print(
        f"{start:5.1f} - {end:5.1f} s"
        f" | spike ratio = {ratio:.2f}"
        f" | {status}"
    )

    total += 1
    high += int(is_high)


# -------------------------
# Summary
# -------------------------

print()
print("=== Summary ===")
print()

print(
    "High-latency windows =",
    high,
    "/",
    total
)

if total > 0:
    print(
        "High-latency window ratio =",
        f"{high / total:.2%}"
    )