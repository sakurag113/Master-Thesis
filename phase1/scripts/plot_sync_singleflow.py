import pandas as pd
import matplotlib.pyplot as plt

# =========================
# File paths
# =========================

input_file = "/home/yuxsun/phase1/data/evpn_sync_singleflow.csv"

output_file = (
    "/home/yuxsun/phase1/plots/"
    "evpn_singleflow_sync_subplots.png"
)


# =========================
# Read data
# =========================

df = pd.read_csv(input_file)

# Convert timestamp to datetime
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Convert to relative time in seconds
df["time_s"] = (
    df["timestamp"] - df["timestamp"].iloc[0]
).dt.total_seconds()

# overlimits is a cumulative counter.
# Convert it to the increment between two samples.
df["delta_overlimits"] = (
    df["overlimits"]
    .diff()
    .fillna(0)
)

# In case of counter reset, avoid negative values
df.loc[df["delta_overlimits"] < 0, "delta_overlimits"] = 0


# =========================
# Create RTT figure
# =========================

fig1, ax1 = plt.subplots(figsize=(10, 4))

ax1.plot(
    df["time_s"],
    df["rtt_ms"],
    linewidth=1.6
)

ax1.set_title(
    "RTT During Single-flow Experiment"
)

ax1.set_xlabel("Time (s)")
ax1.set_ylabel("RTT (ms)")

ax1.grid(
    True,
    alpha=0.3
)

plt.tight_layout()

rtt_output = (
    "/home/yuxsun/phase1/plots/"
    "evpn_singleflow_rtt.png"
)

plt.savefig(
    rtt_output,
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# =========================
# Create Queue Signal figure
# =========================

fig2, ax2 = plt.subplots(figsize=(10, 4))

ax2.plot(
    df["time_s"],
    df["delta_overlimits"],
    linestyle="--",
    linewidth=1.6
)

ax2.set_title(
    "Queue-related Signal During Single-flow Experiment"
)

ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Delta Overlimits")

ax2.grid(
    True,
    alpha=0.3
)

plt.tight_layout()

queue_output = (
    "/home/yuxsun/phase1/plots/"
    "evpn_singleflow_delta_overlimits.png"
)

plt.savefig(
    queue_output,
    dpi=300,
    bbox_inches="tight"
)

plt.show()


print("RTT figure saved to:")
print(rtt_output)

print("\nQueue signal figure saved to:")
print(queue_output)