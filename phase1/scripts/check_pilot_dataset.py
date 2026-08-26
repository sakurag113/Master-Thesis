import os
import glob
import pandas as pd


# ==========================================
# Configuration
# ==========================================

DATA_DIR = "/home/yuxsun/phase2/data"

REQUIRED_COLUMNS = [
    "timestamp",
    "time_s",
    "rtt_ms",
    "overlimits",
    "requested_flows",
    "active_flows",
    "bottleneck_mbit"
]


# ==========================================
# Find experiment CSV files
# ==========================================

all_csv_files = sorted(
    glob.glob(
        os.path.join(
            DATA_DIR,
            "pilot_*m_run*.csv"
        )
    )
)

# Exclude metadata files
files = [
    file
    for file in all_csv_files
    if not file.endswith("_metadata.csv")
]


# ==========================================
# Start quality check
# ==========================================

print()
print("=== Phase 2 Pilot Dataset Quality Check ===")
print()

print(
    "Experiment CSV files found =",
    len(files)
)

print()


results = []


# ==========================================
# Analyze every run
# ==========================================

for file in files:

    name = os.path.basename(file)

    print(
        "Checking:",
        name
    )

    try:

        df = pd.read_csv(file)

    except Exception as e:

        print(
            "  ERROR: cannot read CSV"
        )

        print(
            " ",
            e
        )

        continue


    # --------------------------------------
    # Check required columns
    # --------------------------------------

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:

        print(
            "  ERROR: missing columns:",
            missing_columns
        )

        continue


    # --------------------------------------
    # Basic sample information
    # --------------------------------------

    total_samples = len(df)

    if total_samples == 0:

        print(
            "  ERROR: empty file"
        )

        continue


    duration = (
        df["time_s"].max()
        - df["time_s"].min()
    )


    # --------------------------------------
    # Missing RTT
    # --------------------------------------

    missing_rtt = (
        df["rtt_ms"]
        .isna()
        .sum()
    )


    # --------------------------------------
    # Requested vs actual flows
    # --------------------------------------

    flow_mismatch_samples = (
        df["requested_flows"]
        != df["active_flows"]
    ).sum()


    # More serious case:
    # traffic requested but no active flow

    failed_flow_samples = (
        (
            df["requested_flows"] > 0
        )
        &
        (
            df["active_flows"] == 0
        )
    ).sum()


    # --------------------------------------
    # Flow states
    # --------------------------------------

    requested_states = sorted(
        df["requested_flows"]
        .dropna()
        .unique()
        .tolist()
    )

    active_states = sorted(
        df["active_flows"]
        .dropna()
        .unique()
        .tolist()
    )


    # --------------------------------------
    # Bottleneck rate
    # --------------------------------------

    bottleneck_rates = sorted(
        df["bottleneck_mbit"]
        .dropna()
        .unique()
        .tolist()
    )


    # --------------------------------------
    # Overlimits counter
    # --------------------------------------

    overlimits_diff = (
        df["overlimits"]
        .diff()
    )

    counter_decreases = (
        overlimits_diff < 0
    ).sum()


    # --------------------------------------
    # RTT statistics
    # --------------------------------------

    valid_rtt = (
        df["rtt_ms"]
        .dropna()
    )

    if len(valid_rtt) > 0:

        mean_rtt = (
            valid_rtt.mean()
        )

        max_rtt = (
            valid_rtt.max()
        )

    else:

        mean_rtt = None
        max_rtt = None


    # --------------------------------------
    # Quality status
    # --------------------------------------

    problems = []

    if missing_rtt > 0:

        problems.append(
            "missing RTT"
        )

    if flow_mismatch_samples > 0:

        problems.append(
            "flow mismatch"
        )

    if failed_flow_samples > 0:

        problems.append(
            "failed flows"
        )

    if counter_decreases > 0:

        problems.append(
            "overlimits reset/decrease"
        )

    if len(bottleneck_rates) != 1:

        problems.append(
            "invalid bottleneck rate"
        )


    if len(problems) == 0:

        status = "PASS"

    else:

        status = (
            "CHECK: "
            + ", ".join(problems)
        )


    # --------------------------------------
    # Save result
    # --------------------------------------

    results.append({
        "file":
            name,

        "samples":
            total_samples,

        "duration_s":
            duration,

        "missing_rtt":
            missing_rtt,

        "flow_mismatch_samples":
            flow_mismatch_samples,

        "failed_flow_samples":
            failed_flow_samples,

        "counter_decreases":
            counter_decreases,

        "requested_flow_states":
            str(requested_states),

        "active_flow_states":
            str(active_states),

        "bottleneck_rates":
            str(bottleneck_rates),

        "mean_rtt_ms":
            mean_rtt,

        "max_rtt_ms":
            max_rtt,

        "status":
            status
    })


# ==========================================
# Build result table
# ==========================================

result_df = pd.DataFrame(
    results
)


print()
print(
    "=== Per-run Results ==="
)
print()


if len(result_df) > 0:

    print(
        result_df.to_string(
            index=False
        )
    )

else:

    print(
        "No valid experiment files found."
    )


# ==========================================
# Overall summary
# ==========================================

print()
print(
    "=== Overall Summary ==="
)
print()


if len(result_df) > 0:

    print(
        "Number of valid runs =",
        len(result_df)
    )

    print(
        "Total samples =",
        result_df[
            "samples"
        ].sum()
    )

    print(
        "Total missing RTT samples =",
        result_df[
            "missing_rtt"
        ].sum()
    )

    print(
        "Total requested/active "
        "mismatch samples =",
        result_df[
            "flow_mismatch_samples"
        ].sum()
    )

    print(
        "Total failed-flow samples =",
        result_df[
            "failed_flow_samples"
        ].sum()
    )

    print(
        "Total overlimits "
        "counter decreases =",
        result_df[
            "counter_decreases"
        ].sum()
    )

    passed = (
        result_df[
            "status"
        ] == "PASS"
    ).sum()

    print(
        "Runs passed =",
        passed,
        "/",
        len(result_df)
    )


# ==========================================
# Save quality report
# ==========================================

output = (
    "/home/yuxsun/phase2/data/"
    "pilot_dataset_quality.csv"
)

result_df.to_csv(
    output,
    index=False
)

print()
print(
    "Quality report saved to:"
)

print(
    output
)