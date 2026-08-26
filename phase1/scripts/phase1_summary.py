import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =========================
# Input files
# =========================

repeat_file = (
    "/home/yuxsun/phase1/data/"
    "repeatability_analysis.csv"
)

queue_file = (
    "/home/yuxsun/phase1/data/"
    "queue_repeatability_summary.csv"
)

# =========================
# Load data
# =========================

repeat_df = pd.read_csv(repeat_file)
queue_df = pd.read_csv(queue_file)

repeat_df["condition"] = np.where(
    repeat_df["run"].str.startswith("Single"),
    "Single-flow",
    "Dual-flow"
)

queue_df["condition"] = np.where(
    queue_df["run"].str.startswith("Single"),
    "Single-flow",
    "Dual-flow"
)

# =========================
# Build summary table
# =========================

summary_rows = []

for condition in ["Single-flow", "Dual-flow"]:

    r = repeat_df[
        repeat_df["condition"] == condition
    ]

    q = queue_df[
        queue_df["condition"] == condition
    ]

    summary_rows.append({
        "condition":
            condition,

        "mean_high_latency_ratio":
            r["high_latency_ratio"].mean(),

        "std_high_latency_ratio":
            r["high_latency_ratio"].std(ddof=1),

        "mean_overlimits_rate":
            q["all_mean_overlimits_rate"].mean(),

        "mean_high_window_overlimits_rate":
            q[
                "high_window_mean_overlimits_rate"
            ].mean(),

        "mean_normal_window_overlimits_rate":
            q[
                "normal_window_mean_overlimits_rate"
            ].mean()
    })

summary = pd.DataFrame(summary_rows)

print()
print("=== Phase 1 Final Summary ===")
print()

print(summary.to_string(index=False))

summary_file = (
    "/home/yuxsun/phase1/data/"
    "phase1_final_summary.csv"
)

summary.to_csv(
    summary_file,
    index=False
)

# =========================
# Figure 1:
# High-latency ratio
# =========================

fig1, ax1 = plt.subplots(figsize=(7, 4))

ax1.bar(
    summary["condition"],
    summary["mean_high_latency_ratio"] * 100
)

ax1.errorbar(
    summary["condition"],
    summary["mean_high_latency_ratio"] * 100,
    yerr=summary["std_high_latency_ratio"] * 100,
    fmt="none",
    capsize=5
)

ax1.set_ylabel(
    "High-latency Window Ratio (%)"
)

ax1.set_title(
    "High-latency Window Ratio Across Repeated Runs"
)

ax1.grid(
    True,
    axis="y",
    alpha=0.3
)

fig1.tight_layout()

fig1.savefig(
    "/home/yuxsun/phase1/plots/"
    "phase1_high_latency_ratio.png",
    dpi=300,
    bbox_inches="tight"
)

# =========================
# Figure 2:
# Queue activity
# =========================

fig2, ax2 = plt.subplots(figsize=(7, 4))

labels = [
    "Single HIGH",
    "Single Normal",
    "Dual HIGH",
    "Dual Normal"
]

values = [
    summary.loc[
        summary["condition"] == "Single-flow",
        "mean_high_window_overlimits_rate"
    ].iloc[0],

    summary.loc[
        summary["condition"] == "Single-flow",
        "mean_normal_window_overlimits_rate"
    ].iloc[0],

    summary.loc[
        summary["condition"] == "Dual-flow",
        "mean_high_window_overlimits_rate"
    ].iloc[0],

    summary.loc[
        summary["condition"] == "Dual-flow",
        "mean_normal_window_overlimits_rate"
    ].iloc[0]
]

ax2.bar(
    labels,
    values
)

ax2.set_ylabel(
    "Mean Overlimits Rate (/s)"
)

ax2.set_title(
    "Queue Activity in HIGH and Normal Windows"
)

ax2.tick_params(
    axis="x",
    rotation=20
)

ax2.grid(
    True,
    axis="y",
    alpha=0.3
)

fig2.tight_layout()

fig2.savefig(
    "/home/yuxsun/phase1/plots/"
    "phase1_queue_activity.png",
    dpi=300,
    bbox_inches="tight"
)

print()
print("Saved:")
print(summary_file)
print(
    "/home/yuxsun/phase1/plots/"
    "phase1_high_latency_ratio.png"
)
print(
    "/home/yuxsun/phase1/plots/"
    "phase1_queue_activity.png"
)

plt.show()