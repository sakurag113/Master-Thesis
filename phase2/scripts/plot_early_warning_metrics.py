#!/usr/bin/env python3

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import (
    roc_curve,
    roc_auc_score,
    precision_recall_curve,
    average_precision_score,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)


# ============================================================
# Paths
# ============================================================

PHASE2 = Path.home() / "phase2"

INPUT_FILE = (
    PHASE2
    / "data"
    / "final_early_warning_oof_predictions.csv"
)

OUTPUT_DATA = (
    PHASE2
    / "data"
    / "early_warning_metrics_interpretation.csv"
)

OUTPUT_ROC_PNG = (
    PHASE2
    / "plots"
    / "early_warning_roc_curve.png"
)

OUTPUT_ROC_PDF = (
    PHASE2
    / "plots"
    / "early_warning_roc_curve.pdf"
)

OUTPUT_PR_PNG = (
    PHASE2
    / "plots"
    / "early_warning_pr_curve.png"
)

OUTPUT_PR_PDF = (
    PHASE2
    / "plots"
    / "early_warning_pr_curve.pdf"
)

OUTPUT_CM_PNG = (
    PHASE2
    / "plots"
    / "early_warning_confusion_matrix.png"
)

OUTPUT_CM_PDF = (
    PHASE2
    / "plots"
    / "early_warning_confusion_matrix.pdf"
)


(PHASE2 / "plots").mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# Load OOF predictions
# ============================================================

df = pd.read_csv(
    INPUT_FILE
)


print()
print(
    "=== Early-Warning OOF Metrics Analysis ==="
)
print()


# ============================================================
# Select final deployed model
# ============================================================

model_df = df[
    (
        df["feature_set"]
        == "Queue + Traffic Only"
    )
    &
    (
        df["model"]
        == "Random Forest"
    )
].copy()


if len(model_df) == 0:

    raise RuntimeError(
        "Queue + Traffic Only / Random Forest "
        "predictions were not found."
    )


y_true = (
    model_df["y_true"]
    .astype(int)
    .to_numpy()
)

y_pred = (
    model_df["y_pred"]
    .astype(int)
    .to_numpy()
)

y_prob = (
    model_df["y_prob"]
    .astype(float)
    .to_numpy()
)


# ============================================================
# Basic counts
# ============================================================

n_samples = len(
    y_true
)

n_positive = int(
    np.sum(
        y_true == 1
    )
)

n_negative = int(
    np.sum(
        y_true == 0
    )
)

prevalence = (
    n_positive
    / n_samples
)


# ============================================================
# Pooled OOF metrics
# ============================================================

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

roc_auc = roc_auc_score(
    y_true,
    y_prob
)

pr_auc = average_precision_score(
    y_true,
    y_prob
)


# ============================================================
# Confusion matrix
# ============================================================

cm = confusion_matrix(
    y_true,
    y_pred,
    labels=[0, 1]
)

tn, fp, fn, tp = cm.ravel()


# ============================================================
# Print summary
# ============================================================

print(
    "Samples =",
    n_samples
)

print(
    "Positive samples =",
    n_positive
)

print(
    "Negative samples =",
    n_negative
)

print(
    "Positive prevalence =",
    f"{prevalence:.4f}",
    f"({prevalence:.2%})"
)

print()

print(
    "Pooled OOF Accuracy =",
    f"{accuracy:.4f}"
)

print(
    "Pooled OOF Precision =",
    f"{precision:.4f}"
)

print(
    "Pooled OOF Recall =",
    f"{recall:.4f}"
)

print(
    "Pooled OOF F1 =",
    f"{f1:.4f}"
)

print(
    "Pooled OOF ROC-AUC =",
    f"{roc_auc:.4f}"
)

print(
    "Pooled OOF PR-AUC =",
    f"{pr_auc:.4f}"
)

print()

print(
    "TN =",
    tn
)

print(
    "FP =",
    fp
)

print(
    "FN =",
    fn
)

print(
    "TP =",
    tp
)

print()


# ============================================================
# Save metrics summary
# ============================================================

summary = pd.DataFrame(
    [
        {
            "model":
                "Queue + Traffic Random Forest",

            "samples":
                n_samples,

            "positive_samples":
                n_positive,

            "negative_samples":
                n_negative,

            "positive_prevalence":
                prevalence,

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
                tn,

            "fp":
                fp,

            "fn":
                fn,

            "tp":
                tp,
        }
    ]
)


summary.to_csv(
    OUTPUT_DATA,
    index=False
)


