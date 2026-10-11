import pandas as pd
import numpy as np

from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
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
    "final_prediction_dataset.csv"
)

OUTPUT_GENERAL = (
    "/home/yuxsun/phase2/data/"
    "final_general_cv_results.csv"
)

OUTPUT_EARLY = (
    "/home/yuxsun/phase2/data/"
    "final_early_warning_cv_results.csv"
)

OUTPUT_EARLY_OOF = (
    "/home/yuxsun/phase2/data/"
    "final_early_warning_oof_predictions.csv"
)

OUTPUT_SUMMARY = (
    "/home/yuxsun/phase2/data/"
    "final_model_summary.csv"
)

N_SPLITS = 5
RANDOM_STATE = 42


# ==========================================
# Load dataset
# ==========================================

df = pd.read_csv(
    DATA_FILE
)

print()
print(
    "=== Final Model Evaluation ==="
)
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
    "Positive labels =",
    int(df["label"].sum())
)

print(
    "Positive ratio =",
    f"{df['label'].mean():.2%}"
)

print()


# ==========================================
# Feature sets
# ==========================================

ALL_FEATURES = [
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


NO_CURRENT_HIGH_FEATURES = [
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
    "overlimits_rate_slope"
]


QUEUE_TRAFFIC_FEATURES = [
    "bottleneck_mbit",
    "requested_flows_mean",
    "active_flows_mean",

    "mean_overlimits_rate",
    "max_overlimits_rate",
    "std_overlimits_rate",
    "overlimits_rate_slope"
]


FEATURE_SETS = {
    "All Features":
        ALL_FEATURES,

    "No Current High Ratio":
        NO_CURRENT_HIGH_FEATURES,

    "Queue + Traffic Only":
        QUEUE_TRAFFIC_FEATURES
}


TARGET = "label"
GROUP = "run"


# ==========================================
# Helpers
# ==========================================

def safe_roc_auc(
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
        "accuracy":
            accuracy_score(
                y_true,
                y_pred
            ),

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
            safe_roc_auc(
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
# Grouped CV
# ==========================================

gkf = GroupKFold(
    n_splits=N_SPLITS
)

general_results = []
early_results = []
early_oof_predictions = []


fold = 1


for train_index, test_index in gkf.split(
    df,
    df[TARGET],
    groups=df[GROUP]
):

    train_df = (
        df.iloc[
            train_index
        ].copy()
    )

    test_df = (
        df.iloc[
            test_index
        ].copy()
    )

    print()
    print("=" * 70)
    print(
        f"Fold {fold}"
    )
    print("=" * 70)
    print()

    print(
        "Train runs =",
        train_df["run"].nunique()
    )

    print(
        "Test runs =",
        test_df["run"].nunique()
    )

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

    print()


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
        test_df[TARGET],
        persistence_pred,
        persistence_prob
    )

    metrics.update({
        "fold":
            fold,

        "feature_set":
            "Baseline",

        "model":
            "Persistence"
    })

    general_results.append(
        metrics
    )


    # ======================================
    # Feature-set experiments
    # ======================================

    for feature_set_name, features in FEATURE_SETS.items():

        X_train = (
            train_df[
                features
            ]
        )

        y_train = (
            train_df[
                TARGET
            ]
        )

        X_test = (
            test_df[
                features
            ]
        )

        y_test = (
            test_df[
                TARGET
            ]
        )


        # ==================================
        # Logistic Regression
        # ==================================

        scaler = (
            StandardScaler()
        )

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

        logistic = (
            LogisticRegression(
                max_iter=3000,
                class_weight="balanced",
                random_state=RANDOM_STATE
            )
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

            "feature_set":
                feature_set_name,

            "model":
                "Logistic Regression"
        })

        general_results.append(
            metrics
        )


        # ==================================
        # Random Forest
        # ==================================

        rf = (
            RandomForestClassifier(
                n_estimators=400,
                max_depth=8,
                min_samples_leaf=3,
                class_weight="balanced",
                random_state=RANDOM_STATE
            )
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

            "feature_set":
                feature_set_name,

            "model":
                "Random Forest"
        })

        general_results.append(
            metrics
        )


        # ==================================
        # Early-warning subset
        # ==================================

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


        if len(
            early_test
        ) == 0:

            continue


        X_early = (
            early_test[
                features
            ]
        )

        y_early = (
            early_test[
                TARGET
            ]
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

            "feature_set":
                feature_set_name,

            "model":
                "Logistic Regression",

            "early_samples":
                len(early_test),

            "early_positive_samples":
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

        oof_part = pd.DataFrame({
            "fold":
                fold,

            "run":
                early_test[
                    "run"
                ].to_numpy(),

            "source_index":
                early_test.index.to_numpy(),

            "feature_set":
                feature_set_name,

            "model":
                "Random Forest",

            "y_true":
                y_early.to_numpy(),

            "y_pred":
                early_rf_pred,

            "y_prob":
                early_rf_prob
        })

        early_oof_predictions.append(
            oof_part
        )

        metrics = calculate_metrics(
            y_early,
            early_rf_pred,
            early_rf_prob
        )

        metrics.update({
            "fold":
                fold,

            "feature_set":
                feature_set_name,

            "model":
                "Random Forest",

            "early_samples":
                len(early_test),

            "early_positive_samples":
                int(
                    y_early.sum()
                )
        })

        early_results.append(
            metrics
        )


    # ======================================
    # Early Persistence Baseline
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

    if len(
        early_test
    ) > 0:

        y_early = (
            early_test[
                TARGET
            ]
        )

        persistence_early_pred = (
            np.zeros(
                len(
                    early_test
                ),
                dtype=int
            )
        )

        persistence_early_prob = (
            np.zeros(
                len(
                    early_test
                )
            )
        )

        metrics = calculate_metrics(
            y_early,
            persistence_early_pred,
            persistence_early_prob
        )

        metrics.update({
            "fold":
                fold,

            "feature_set":
                "Baseline",

            "model":
                "Persistence",

            "early_samples":
                len(
                    early_test
                ),

            "early_positive_samples":
                int(
                    y_early.sum()
                )
        })

        early_results.append(
            metrics
        )


    print(
        "Early-warning samples =",
        len(
            early_test
        )
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
            len(
                early_test
            )
            -
            early_test[
                TARGET
            ].sum()
        )
    )


    fold += 1


