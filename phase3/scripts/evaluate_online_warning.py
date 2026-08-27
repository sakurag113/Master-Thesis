#!/usr/bin/env python3

import os

import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix
)


# ============================================================
# Paths
# ============================================================

INPUT_FILE = (
    "/home/yuxsun/phase3/logs/"
    "online_validation_log.csv"
)

DATA_DIR = (
    "/home/yuxsun/phase3/data"
)

LABELED_FILE = (
    "/home/yuxsun/phase3/data/"
    "online_validation_labeled.csv"
)

METRICS_FILE = (
    "/home/yuxsun/phase3/data/"
    "online_validation_metrics.csv"
)

os.makedirs(
    DATA_DIR,
    exist_ok=True
)


# ============================================================
# Same definition as Phase 2
# ============================================================

OBSERVATION_WINDOW = 2.0

PREDICTION_HORIZON = 2.0

RTT_THRESHOLD = 75.0

HIGH_RATIO_THRESHOLD = 0.50

WARNING_THRESHOLD = 0.50

MIN_RTT_SAMPLES = 2


# ============================================================
# Load data
# ============================================================

df = pd.read_csv(
    INPUT_FILE
)

df = df.sort_values(
    "time_s"
).reset_index(
    drop=True
)


print()
print(
    "=== Phase 3 Online Early-warning Evaluation ==="
)
print()

print(
    f"Raw telemetry samples = {len(df)}"
)


# ============================================================
# Select actual prediction records
# ============================================================

prediction_rows = df[
    df["future_high_probability"]
    .notna()
].copy()


print(
    f"Online predictions = "
    f"{len(prediction_rows)}"
)

print()


# ============================================================
# Build real future labels
# ============================================================

records = []


for _, row in prediction_rows.iterrows():

    t = float(
        row["time_s"]
    )


    # --------------------------------------------------------
    # Current 2-second observation RTT window
    # --------------------------------------------------------

    current_window = df[
        (df["time_s"] > t - OBSERVATION_WINDOW)
        &
        (df["time_s"] <= t)
    ]

    current_rtt = (
        current_window["rtt_ms"]
        .dropna()
    )


    # --------------------------------------------------------
    # Future 2-second RTT window
    # --------------------------------------------------------

    future_window = df[
        (df["time_s"] > t)
        &
        (
            df["time_s"]
            <= t + PREDICTION_HORIZON
        )
    ]

    future_rtt = (
        future_window["rtt_ms"]
        .dropna()
    )


    if (
        len(current_rtt)
        < MIN_RTT_SAMPLES
        or
        len(future_rtt)
        < MIN_RTT_SAMPLES
    ):

        continue


    # --------------------------------------------------------
    # Current state
    # --------------------------------------------------------

    current_high_ratio = float(
        (
            current_rtt
            > RTT_THRESHOLD
        ).mean()
    )

    current_high = int(
        current_high_ratio
        >= HIGH_RATIO_THRESHOLD
    )


    # --------------------------------------------------------
    # Future state
    # --------------------------------------------------------

    future_high_ratio = float(
        (
            future_rtt
            > RTT_THRESHOLD
        ).mean()
    )

    future_high = int(
        future_high_ratio
        >= HIGH_RATIO_THRESHOLD
    )


    records.append({

        "time_s":
            t,

        "active_flows":
            row["active_flows"],

        "rtt_ms":
            row["rtt_ms"],

        "future_high_probability":
            row["future_high_probability"],

        "prediction":
            int(
                row["prediction"]
            ),

        "current_high_ratio":
            current_high_ratio,

        "current_high":
            current_high,

        "future_high_ratio":
            future_high_ratio,

        "future_high":
            future_high,

        "transition":
            (
                ("HIGH" if current_high else "NORMAL")
                + "_TO_"
                + ("HIGH" if future_high else "NORMAL")
            )
    })


labeled = pd.DataFrame(
    records
)


if len(labeled) == 0:

    print(
        "ERROR:"
    )

    print(
        "No valid labeled predictions were produced."
    )

    raise SystemExit(1)


