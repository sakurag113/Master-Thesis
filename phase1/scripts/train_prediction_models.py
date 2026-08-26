import pandas as pd
import numpy as np

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix
)


# ==========================================
# Configuration
# ==========================================

DATA_FILE = (
    "/home/yuxsun/phase2/data/"
    "prediction_dataset.csv"
)

RANDOM_STATE = 42


# ==========================================
# Load dataset
# ==========================================

df = pd.read_csv(DATA_FILE)

print()
print("=== Prediction Model Pilot Validation ===")
print()

print("Total samples =", len(df))
print("Total runs =", df["run"].nunique())


# ==========================================
# Feature selection
# ==========================================

FEATURES = [
    "bottleneck_mbit",
    "requested_flows_mean",
    "active_flows_mean",

    "mean_rtt",
    "std_rtt",
    "min_rtt",
    "max_rtt",
    "median_rtt",
    "p95_rtt",
    "rtt_slope",

    "mean_overlimits_rate",
    "max_overlimits_rate",
    "std_overlimits_rate",
    "overlimits_rate_slope",

    "current_high_ratio"
]

TARGET = "label"


# ==========================================
# Split by RUN
# ==========================================

runs = sorted(
    df["run"].unique()
)

print()
print("Runs:")
print(runs)

# 12 pilot runs:
# use 8 train + 4 test
#
# Keep complete runs together.
# We deliberately do NOT randomly split individual rows.

rng = np.random.default_rng(
    RANDOM_STATE
)

shuffled_runs = runs.copy()

rng.shuffle(
    shuffled_runs
)

train_runs = shuffled_runs[:8]
test_runs = shuffled_runs[8:]


print()
print("=== Run-level Split ===")
print()

print("Train runs:")
for run in train_runs:
    print(" ", run)

print()

print("Test runs:")
for run in test_runs:
    print(" ", run)


train_df = df[
    df["run"].isin(train_runs)
].copy()

test_df = df[
    df["run"].isin(test_runs)
].copy()


print()
print("Train samples =", len(train_df))
print("Test samples =", len(test_df))

print(
    "Train positive ratio =",
    f"{train_df[TARGET].mean():.2%}"
)

print(
    "Test positive ratio =",
    f"{test_df[TARGET].mean():.2%}"
)


# ==========================================
# Prepare data
# ==========================================

X_train = train_df[FEATURES]
y_train = train_df[TARGET]

X_test = test_df[FEATURES]
y_test = test_df[TARGET]


# ==========================================
# Evaluation helper
# ==========================================

def evaluate_model(
    name,
    y_true,
    y_pred,
    y_prob=None
):

    print()
    print(
        f"=== {name} ==="
    )
    print()

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

    print(
        "Accuracy =",
        f"{accuracy:.3f}"
    )

    print(
        "Precision =",
        f"{precision:.3f}"
    )

    print(
        "Recall =",
        f"{recall:.3f}"
    )

    print(
        "F1-score =",
        f"{f1:.3f}"
    )

    if y_prob is not None:

        # AUC requires both classes
        if len(np.unique(y_true)) == 2:

            roc_auc = roc_auc_score(
                y_true,
                y_prob
            )

            pr_auc = average_precision_score(
                y_true,
                y_prob
            )

            print(
                "ROC-AUC =",
                f"{roc_auc:.3f}"
            )

            print(
                "PR-AUC =",
                f"{pr_auc:.3f}"
            )

    print()
    print("Confusion matrix:")
    print(
        confusion_matrix(
            y_true,
            y_pred
        )
    )


# ==========================================
# Model 0:
# Persistence baseline
# ==========================================
#
# Predict:
# future state = current state

persistence_pred = (
    test_df["current_high"]
    .astype(int)
    .values
)

evaluate_model(
    "Persistence Baseline",
    y_test,
    persistence_pred
)


# ==========================================
# Model 1:
# Logistic Regression
# ==========================================

scaler = StandardScaler()

X_train_scaled = (
    scaler.fit_transform(
        X_train
    )
)

X_test_scaled = (
    scaler.transform(
        X_test
    )
)

logistic = LogisticRegression(
    max_iter=2000,
    class_weight="balanced",
    random_state=RANDOM_STATE
)

