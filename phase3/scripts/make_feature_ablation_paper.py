#!/usr/bin/env python3

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# Paths
# ============================================================

PHASE2_DIR = Path.home() / "phase2"

INPUT_FILE = (
    PHASE2_DIR
    / "data"
    / "final_model_summary.csv"
)

OUTPUT_DIR = (
    PHASE2_DIR
    / "img"
)

OUTPUT_DATA_DIR = (
    PHASE2_DIR
    / "data"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# Load data
# ============================================================

df = pd.read_csv(INPUT_FILE)

print()
print("Columns:")
print(df.columns.tolist())

print()
print("Feature sets found:")
print(df["feature_set"].unique())

print()


# ============================================================
# Select early-warning Random Forest results
# ============================================================

rf = df[
    (df["task"] == "early_warning")
    &
    (df["model"] == "Random Forest")
].copy()


# ============================================================
# Keep only feature-ablation sets
# ============================================================

FEATURE_SETS = [
    "All Features",
    "No Current High Ratio",
    "Queue + Traffic Only",
]

rf = rf[
    rf["feature_set"].isin(
        FEATURE_SETS
    )
].copy()


# ============================================================
# Metrics
# ============================================================

METRICS = [
    "f1",
    "roc_auc",
    "pr_auc",
]

METRIC_LABELS = {
    "f1": "F1",
    "roc_auc": "ROC-AUC",
    "pr_auc": "PR-AUC",
}


# ============================================================
# Print selected data
# ============================================================

print(
    "Selected early-warning Random Forest rows:"
)

print()

print(
    rf[
        [
            "feature_set",
            "metric",
            "mean",
            "std",
        ]
    ].to_string(
        index=False
    )
)

print()


# ============================================================
# Build paper table
# ============================================================

table_rows = []

for feature_set in FEATURE_SETS:

    subset = rf[
        rf["feature_set"] == feature_set
    ]

    row = {
        "Feature Set":
            feature_set
    }

    for metric in METRICS:

        metric_row = subset[
            subset["metric"] == metric
        ]

        if metric_row.empty:

            row[
                METRIC_LABELS[metric]
            ] = "N/A"

            continue

        mean_value = float(
            metric_row.iloc[0]["mean"]
        )

        std_value = float(
            metric_row.iloc[0]["std"]
        )

        row[
            METRIC_LABELS[metric]
        ] = (
            f"{mean_value:.3f} ± "
            f"{std_value:.3f}"
        )

    table_rows.append(row)


table = pd.DataFrame(
    table_rows
)


TABLE_FILE = (
    OUTPUT_DATA_DIR
    / "feature_ablation_paper_table.csv"
)


table.to_csv(
    TABLE_FILE,
    index=False
)


print()
print(
    "=============================================="
)

print(
    " Feature Ablation Paper Table"
)

print(
    "=============================================="
)

print()

print(
    table.to_string(
        index=False
    )
)

print()


# ============================================================
# Prepare values for plot
# ============================================================

means = {}
stds = {}


for feature_set in FEATURE_SETS:

    subset = rf[
        rf["feature_set"] == feature_set
    ]

    means[feature_set] = []
    stds[feature_set] = []

    for metric in METRICS:

        metric_row = subset[
            subset["metric"] == metric
        ]

        if metric_row.empty:

            means[
                feature_set
            ].append(
                np.nan
            )

            stds[
                feature_set
            ].append(
                np.nan
            )

        else:

            means[
                feature_set
            ].append(
                float(
                    metric_row.iloc[0]["mean"]
                )
            )

            stds[
                feature_set
            ].append(
                float(
                    metric_row.iloc[0]["std"]
                )
            )


# ============================================================
# Plot
# ============================================================

x = np.arange(
    len(METRICS)
)

width = 0.24


fig, ax = plt.subplots(
    figsize=(10, 6)
)


offsets = [
    -width,
    0,
    width,
]


for feature_set, offset in zip(
    FEATURE_SETS,
    offsets
):

    values = means[
        feature_set
    ]

    errors = stds[
        feature_set
    ]

    bars = ax.bar(
        x + offset,
        values,
        width,
        yerr=errors,
        capsize=4,
        label=feature_set
    )

    # --------------------------------------------------------
    # Value labels
    # --------------------------------------------------------

    for bar, value in zip(
        bars,
        values
    ):

        if np.isnan(value):
            continue

        ax.text(
            bar.get_x()
            +
            bar.get_width() / 2,
            bar.get_height()
            +
            0.015,
            f"{value:.3f}",
            ha="center",
            va="bottom",
            fontsize=9
        )


# ============================================================
# Plot formatting
# ============================================================

ax.set_ylabel(
    "Score"
)

ax.set_xlabel(
    "Evaluation metric"
)

ax.set_xticks(
    x
)

ax.set_xticklabels(
    [
        METRIC_LABELS[m]
        for m in METRICS
    ]
)

ax.set_ylim(
    0,
    1.05
)

ax.set_title(
    "Early-Warning Feature Ablation "
    "(Random Forest)"
)

ax.grid(
    axis="y",
    alpha=0.20
)

ax.legend(
    loc="upper left",
    frameon=True
)

fig.tight_layout()


# ============================================================
# Save figure
# ============================================================

PNG_FILE = (
    OUTPUT_DIR
    / "feature_ablation_paper.png"
)

PDF_FILE = (
    OUTPUT_DIR
    / "feature_ablation_paper.pdf"
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
# Finish
# ============================================================

print(
    "Saved table:"
)

print(
    TABLE_FILE
)

print()

print(
    "Saved figure:"
)

print(
    PNG_FILE
)

print(
    PDF_FILE
)

print()