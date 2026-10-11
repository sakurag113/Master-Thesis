#!/usr/bin/env python3

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# Paths
# ============================================================

PHASE3 = Path.home() / "phase3"

DATA_DIR = PHASE3 / "data"
IMG_DIR = PHASE3 / "img"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

IMG_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# Key results
# ============================================================

rows = [

    # --------------------------------------------------------
    # Dataset scale
    # --------------------------------------------------------

    {
        "Section": "Dataset Scale",
        "Item": "Independent experiment runs",
        "Value": "60",
        "Notes": "Used for grouped cross-validation"
    },

    {
        "Section": "Dataset Scale",
        "Item": "Prediction windows",
        "Value": "4543",
        "Notes": "Complete Phase 2 prediction dataset"
    },

    {
        "Section": "Dataset Scale",
        "Item": "Early-warning samples",
        "Value": "2623",
        "Notes": "Samples with current_high = 0"
    },

    {
        "Section": "Dataset Scale",
        "Item": "NORMAL → HIGH transitions",
        "Value": "381",
        "Notes": "Positive early-warning samples"
    },

    {
        "Section": "Dataset Scale",
        "Item": "Early-warning positive prevalence",
        "Value": "14.53%",
        "Notes": "381 / 2623"
    },

    {
        "Section": "Dataset Scale",
        "Item": "Mean bottleneck packets per measured run",
        "Value": "2885",
        "Notes": "Measured from Phase 3 packet-count runs"
    },


    # --------------------------------------------------------
    # Final offline model
    # --------------------------------------------------------

    {
        "Section": "Final Model",
        "Item": "Selected model",
        "Value": "Queue + Traffic Random Forest",
        "Notes": "Selected after feature ablation"
    },

    {
        "Section": "Final Model",
        "Item": "Number of online features",
        "Value": "7",
        "Notes": "Traffic, bottleneck, and queue features"
    },

    {
        "Section": "Final Model",
        "Item": "5-fold F1",
        "Value": "0.483 ± 0.067",
        "Notes": "Early-warning evaluation"
    },

    {
        "Section": "Final Model",
        "Item": "5-fold ROC-AUC",
        "Value": "0.792 ± 0.041",
        "Notes": "Early-warning evaluation"
    },

    {
        "Section": "Final Model",
        "Item": "5-fold PR-AUC",
        "Value": "0.556 ± 0.060",
        "Notes": "Early-warning evaluation"
    },


    # --------------------------------------------------------
    # Pooled OOF metrics
    # --------------------------------------------------------

    {
        "Section": "Pooled OOF Metrics",
        "Item": "Accuracy",
        "Value": "0.884",
        "Notes": "Queue + Traffic RF"
    },

    {
        "Section": "Pooled OOF Metrics",
        "Item": "Precision",
        "Value": "0.692",
        "Notes": "Queue + Traffic RF"
    },

    {
        "Section": "Pooled OOF Metrics",
        "Item": "Recall",
        "Value": "0.365",
        "Notes": "Queue + Traffic RF"
    },

    {
        "Section": "Pooled OOF Metrics",
        "Item": "F1",
        "Value": "0.478",
        "Notes": "Queue + Traffic RF"
    },

    {
        "Section": "Pooled OOF Metrics",
        "Item": "ROC-AUC",
        "Value": "0.787",
        "Notes": "Queue + Traffic RF"
    },

    {
        "Section": "Pooled OOF Metrics",
        "Item": "PR-AUC",
        "Value": "0.547",
        "Notes": "Random prevalence baseline = 0.145"
    },

    {
        "Section": "Pooled OOF Metrics",
        "Item": "Confusion matrix",
        "Value": "TN 2180 / FP 62 / FN 242 / TP 139",
        "Notes": "Default decision threshold"
    },


    # --------------------------------------------------------
    # Phase 3 online validation
    # --------------------------------------------------------

    {
        "Section": "Phase 3 Online",
        "Item": "Single-flow mean risk",
        "Value": "0.791",
        "Notes": "Flow comparison experiment"
    },

    {
        "Section": "Phase 3 Online",
        "Item": "Dual-flow mean risk",
        "Value": "0.828",
        "Notes": "Flow comparison experiment"
    },

    {
        "Section": "Phase 3 Online",
        "Item": "Single-flow mean overlimits rate",
        "Value": "112.9 events/s",
        "Notes": "Queue pressure"
    },

    {
        "Section": "Phase 3 Online",
        "Item": "Dual-flow mean overlimits rate",
        "Value": "177.2 events/s",
        "Notes": "Queue pressure"
    },

    {
        "Section": "Phase 3 Online",
        "Item": "Mean time to risk < 0.5",
        "Value": "1.73 s",
        "Notes": "After traffic termination"
    },

    {
        "Section": "Phase 3 Online",
        "Item": "Mean time to low-risk baseline",
        "Value": "2.36 s",
        "Notes": "Consistent with 2 s observation window"
    },


    # --------------------------------------------------------
    # Packet statistics
    # --------------------------------------------------------

    {
        "Section": "Packet Statistics",
        "Item": "Mean spine packet rate",
        "Value": "44.55 pkt/s",
        "Notes": "n = 6 measured runs"
    },

    {
        "Section": "Packet Statistics",
        "Item": "Mean spine throughput",
        "Value": "4.17 Mbit/s",
        "Notes": "n = 6 measured runs"
    },

    {
        "Section": "Packet Statistics",
        "Item": "Mean delivery ratio",
        "Value": "0.984",
        "Notes": "h2_rx / h1_tx"
    },


    # --------------------------------------------------------
    # EVPN / VXLAN verification
    # --------------------------------------------------------

    {
        "Section": "EVPN/VXLAN",
        "Item": "VXLAN VNI",
        "Value": "100",
        "Notes": "vxlan100"
    },

    {
        "Section": "EVPN/VXLAN",
        "Item": "VXLAN UDP port",
        "Value": "4789",
        "Notes": "Confirmed by packet capture"
    },

    {
        "Section": "EVPN/VXLAN",
        "Item": "VTEP addresses",
        "Value": "1.1.1.1 ↔ 2.2.2.2",
        "Notes": "leaf1 ↔ leaf2"
    },

    {
        "Section": "EVPN/VXLAN",
        "Item": "BGP EVPN control plane",
        "Value": "Verified",
        "Notes": "Established peers, Type-2/Type-3 routes"
    },

    {
        "Section": "EVPN/VXLAN",
        "Item": "VXLAN data plane",
        "Value": "Verified",
        "Notes": "UDP/4789, VNI 100, inner h1 ↔ h2 traffic"
    },
]