# ==========================================
# DataFrames
# ==========================================

general_df = pd.DataFrame(
    general_results
)

early_df = pd.DataFrame(
    early_results
)


if early_oof_predictions:
    early_oof_df = pd.concat(
        early_oof_predictions,
        ignore_index=True
    )
else:
    early_oof_df = pd.DataFrame(
        columns=[
            "fold",
            "run",
            "source_index",
            "feature_set",
            "model",
            "y_true",
            "y_pred",
            "y_prob"
        ]
    )


# ==========================================
# Print General Summary
# ==========================================

print()
print()
print(
    "========================================"
)
print(
    "=== FINAL GENERAL PREDICTION SUMMARY ==="
)
print(
    "========================================"
)
print()


general_summary = (
    general_df
    .groupby(
        [
            "feature_set",
            "model"
        ]
    )[
        [
            "accuracy",
            "precision",
            "recall",
            "f1",
            "roc_auc",
            "pr_auc"
        ]
    ]
    .agg(
        [
            "mean",
            "std"
        ]
    )
)


print(
    general_summary
    .to_string()
)


# ==========================================
# Print Early-warning Summary
# ==========================================

print()
print()
print(
    "========================================"
)
print(
    "=== FINAL EARLY-WARNING SUMMARY ==="
)
print(
    "========================================"
)
print()


early_summary = (
    early_df
    .groupby(
        [
            "feature_set",
            "model"
        ]
    )[
        [
            "accuracy",
            "precision",
            "recall",
            "f1",
            "roc_auc",
            "pr_auc"
        ]
    ]
    .agg(
        [
            "mean",
            "std"
        ]
    )
)


print(
    early_summary
    .to_string()
)


# ==========================================
# Early positive samples per fold
# ==========================================

print()
print(
    "=== Early-warning Samples per Fold ==="
)
print()


early_sample_summary = (
    early_df[
        early_df[
            "model"
        ]
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
)


print(
    early_sample_summary
    .to_string()
)


# ==========================================
# Save raw results
# ==========================================

general_df.to_csv(
    OUTPUT_GENERAL,
    index=False
)

early_df.to_csv(
    OUTPUT_EARLY,
    index=False
)


early_oof_df.to_csv(
    OUTPUT_EARLY_OOF,
    index=False
)


# ==========================================
# Build compact summary CSV
# ==========================================

summary_rows = []


for (
    feature_set,
    model
), subset in general_df.groupby(
    [
        "feature_set",
        "model"
    ]
):

    for metric in [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "pr_auc"
    ]:

        summary_rows.append({
            "task":
                "general",

            "feature_set":
                feature_set,

            "model":
                model,

            "metric":
                metric,

            "mean":
                subset[
                    metric
                ].mean(),

            "std":
                subset[
                    metric
                ].std(
                    ddof=1
                )
        })


for (
    feature_set,
    model
), subset in early_df.groupby(
    [
        "feature_set",
        "model"
    ]
):

    for metric in [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "pr_auc"
    ]:

        summary_rows.append({
            "task":
                "early_warning",

            "feature_set":
                feature_set,

            "model":
                model,

            "metric":
                metric,

            "mean":
                subset[
                    metric
                ].mean(),

            "std":
                subset[
                    metric
                ].std(
                    ddof=1
                )
        })


summary_df = pd.DataFrame(
    summary_rows
)

summary_df.to_csv(
    OUTPUT_SUMMARY,
    index=False
)


# ==========================================
# Finish
# ==========================================

print()
print(
    "Saved general results to:"
)
print(
    OUTPUT_GENERAL
)

print()
print(
    "Saved early-warning results to:"
)
print(
    OUTPUT_EARLY
)

print()
print(
    "Saved early-warning OOF predictions to:"
)
print(
    OUTPUT_EARLY_OOF
)

print()
print(
    "OOF prediction rows =",
    len(
        early_oof_df
    )
)

print()
print(
    "Saved final summary to:"
)
print(
    OUTPUT_SUMMARY
)

print()
print(
    "=== Final model evaluation finished ==="
)