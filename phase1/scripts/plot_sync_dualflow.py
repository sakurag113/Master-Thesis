import pandas as pd
import matplotlib.pyplot as plt

input_file = "/home/yuxsun/phase1/data/evpn_sync_dualflow.csv"

df = pd.read_csv(input_file)

df["timestamp"] = pd.to_datetime(df["timestamp"])

df["time_s"] = (
    df["timestamp"] - df["timestamp"].iloc[0]
).dt.total_seconds()

df["delta_overlimits"] = (
    df["overlimits"]
    .diff()
    .fillna(0)
)

df.loc[df["delta_overlimits"] < 0, "delta_overlimits"] = 0


# RTT figure

fig1, ax1 = plt.subplots(figsize=(10, 4))

ax1.plot(
    df["time_s"],
    df["rtt_ms"],
    linewidth=1.6
)

ax1.set_title("RTT During Dual-flow Experiment")
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("RTT (ms)")
ax1.grid(True, alpha=0.3)

fig1.tight_layout()

rtt_output = (
    "/home/yuxsun/phase1/plots/"
    "evpn_dualflow_rtt.png"
)

fig1.savefig(
    rtt_output,
    dpi=300,
    bbox_inches="tight"
)


# Queue-related signal figure

fig2, ax2 = plt.subplots(figsize=(10, 4))

ax2.plot(
    df["time_s"],
    df["delta_overlimits"],
    linestyle="--",
    linewidth=1.6
)

ax2.set_title(
    "Queue-related Signal During Dual-flow Experiment"
)

ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Delta Overlimits")
ax2.grid(True, alpha=0.3)

fig2.tight_layout()

queue_output = (
    "/home/yuxsun/phase1/plots/"
    "evpn_dualflow_delta_overlimits.png"
)

fig2.savefig(
    queue_output,
    dpi=300,
    bbox_inches="tight"
)

print("RTT figure saved to:")
print(rtt_output)

print("\nQueue signal figure saved to:")
print(queue_output)

plt.show()