labeled.to_csv(
    LABELED_FILE,
    index=False
)


# ============================================================
# Evaluation helper
# ============================================================

def evaluate_subset(
    data,
    evaluation_name
):

    y_true = (
        data["future_high"]
        .astype(int)
        .values
    )

    y_prob = (
        data["future_high_probability"]
        .astype(float)
        .values
    )

    y_pred = (
        y_prob
        >= WARNING_THRESHOLD
    ).astype(int)


    accuracy = accuracy_score(
        y_true,
        y_pred
    )

    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0
    )


    if len(
        np.unique(
            y_true
        )
    ) >= 2:

        roc_auc = roc_auc_score(
            y_true,
            y_prob
        )

        pr_auc = average_precision_score(
            y_true,
            y_prob
        )

    else:

        roc_auc = np.nan
        pr_auc = np.nan


    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1]
    )

    tn, fp, fn, tp = (
        cm.ravel()
    )


    return {

        "evaluation":
            evaluation_name,

        "samples":
            len(data),

        "positive_samples":
            int(
                y_true.sum()
            ),

        "positive_ratio":
            float(
                y_true.mean()
            ),

        "accuracy":
            accuracy,

        "precision":
            precision,

        "recall":
            recall,

        "f1":
            f1,

        "roc_auc":
            roc_auc,

        "pr_auc":
            pr_auc,

        "tn":
            int(tn),

        "fp":
            int(fp),

        "fn":
            int(fn),

        "tp":
            int(tp)
    }


# ============================================================
# General prediction
# ============================================================

general_result = evaluate_subset(
    labeled,
    "General"
)


# ============================================================
# Early-warning evaluation
#
# Only predictions where current RTT window is NORMAL
# ============================================================

early_df = labeled[
    labeled["current_high"] == 0
].copy()


if len(early_df) > 0:

    early_result = evaluate_subset(
        early_df,
        "Early-warning"
    )

else:

    early_result = None


# ============================================================
# Save metrics
# ============================================================

results = [
    general_result
]

if early_result is not None:

    results.append(
        early_result
    )


metrics_df = pd.DataFrame(
    results
)

metrics_df.to_csv(
    METRICS_FILE,
    index=False
)


# ============================================================
# Print dataset summary
# ============================================================

print(
    "=== Transition Distribution ==="
)
print()

print(
    labeled[
        "transition"
    ].value_counts()
)

print()


# ============================================================
# Print evaluation results
# ============================================================

for result in results:

    print(
        "========================================"
    )

    print(
        result["evaluation"]
    )

    print(
        "========================================"
    )

    print(
        f"Samples        = "
        f"{result['samples']}"
    )

    print(
        f"Positive       = "
        f"{result['positive_samples']}"
    )

    print(
        f"Positive ratio = "
        f"{result['positive_ratio']:.4f}"
    )

    print()

    print(
        f"Accuracy       = "
        f"{result['accuracy']:.4f}"
    )

    print(
        f"Precision      = "
        f"{result['precision']:.4f}"
    )

    print(
        f"Recall         = "
        f"{result['recall']:.4f}"
    )

    print(
        f"F1             = "
        f"{result['f1']:.4f}"
    )


    if np.isnan(
        result["roc_auc"]
    ):

        print(
            "ROC-AUC        = N/A"
        )

    else:

        print(
            f"ROC-AUC        = "
            f"{result['roc_auc']:.4f}"
        )


    if np.isnan(
        result["pr_auc"]
    ):

        print(
            "PR-AUC         = N/A"
        )

    else:

        print(
            f"PR-AUC         = "
            f"{result['pr_auc']:.4f}"
        )


    print()

    print(
        "Confusion matrix:"
    )

    print(
        f"TN = {result['tn']}   "
        f"FP = {result['fp']}"
    )

    print(
        f"FN = {result['fn']}   "
        f"TP = {result['tp']}"
    )

    print()


print(
    "Labeled predictions saved to:"
)

print(
    LABELED_FILE
)

print()

print(
    "Metrics saved to:"
)

print(
    METRICS_FILE
)

print()