logistic.fit(
    X_train_scaled,
    y_train
)

logistic_pred = (
    logistic.predict(
        X_test_scaled
    )
)

logistic_prob = (
    logistic.predict_proba(
        X_test_scaled
    )[:, 1]
)

evaluate_model(
    "Logistic Regression",
    y_test,
    logistic_pred,
    logistic_prob
)


# ==========================================
# Logistic coefficients
# ==========================================

coef_df = pd.DataFrame({
    "feature": FEATURES,
    "coefficient":
        logistic.coef_[0]
})

coef_df[
    "abs_coefficient"
] = (
    coef_df[
        "coefficient"
    ].abs()
)

coef_df = (
    coef_df.sort_values(
        "abs_coefficient",
        ascending=False
    )
)

print()
print(
    "=== Logistic Regression "
    "Feature Coefficients ==="
)
print()

print(
    coef_df[
        [
            "feature",
            "coefficient"
        ]
    ].to_string(
        index=False
    )
)


# ==========================================
# Model 2:
# Random Forest
# ==========================================

rf = RandomForestClassifier(
    n_estimators=300,
    max_depth=6,
    min_samples_leaf=3,
    class_weight="balanced",
    random_state=RANDOM_STATE
)

rf.fit(
    X_train,
    y_train
)

rf_pred = (
    rf.predict(
        X_test
    )
)

rf_prob = (
    rf.predict_proba(
        X_test
    )[:, 1]
)

evaluate_model(
    "Random Forest",
    y_test,
    rf_pred,
    rf_prob
)


# ==========================================
# Random Forest feature importance
# ==========================================

importance_df = pd.DataFrame({
    "feature": FEATURES,
    "importance":
        rf.feature_importances_
})

importance_df = (
    importance_df.sort_values(
        "importance",
        ascending=False
    )
)

print()
print(
    "=== Random Forest "
    "Feature Importance ==="
)
print()

print(
    importance_df.to_string(
        index=False
    )
)


# ==========================================
# Early-warning evaluation
# ==========================================
#
# Only evaluate samples where the CURRENT
# observation window is still NORMAL.
#
# This asks:
# Can we predict NORMAL -> HIGH?

early_mask = (
    test_df["current_high"] == 0
)

early_test = (
    test_df.loc[
        early_mask
    ].copy()
)

print()
print(
    "================================"
)
print(
    "=== Early-warning Evaluation ==="
)
print(
    "================================"
)
print()

print(
    "Current-NORMAL test samples =",
    len(early_test)
)

print(
    "NORMAL -> HIGH samples =",
    int(
        early_test[TARGET].sum()
    )
)

print(
    "NORMAL -> NORMAL samples =",
    int(
        len(early_test)
        - early_test[TARGET].sum()
    )
)


if len(early_test) > 0:

    X_early = (
        early_test[FEATURES]
    )

    y_early = (
        early_test[TARGET]
    )


    # --------------------------------------
    # Persistence baseline
    # --------------------------------------
    #
    # Because current state is NORMAL,
    # persistence predicts every future
    # state as NORMAL.

    persistence_early = np.zeros(
        len(early_test),
        dtype=int
    )

    evaluate_model(
        "Early-warning Persistence Baseline",
        y_early,
        persistence_early
    )


    # --------------------------------------
    # Logistic Regression
    # --------------------------------------

    X_early_scaled = (
        scaler.transform(
            X_early
        )
    )

    early_logistic_pred = (
        logistic.predict(
            X_early_scaled
        )
    )

    early_logistic_prob = (
        logistic.predict_proba(
            X_early_scaled
        )[:, 1]
    )

    evaluate_model(
        "Early-warning Logistic Regression",
        y_early,
        early_logistic_pred,
        early_logistic_prob
    )


    # --------------------------------------
    # Random Forest
    # --------------------------------------

    early_rf_pred = (
        rf.predict(
            X_early
        )
    )

    early_rf_prob = (
        rf.predict_proba(
            X_early
        )[:, 1]
    )

    evaluate_model(
        "Early-warning Random Forest",
        y_early,
        early_rf_pred,
        early_rf_prob
    )


print()
print(
    "=== Pilot prediction validation finished ==="
)