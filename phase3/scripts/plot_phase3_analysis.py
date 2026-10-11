#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.patches import Patch
from pathlib import Path


# ============================================================
# Paths
# ============================================================

LOG_FILE = (
    Path.home()
    / "phase3"
    / "logs"
    / "flow_comparison_log.csv"
)

OUTPUT_DIR = (
    Path.home()
    / "phase3"
    / "img"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# Configuration
# ============================================================

WARNING_THRESHOLD = 0.50

SINGLE_FLOW_COLOR = "orange"
DUAL_FLOW_COLOR = "red"

SINGLE_FLOW_ALPHA = 0.14
DUAL_FLOW_ALPHA = 0.10


# ============================================================
# Load data
# ============================================================

df = pd.read_csv(LOG_FILE)

pred = df.dropna(
    subset=["future_high_probability"]
).copy()


# ============================================================
# Detect traffic segments
# ============================================================

def find_segments(data):

    times = data["time_s"].tolist()

    flows = (
        data["active_flows"]
        .fillna(0)
        .astype(int)
        .tolist()
    )

    segments = []

    if len(times) == 0:
        return segments

    start_idx = 0

    for i in range(1, len(data)):

        if flows[i] != flows[i - 1]:

            segments.append(
                (
                    times[start_idx],
                    times[i],
                    flows[i - 1]
                )
            )

            start_idx = i

    segments.append(
        (
            times[start_idx],
            times[-1],
            flows[-1]
        )
    )

    return segments


segments = find_segments(df)


# ============================================================
# Helper functions
# ============================================================

def add_phase_background(ax):

    for start, end, flow in segments:

        if flow == 1:

            ax.axvspan(
                start,
                end,
                color=SINGLE_FLOW_COLOR,
                alpha=SINGLE_FLOW_ALPHA,
                linewidth=0
            )

        elif flow == 2:

            ax.axvspan(
                start,
                end,
                color=DUAL_FLOW_COLOR,
                alpha=DUAL_FLOW_ALPHA,
                linewidth=0
            )


def add_phase_change_lines(ax):

    for i in range(1, len(df)):

        previous_flow = int(
            df.iloc[i - 1]["active_flows"]
        )

        current_flow = int(
            df.iloc[i]["active_flows"]
        )

        if current_flow != previous_flow:

            t = df.iloc[i]["time_s"]

            ax.axvline(
                t,
                linestyle=":",
                linewidth=0.8,
                color="gray",
                alpha=0.4
            )


def add_phase_labels(ax, y_position):

    for start, end, flow in segments:

        duration = end - start

        if duration < 3:
            continue

        center = (
            start + end
        ) / 2

        if flow == 1:

            ax.text(
                center,
                y_position,
                "Single-flow",
                ha="center",
                va="center",
                fontsize=9
            )

        elif flow == 2:

            ax.text(
                center,
                y_position,
                "Dual-flow",
                ha="center",
                va="center",
                fontsize=9
            )


def save_figure(fig, base_name):

    png_file = (
        OUTPUT_DIR
        / f"{base_name}.png"
    )

    pdf_file = (
        OUTPUT_DIR
        / f"{base_name}.pdf"
    )

    fig.savefig(
        png_file,
        dpi=300,
        bbox_inches="tight"
    )

    fig.savefig(
        pdf_file,
        bbox_inches="tight"
    )

    plt.close(fig)

    return png_file, pdf_file


phase_handles = [

    Patch(
        facecolor=SINGLE_FLOW_COLOR,
        alpha=SINGLE_FLOW_ALPHA,
        label="Single-flow period"
    ),

    Patch(
        facecolor=DUAL_FLOW_COLOR,
        alpha=DUAL_FLOW_ALPHA,
        label="Dual-flow period"
    ),
]


# ============================================================
# FIGURE 1
# Online Risk and Traffic Load
# ============================================================

fig, (ax1, ax2) = plt.subplots(
    2,
    1,
    figsize=(13, 8),
    sharex=True,
    gridspec_kw={
        "height_ratios": [1, 2]
    }
)


add_phase_background(ax1)
add_phase_background(ax2)

add_phase_change_lines(ax1)
add_phase_change_lines(ax2)


# ------------------------------------------------------------
# Active flows
# ------------------------------------------------------------

flow_line = ax1.step(
    df["time_s"],
    df["active_flows"],
    where="post",
    linewidth=2.2,
    color="black",
    label="Active flows"
)[0]


ax1.set_ylabel(
    "Active flows"
)

ax1.set_ylim(
    -0.2,
    2.4
)

ax1.set_yticks(
    [0, 1, 2]
)

ax1.grid(
    alpha=0.20
)

add_phase_labels(
    ax1,
    2.15
)

ax1.legend(
    handles=[
        flow_line,
        *phase_handles
    ],
    loc="upper right"
)


# ------------------------------------------------------------
# Predicted risk
# ------------------------------------------------------------

risk_line = ax2.plot(
    pred["time_s"],
    pred["future_high_probability"],
    marker="o",
    markersize=4.0,
    linewidth=2.0,
    color="tab:blue",
    label="Predicted risk"
)[0]


threshold_line = ax2.axhline(
    WARNING_THRESHOLD,
    linestyle="--",
    linewidth=1.7,
    color="tab:red",
    label="Warning threshold"
)


ax2.set_xlabel(
    "Time (s)"
)

ax2.set_ylabel(
    "Future HIGH probability"
)

ax2.set_ylim(
    0,
    1.05
)

ax2.grid(
    alpha=0.20
)

ax2.legend(
    handles=[
        risk_line,
        threshold_line,
        *phase_handles
    ],
    loc="upper right"
)


fig.suptitle(
    "Online Risk and Traffic Load",
    fontsize=14
)

fig.tight_layout(
    rect=[0, 0, 1, 0.96]
)


flow_png, flow_pdf = save_figure(
    fig,
    "phase3_risk_vs_flows_paper"
)


# ============================================================
# FIGURE 2
# Online Risk and Queue Pressure
# ============================================================

fig, (ax1, ax2) = plt.subplots(
    2,
    1,
    figsize=(13, 8),
    sharex=True
)


add_phase_background(ax1)
add_phase_background(ax2)

add_phase_change_lines(ax1)
add_phase_change_lines(ax2)


# ------------------------------------------------------------
# Predicted risk
# ------------------------------------------------------------

risk_line = ax1.plot(
    pred["time_s"],
    pred["future_high_probability"],
    marker="o",
    markersize=4.0,
    linewidth=2.0,
    color="tab:blue",
    label="Predicted risk"
)[0]


threshold_line = ax1.axhline(
    WARNING_THRESHOLD,
    linestyle="--",
    linewidth=1.7,
    color="tab:red",
    label="Warning threshold"
)


ax1.set_ylabel(
    "Future HIGH probability"
)

ax1.set_ylim(
    0,
    1.05
)

ax1.grid(
    alpha=0.20
)

ax1.legend(
    handles=[
        risk_line,
        threshold_line,
        *phase_handles
    ],
    loc="upper right"
)


# ------------------------------------------------------------
# Mean queue pressure
# ------------------------------------------------------------

queue_pred = pred.dropna(
    subset=["mean_overlimits_rate"]
)


queue_line = ax2.plot(
    queue_pred["time_s"],
    queue_pred["mean_overlimits_rate"],
    marker="o",
    markersize=3.5,
    linewidth=1.8,
    color="tab:green",
    label="Mean overlimits rate"
)[0]


ax2.set_xlabel(
    "Time (s)"
)

ax2.set_ylabel(
    "Mean overlimits rate\n(events/s)"
)

ax2.grid(
    alpha=0.20
)

ax2.legend(
    handles=[
        queue_line,
        *phase_handles
    ],
    loc="upper right"
)


fig.suptitle(
    "Online Risk and Queue Pressure",
    fontsize=14
)

fig.tight_layout(
    rect=[0, 0, 1, 0.96]
)


queue_png, queue_pdf = save_figure(
    fig,
    "phase3_risk_vs_queue_paper"
)


# ============================================================
# FIGURE 3
# Online Risk and RTT
# ============================================================

fig, (ax1, ax2) = plt.subplots(
    2,
    1,
    figsize=(13, 8),
    sharex=True
)


add_phase_background(ax1)
add_phase_background(ax2)

add_phase_change_lines(ax1)
add_phase_change_lines(ax2)


# ------------------------------------------------------------
# Predicted risk
# ------------------------------------------------------------

risk_line = ax1.plot(
    pred["time_s"],
    pred["future_high_probability"],
    marker="o",
    markersize=4.0,
    linewidth=2.0,
    color="tab:blue",
    label="Predicted risk"
)[0]


threshold_line = ax1.axhline(
    WARNING_THRESHOLD,
    linestyle="--",
    linewidth=1.7,
    color="tab:red",
    label="Warning threshold"
)


ax1.set_ylabel(
    "Future HIGH probability"
)

ax1.set_ylim(
    0,
    1.05
)

ax1.grid(
    alpha=0.20
)

ax1.legend(
    handles=[
        risk_line,
        threshold_line,
        *phase_handles
    ],
    loc="upper right"
)


# ------------------------------------------------------------
# RTT
# ------------------------------------------------------------

rtt_df = df.dropna(
    subset=["rtt_ms"]
)


rtt_line = ax2.plot(
    rtt_df["time_s"],
    rtt_df["rtt_ms"],
    linewidth=1.6,
    color="tab:purple",
    label="RTT"
)[0]


ax2.set_xlabel(
    "Time (s)"
)

ax2.set_ylabel(
    "RTT (ms)"
)

ax2.grid(
    alpha=0.20
)

ax2.legend(
    handles=[
        rtt_line,
        *phase_handles
    ],
    loc="upper right"
)


fig.suptitle(
    "Online Risk and RTT",
    fontsize=14
)

fig.tight_layout(
    rect=[0, 0, 1, 0.96]
)


rtt_png, rtt_pdf = save_figure(
    fig,
    "phase3_risk_vs_rtt_paper"
)


# ============================================================
# Finished
# ============================================================

print()
print(
    "=============================================="
)

print(
    " Phase 3 Paper Figures Generated"
)

print(
    "=============================================="
)

print()

print(
    "Traffic-load figure:"
)

print(
    flow_png
)

print(
    flow_pdf
)

print()

print(
    "Queue-pressure figure:"
)

print(
    queue_png
)

print(
    queue_pdf
)

print()

print(
    "RTT figure:"
)

print(
    rtt_png
)

print(
    rtt_pdf
)

print()