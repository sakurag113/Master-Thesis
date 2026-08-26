import os
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier


# ==========================================
# Paths
# ==========================================

DATA_FILE = (
    "/home/yuxsun/phase2/data/"
    "final_prediction_dataset.csv"
)

MODEL_DIR = (
    "/home/yuxsun/phase3/models"
)

MODEL_FILE = (
    "/home/yuxsun/phase3/models/"
    "online_rf_queue_traffic.joblib"
)

FEATURE_FILE = (
    "/home/yuxsun/phase3/models/"
    "online_feature_list.txt"
)


# ==========================================
# Feature set
# ==========================================

FEATURES = [
    "bottleneck_mbit",
    "requested_flows_mean",
    "active_flows_mean",

    "mean_overlimits_rate",
    "max_overlimits_rate",
    "std_overlimits_rate",
    "overlimits_rate_slope"
]

TARGET = "label"


# ==========================================
# Create model directory
# ==========================================

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


# ==========================================
# Load Phase 2 final dataset
# ==========================================

df = pd.read_csv(
    DATA_FILE
)

print()
print("=== Phase 3 Online Model Training ===")
print()

print(
    "Dataset samples =",
    len(df)
)

print(
    "Positive samples =",
    int(df[TARGET].sum())
)

print(
    "Negative samples =",
    int(
        len(df)
        - df[TARGET].sum()
    )
)


# ==========================================
# Prepare training data
# ==========================================

X = df[
    FEATURES
]

y = df[
    TARGET
]


# ==========================================
# Train final Random Forest
# ==========================================

model = RandomForestClassifier(
    n_estimators=400,
    max_depth=8,
    min_samples_leaf=3,
    class_weight="balanced",
    random_state=42
)

model.fit(
    X,
    y
)


# ==========================================
# Save model
# ==========================================

joblib.dump(
    model,
    MODEL_FILE
)


# ==========================================
# Save feature list
# ==========================================

with open(
    FEATURE_FILE,
    "w"
) as f:

    for feature in FEATURES:
        f.write(
            feature + "\n"
        )


# ==========================================
# Feature importance
# ==========================================

importance_df = pd.DataFrame({
    "feature":
        FEATURES,

    "importance":
        model.feature_importances_
})

importance_df = (
    importance_df.sort_values(
        "importance",
        ascending=False
    )
)

print()
print(
    "=== Feature Importance ==="
)
print()

print(
    importance_df.to_string(
        index=False
    )
)


print()
print(
    "Model saved to:"
)

print(
    MODEL_FILE
)

print()
print(
    "Feature list saved to:"
)

print(
    FEATURE_FILE
)