# ============================================================
# ROC Curve
# ============================================================

fpr, tpr, _ = roc_curve(
    y_true,
    y_prob
)


fig, ax = plt.subplots(
    figsize=(7.5, 6)
)


ax.plot(
    fpr,
    tpr,
    linewidth=2,
    label=(
        "Queue + Traffic RF "
        f"(AUC = {roc_auc:.3f})"
    )
)


ax.plot(
    [0, 1],
    [0, 1],
    linestyle="--",
    linewidth=1.5,
    label="Random classifier"
)


ax.set_xlabel(
    "False Positive Rate"
)

ax.set_ylabel(
    "True Positive Rate"
)

ax.set_title(
    "Early-Warning ROC Curve"
)

ax.set_xlim(
    0,
    1
)

ax.set_ylim(
    0,
    1.02
)

ax.grid(
    alpha=0.2
)

ax.legend(
    loc="lower right"
)

fig.tight_layout()


fig.savefig(
    OUTPUT_ROC_PNG,
    dpi=300,
    bbox_inches="tight"
)

fig.savefig(
    OUTPUT_ROC_PDF,
    bbox_inches="tight"
)

plt.close(
    fig
)


# ============================================================
# Precision-Recall Curve
# ============================================================

pr_precision, pr_recall, _ = (
    precision_recall_curve(
        y_true,
        y_prob
    )
)


fig, ax = plt.subplots(
    figsize=(7.5, 6)
)


ax.plot(
    pr_recall,
    pr_precision,
    linewidth=2,
    label=(
        "Queue + Traffic RF "
        f"(AP = {pr_auc:.3f})"
    )
)


ax.axhline(
    y=prevalence,
    linestyle="--",
    linewidth=1.5,
    label=(
        "Random baseline "
        f"({prevalence:.3f})"
    )
)


ax.set_xlabel(
    "Recall"
)

ax.set_ylabel(
    "Precision"
)

ax.set_title(
    "Early-Warning Precision-Recall Curve"
)

ax.set_xlim(
    0,
    1
)

ax.set_ylim(
    0,
    1.02
)

ax.grid(
    alpha=0.2
)

ax.legend(
    loc="upper right"
)

fig.tight_layout()


fig.savefig(
    OUTPUT_PR_PNG,
    dpi=300,
    bbox_inches="tight"
)

fig.savefig(
    OUTPUT_PR_PDF,
    bbox_inches="tight"
)

plt.close(
    fig
)


# ============================================================
# Confusion Matrix
# ============================================================

fig, ax = plt.subplots(
    figsize=(6.5, 5.5)
)


image = ax.imshow(
    cm
)


fig.colorbar(
    image,
    ax=ax,
    fraction=0.046,
    pad=0.04
)


ax.set_xticks(
    [0, 1]
)

ax.set_yticks(
    [0, 1]
)


ax.set_xticklabels(
    [
        "Predicted NORMAL",
        "Predicted HIGH"
    ]
)

ax.set_yticklabels(
    [
        "Actual NORMAL",
        "Actual HIGH"
    ]
)


ax.set_xlabel(
    "Predicted class"
)

ax.set_ylabel(
    "Actual class"
)

ax.set_title(
    "Early-Warning Confusion Matrix"
)


threshold = (
    cm.max()
    / 2
)


for i in range(
    cm.shape[0]
):

    for j in range(
        cm.shape[1]
    ):

        value = (
            cm[i, j]
        )

        ax.text(
            j,
            i,
            str(
                value
            ),
            ha="center",
            va="center",
            fontsize=14,
            color=(
                "white"
                if value > threshold
                else "black"
            )
        )


fig.tight_layout()


fig.savefig(
    OUTPUT_CM_PNG,
    dpi=300,
    bbox_inches="tight"
)

fig.savefig(
    OUTPUT_CM_PDF,
    bbox_inches="tight"
)

plt.close(
    fig
)


# ============================================================
# Finish
# ============================================================

print(
    "Saved summary:"
)

print(
    OUTPUT_DATA
)

print()

print(
    "Saved ROC curve:"
)

print(
    OUTPUT_ROC_PNG
)

print(
    OUTPUT_ROC_PDF
)

print()

print(
    "Saved PR curve:"
)

print(
    OUTPUT_PR_PNG
)

print(
    OUTPUT_PR_PDF
)

print()

print(
    "Saved confusion matrix:"
)

print(
    OUTPUT_CM_PNG
)

print(
    OUTPUT_CM_PDF
)

print()

print(
    "=== Metrics analysis finished ==="
)