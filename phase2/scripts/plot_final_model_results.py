import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ==========================================
# Configuration
# ==========================================

SUMMARY_FILE = (
    "/home/yuxsun/phase2/data/"
    "final_model_summary.csv"
)

EARLY_FILE = (
    "/home/yuxsun/phase2/data/"
    "final_early_warning_cv_results.csv"
)

PLOT_DIR = (
    "/home/yuxsun/phase2/plots"
)


# ==========================================
# Load data
# ==========================================

summary = pd.read_csv(
    SUMMARY_FILE
)

early = pd.read_csv(
    EARLY_FILE
)


# ==========================================
# Helper
# ==========================================

def get_metric(
    task,
    feature_set,
    model,
    metric
):

    row = summary[
        (summary["task"] == task)
        &
        (
            summary["feature_set"]
            == feature_set
        )
        &
        (
            summary["model"]
            == model
        )
        &
        (
            summary["metric"]
            == metric
        )
    ]

    if len(row) == 0:
        return np.nan, np.nan

    return (
        row["mean"].iloc[0],
        row["std"].iloc[0]
    )


# ==========================================
# Figure 1
# General Prediction
# ==========================================

models = [
    "Persistence",
    "Logistic Regression",
    "Random Forest"
]

metrics = [
    "f1",
    "roc_auc",
    "pr_auc"
]

metric_labels = [
    "F1",
    "ROC-AUC",
    "PR-AUC"
]


values = []
errors = []

for model in models:

    model_values = []
    model_errors = []

    for metric in metrics:

        if model == "Persistence":

            mean, std = get_metric(
                "general",
                "Baseline",
                model,
                metric
            )

        else:

            mean, std = get_metric(
                "general",
                "All Features",
                model,
                metric
            )

        model_values.append(
            mean
        )

        model_errors.append(
            std
        )

    values.append(
        model_values
    )

    errors.append(
        model_errors
    )


values = np.array(
    values
)

errors = np.array(
    errors
)


x = np.arange(
    len(metric_labels)
)

width = 0.25


plt.figure(
    figsize=(9, 5.5)
)


for i, model in enumerate(models):

    plt.bar(
        x
        + (i - 1) * width,
        values[i],
        width,
        yerr=errors[i],
        capsize=4,
        label=model
    )


plt.xticks(
    x,
    metric_labels
)

plt.ylim(
    0,
    1.05
)

plt.ylabel(
    "Score"
)

plt.title(
    "General Prediction Performance"
)

plt.legend()

plt.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    f"{PLOT_DIR}/"
    "final_general_prediction.png",
    dpi=300
)

plt.show()


# ==========================================
# Figure 2
# Early-warning Prediction
# ==========================================

values = []
errors = []

for model in models:

    model_values = []
    model_errors = []

    for metric in metrics:

        if model == "Persistence":

            mean, std = get_metric(
                "early_warning",
                "Baseline",
                model,
                metric
            )

        else:

            mean, std = get_metric(
                "early_warning",
                "All Features",
                model,
                metric
            )

        model_values.append(
            mean
        )

        model_errors.append(
            std
        )

    values.append(
        model_values
    )

    errors.append(
        model_errors
    )


values = np.array(
    values
)

errors = np.array(
    errors
)


plt.figure(
    figsize=(9, 5.5)
)


for i, model in enumerate(models):

    plt.bar(
        x
        + (i - 1) * width,
        values[i],
        width,
        yerr=errors[i],
        capsize=4,
        label=model
    )


plt.xticks(
    x,
    metric_labels
)

plt.ylim(
    0,
    1.05
)

plt.ylabel(
    "Score"
)

plt.title(
    "Early-warning Prediction Performance"
)

plt.legend()

plt.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    f"{PLOT_DIR}/"
    "final_early_warning_prediction.png",
    dpi=300
)

plt.show()


# ==========================================
# Figure 3
# Feature Ablation
# Random Forest Early-warning
# ==========================================

feature_sets = [
    "All Features",
    "No Current High Ratio",
    "Queue + Traffic Only"
]

feature_labels = [
    "All Features",
    "No Current\nHigh Ratio",
    "Queue + Traffic\nOnly"
]

ablation_metrics = [
    "f1",
    "roc_auc",
    "pr_auc"
]

ablation_labels = [
    "F1",
    "ROC-AUC",
    "PR-AUC"
]


values = []
errors = []

for feature_set in feature_sets:

    feature_values = []
    feature_errors = []

    for metric in ablation_metrics:

        mean, std = get_metric(
            "early_warning",
            feature_set,
            "Random Forest",
            metric
        )

        feature_values.append(
            mean
        )

        feature_errors.append(
            std
        )

    values.append(
        feature_values
    )

    errors.append(
        feature_errors
    )


values = np.array(
    values
)

errors = np.array(
    errors
)


x_ablation = np.arange(
    len(ablation_labels)
)

width = 0.25


plt.figure(
    figsize=(9, 5.5)
)


for i, label in enumerate(
    feature_labels
):

    plt.bar(
        x_ablation
        + (i - 1) * width,
        values[i],
        width,
        yerr=errors[i],
        capsize=4,
        label=label
    )


plt.xticks(
    x_ablation,
    ablation_labels
)

plt.ylim(
    0,
    1.05
)

plt.ylabel(
    "Score"
)

plt.title(
    "Early-warning Feature Ablation "
    "(Random Forest)"
)

plt.legend()

plt.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    f"{PLOT_DIR}/"
    "final_feature_ablation.png",
    dpi=300
)

plt.show()


# ==========================================
# Figure 4
# Early-warning samples per fold
# ==========================================

sample_summary = (
    early[
        early["model"]
        ==
        "Logistic Regression"
    ]
    .groupby(
        "fold"
    )[
        [
            "early_samples",
            "early_positive_samples"
        ]
    ]
    .first()
    .reset_index()
)


plt.figure(
    figsize=(8, 5)
)

plt.bar(
    sample_summary["fold"],
    sample_summary[
        "early_positive_samples"
    ]
)

plt.xlabel(
    "Fold"
)

plt.ylabel(
    "NORMAL → HIGH Samples"
)

plt.title(
    "Early-warning Positive Samples "
    "Across 5 Folds"
)

plt.xticks(
    sample_summary["fold"]
)

plt.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    f"{PLOT_DIR}/"
    "final_early_positive_samples.png",
    dpi=300
)

plt.show()


print()
print(
    "Saved:"
)

print(
    f"{PLOT_DIR}/"
    "final_general_prediction.png"
)

print(
    f"{PLOT_DIR}/"
    "final_early_warning_prediction.png"
)

print(
    f"{PLOT_DIR}/"
    "final_feature_ablation.png"
)

print(
    f"{PLOT_DIR}/"
    "final_early_positive_samples.png"
)