import pandas as pd
import numpy as np

from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score
)


# ==========================================
# Configuration
# ==========================================

DATA_FILE = (
    "/home/yuxsun/phase2/data/"
    "prediction_dataset.csv"
)

N_SPLITS = 4
RANDOM_STATE = 42


# ==========================================
# Load dataset
# ==========================================

df = pd.read_csv(DATA_FILE)

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
GROUP = "run"


print()
print("=== Grouped Cross-validation ===")
print()

print(
    "Total samples =",
    len(df)
)

print(
    "Total runs =",
    df["run"].nunique()
)

print(
    "Number of folds =",
    N_SPLITS
)

print()


# ==========================================
# Prepare data
# ==========================================

X = df[FEATURES]
y = df[TARGET]
groups = df[GROUP]

gkf = GroupKFold(
    n_splits=N_SPLITS
)


# ==========================================
# Storage
# ==========================================

general_results = []

early_results = []


# ==========================================
# Evaluation helper
# ==========================================

def safe_auc(
    y_true,
    y_prob
):

    if len(
        np.unique(y_true)
    ) < 2:

        return np.nan

    return roc_auc_score(
        y_true,
        y_prob
    )


def safe_pr_auc(
    y_true,
    y_prob
):

    if len(
        np.unique(y_true)
    ) < 2:

        return np.nan

    return average_precision_score(
        y_true,
        y_prob
    )


def calculate_metrics(
    y_true,
    y_pred,
    y_prob
):

    return {
        "precision":
            precision_score(
                y_true,
                y_pred,
                zero_division=0
            ),

        "recall":
            recall_score(
                y_true,
                y_pred,
                zero_division=0
            ),

        "f1":
            f1_score(
                y_true,
                y_pred,
                zero_division=0
            ),

        "roc_auc":
            safe_auc(
                y_true,
                y_prob
            ),

        "pr_auc":
            safe_pr_auc(
                y_true,
                y_prob
            )
    }


# ==========================================
# Cross-validation
# ==========================================

fold = 1

for train_index, test_index in gkf.split(
    X,
    y,
    groups
):

    train_df = df.iloc[
        train_index
    ].copy()

    test_df = df.iloc[
        test_index
    ].copy()


    print()
    print("=" * 60)
    print(
        f"Fold {fold}"
    )
    print("=" * 60)
    print()


    train_runs = sorted(
        train_df["run"]
        .unique()
    )

    test_runs = sorted(
        test_df["run"]
        .unique()
    )


    print(
        "Train runs:"
    )

    for run in train_runs:
        print(
            " ",
            run
        )

    print()

    print(
        "Test runs:"
    )

    for run in test_runs:
        print(
            " ",
            run
        )

    print()

    print(
        "Train samples =",
        len(train_df)
    )

    print(
        "Test samples =",
        len(test_df)
    )

    print(
        "Test positive ratio =",
        f"{test_df[TARGET].mean():.2%}"
    )


    # ======================================
    # Training data
    # ======================================

    X_train = train_df[
        FEATURES
    ]

    y_train = train_df[
        TARGET
    ]

    X_test = test_df[
        FEATURES
    ]

    y_test = test_df[
        TARGET
    ]


    # ======================================
    # Persistence baseline
    # ======================================

    persistence_pred = (
        test_df[
            "current_high"
        ]
        .astype(int)
        .values
    )

    persistence_prob = (
        test_df[
            "current_high_ratio"
        ]
        .values
    )

    metrics = calculate_metrics(
        y_test,
        persistence_pred,
        persistence_prob
    )

    metrics.update({
        "fold":
            fold,

        "model":
            "Persistence"
    })

    general_results.append(
        metrics
    )


    # ======================================
    # Logistic Regression
    # ======================================

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

    metrics = calculate_metrics(
        y_test,
        logistic_pred,
        logistic_prob
    )

    metrics.update({
        "fold":
            fold,

        "model":
            "Logistic Regression"
    })

    general_results.append(
        metrics
    )


    # ======================================
    # Random Forest
    # ======================================

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

    metrics = calculate_metrics(
        y_test,
        rf_pred,
        rf_prob
    )

    metrics.update({
        "fold":
            fold,

        "model":
            "Random Forest"
    })

    general_results.append(
        metrics
    )


    # ======================================
    # Early-warning subset
    # ======================================

    early_mask = (
        test_df[
            "current_high"
        ] == 0
    )

    early_test = (
        test_df.loc[
            early_mask
        ].copy()
    )


    print()
    print(
        "Early-warning samples =",
        len(early_test)
    )

    print(
        "NORMAL -> HIGH =",
        int(
            early_test[
                TARGET
            ].sum()
        )
    )

    print(
        "NORMAL -> NORMAL =",
        int(
            len(early_test)
            -
            early_test[
                TARGET
            ].sum()
        )
    )


    if len(
        early_test
    ) > 0:

        X_early = (
            early_test[
                FEATURES
            ]
        )

        y_early = (
            early_test[
                TARGET
            ]
        )


        # ----------------------------------
        # Early persistence
        # ----------------------------------

        early_persistence_pred = (
            np.zeros(
                len(early_test),
                dtype=int
            )
        )

        early_persistence_prob = (
            np.zeros(
                len(early_test)
            )
        )

        metrics = calculate_metrics(
            y_early,
            early_persistence_pred,
            early_persistence_prob
        )

        metrics.update({
            "fold":
                fold,

            "model":
                "Persistence",

            "samples":
                len(early_test),

            "positive_samples":
                int(
                    y_early.sum()
                )
        })

        early_results.append(
            metrics
        )


        # ----------------------------------
        # Early Logistic
        # ----------------------------------

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

        metrics = calculate_metrics(
            y_early,
            early_logistic_pred,
            early_logistic_prob
        )

        metrics.update({
            "fold":
                fold,

            "model":
                "Logistic Regression",

            "samples":
                len(early_test),

            "positive_samples":
                int(
                    y_early.sum()
                )
        })

        early_results.append(
            metrics
        )


        # ----------------------------------
        # Early Random Forest
        # ----------------------------------

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

        metrics = calculate_metrics(
            y_early,
            early_rf_pred,
            early_rf_prob
        )

        metrics.update({
            "fold":
                fold,

            "model":
                "Random Forest",

            "samples":
                len(early_test),

            "positive_samples":
                int(
                    y_early.sum()
                )
        })

        early_results.append(
            metrics
        )


    fold += 1