df = pd.DataFrame(rows)


# ============================================================
# Save CSV
# ============================================================

CSV_FILE = (
    DATA_DIR
    / "thesis_key_results.csv"
)

df.to_csv(
    CSV_FILE,
    index=False
)


# ============================================================
# Build display table
# ============================================================

display_df = df.copy()

fig_height = 0.42 * len(display_df) + 2.5

fig, ax = plt.subplots(
    figsize=(15, fig_height)
)

ax.axis(
    "off"
)


table = ax.table(
    cellText=display_df.values,
    colLabels=display_df.columns,
    cellLoc="left",
    colLoc="left",
    loc="center",
    colWidths=[
        0.18,
        0.32,
        0.22,
        0.28
    ]
)


table.auto_set_font_size(
    False
)

table.set_fontsize(
    9
)

table.scale(
    1,
    1.65
)


for col in range(
    len(display_df.columns)
):

    table[
        (0, col)
    ].set_text_props(
        weight="bold"
    )


# Bold section names
previous_section = None

for row_index in range(
    1,
    len(display_df) + 1
):

    section = (
        display_df.iloc[
            row_index - 1
        ]["Section"]
    )

    if section != previous_section:

        table[
            (row_index, 0)
        ].set_text_props(
            weight="bold"
        )

    previous_section = section


ax.set_title(
    "Master Thesis Key Results Summary",
    fontsize=15,
    pad=20
)


fig.tight_layout()


PNG_FILE = (
    IMG_DIR
    / "thesis_key_results_summary.png"
)

PDF_FILE = (
    IMG_DIR
    / "thesis_key_results_summary.pdf"
)


fig.savefig(
    PNG_FILE,
    dpi=300,
    bbox_inches="tight"
)

fig.savefig(
    PDF_FILE,
    bbox_inches="tight"
)

plt.close(
    fig
)


# ============================================================
# Print
# ============================================================

print()
print(
    "=============================================="
)

print(
    " Master Thesis Key Results Summary"
)

print(
    "=============================================="
)

print()

print(
    df.to_string(
        index=False
    )
)

print()

print(
    "Saved:"
)

print(
    CSV_FILE
)

print(
    PNG_FILE
)

print(
    PDF_FILE
)

print()