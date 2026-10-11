#!/usr/bin/env python3

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# Paths
# ============================================================

PHASE3_DIR = Path.home() / "phase3"

DATA_DIR = (
    PHASE3_DIR
    / "data"
)

IMG_DIR = (
    PHASE3_DIR
    / "img"
)

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

IMG_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# Feature definitions
# ============================================================

rows = [
    {
        "Feature": "bottleneck_mbit",
        "Category": "Configuration",
        "Meaning":
            "Configured bottleneck link capacity in Mbit/s."
    },
    {
        "Feature": "requested_flows_mean",
        "Category": "Traffic",
        "Meaning":
            "Mean number of requested traffic flows "
            "within the observation window."
    },
    {
        "Feature": "active_flows_mean",
        "Category": "Traffic",
        "Meaning":
            "Mean number of actually established active TCP "
            "flows within the observation window."
    },
    {
        "Feature": "mean_overlimits_rate",
        "Category": "Queue",
        "Meaning":
            "Mean rate of TBF queue overlimit events "
            "within the observation window."
    },
    {
        "Feature": "max_overlimits_rate",
        "Category": "Queue",
        "Meaning":
            "Maximum queue overlimit-event rate "
            "observed within the window."
    },
    {
        "Feature": "std_overlimits_rate",
        "Category": "Queue",
        "Meaning":
            "Standard deviation of queue overlimit rate, "
            "representing variability in queue pressure."
    },
    {
        "Feature": "overlimits_rate_slope",
        "Category": "Queue",
        "Meaning":
            "Linear trend of queue overlimit rate "
            "over the observation window."
    },
]


df = pd.DataFrame(rows)


# ============================================================
# Save CSV
# ============================================================

CSV_FILE = (
    DATA_DIR
    / "online_feature_definition_table.csv"
)

df.to_csv(
    CSV_FILE,
    index=False
)


# ============================================================
# Make wrapped display text
# ============================================================

display_df = df.copy()

display_df["Meaning"] = [
    "Configured bottleneck link\ncapacity in Mbit/s.",

    "Mean number of requested traffic flows\n"
    "within the observation window.",

    "Mean number of actually established active TCP\n"
    "flows within the observation window.",

    "Mean rate of TBF queue overlimit events\n"
    "within the observation window.",

    "Maximum queue overlimit-event rate\n"
    "observed within the window.",

    "Standard deviation of queue overlimit rate,\n"
    "representing variability in queue pressure.",

    "Linear trend of queue overlimit rate\n"
    "over the observation window.",
]


# ============================================================
# Plot table
# ============================================================

fig, ax = plt.subplots(
    figsize=(14, 7)
)

ax.axis("off")


table = ax.table(
    cellText=display_df.values,
    colLabels=display_df.columns,
    cellLoc="left",
    colLoc="left",
    loc="center",
    colWidths=[
        0.25,
        0.16,
        0.59,
    ],
)


table.auto_set_font_size(False)

table.set_fontsize(10)

table.scale(
    1,
    2.2
)


# ============================================================
# Header formatting
# ============================================================

for col in range(
    len(display_df.columns)
):

    cell = table[
        (0, col)
    ]

    cell.set_text_props(
        weight="bold"
    )


# ============================================================
# Row alignment
# ============================================================

for row in range(
    1,
    len(display_df) + 1
):

    for col in range(
        len(display_df.columns)
    ):

        cell = table[
            (row, col)
        ]

        cell.set_text_props(
            va="center"
        )


ax.set_title(
    "Final Queue + Traffic Feature Set",
    fontsize=14,
    pad=20
)


fig.tight_layout()


# ============================================================
# Save PNG + PDF
# ============================================================

PNG_FILE = (
    IMG_DIR
    / "online_feature_definition_table.png"
)

PDF_FILE = (
    IMG_DIR
    / "online_feature_definition_table.pdf"
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

plt.close(fig)


# ============================================================
# Save LaTeX table
# ============================================================

TEX_FILE = (
    DATA_DIR
    / "online_feature_definition_table.tex"
)


latex_text = df.to_latex(
    index=False,
    escape=True,
    caption=(
        "Final Queue + Traffic feature set "
        "used by the online Random Forest model."
    ),
    label="tab:online_features",
    column_format="lll",
)


with open(
    TEX_FILE,
    "w"
) as f:

    f.write(
        latex_text
    )


# ============================================================
# Print result
# ============================================================

print()
print(
    "=============================================="
)

print(
    " Feature Definition Table Generated"
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
    "CSV:"
)

print(
    CSV_FILE
)

print()

print(
    "PNG:"
)

print(
    PNG_FILE
)

print()

print(
    "PDF:"
)

print(
    PDF_FILE
)

print()

print(
    "LaTeX:"
)

print(
    TEX_FILE
)

print()