# ==========================================
# Convert to DataFrames
# ==========================================

general_df = pd.DataFrame(
    general_results
)

early_df = pd.DataFrame(
    early_results
)


# ==========================================
# Print general results
# ==========================================

print()
print()
print(
    "========================================"
)
print(
    "=== General Prediction CV Summary ==="
)
print(
    "========================================"
)
print()


for model in [
    "Persistence",
    "Logistic Regression",
    "Random Forest"
]:

    subset = general_df[
        general_df["model"]
        == model
    ]

    print(model)

    for metric in [
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "pr_auc"
    ]:

        print(
            f"  {metric}: "
            f"{subset[metric].mean():.3f} "
            f"+/- "
            f"{subset[metric].std(ddof=1):.3f}"
        )

    print()


# ==========================================
# Print early-warning results
# ==========================================

print()
print(
    "========================================"
)
print(
    "=== Early-warning CV Summary ==="
)
print(
    "========================================"
)
print()


for model in [
    "Persistence",
    "Logistic Regression",
    "Random Forest"
]:

    subset = early_df[
        early_df["model"]
        == model
    ]

    print(model)

    for metric in [
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "pr_auc"
    ]:

        print(
            f"  {metric}: "
            f"{subset[metric].mean():.3f} "
            f"+/- "
            f"{subset[metric].std(ddof=1):.3f}"
        )

    print()


# ==========================================
# Per-fold early-warning positives
# ==========================================

print()
print(
    "=== Early-warning Positive Samples "
    "per Fold ==="
)
print()

positive_summary = (
    early_df[
        early_df["model"]
        == "Logistic Regression"
    ][
        [
            "fold",
            "samples",
            "positive_samples"
        ]
    ]
)

print(
    positive_summary.to_string(
        index=False
    )
)


# ==========================================
# Save results
# ==========================================

GENERAL_OUTPUT = (
    "/home/yuxsun/phase2/data/"
    "pilot_general_cv_results.csv"
)

EARLY_OUTPUT = (
    "/home/yuxsun/phase2/data/"
    "pilot_early_warning_cv_results.csv"
)

general_df.to_csv(
    GENERAL_OUTPUT,
    index=False
)

early_df.to_csv(
    EARLY_OUTPUT,
    index=False
)

print()
print(
    "Saved general CV results to:"
)
print(
    GENERAL_OUTPUT
)

print()
print(
    "Saved early-warning CV results to:"
)
print(
    EARLY_OUTPUT
)