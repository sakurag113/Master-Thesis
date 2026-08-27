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
# Find formal experiment CSV files
# ==========================================

all_files = sorted(
    glob.glob(
        os.path.join(
            DATA_DIR,
            "formal_*m_run*.csv"
        )
    )
)

files = [
    f
    for f in all_files
    if not f.endswith("_metadata.csv")
]


print()
print("=== Phase 2 Formal Dataset Quality Check ===")
print()

print("Formal run files found =", len(files))
print()


# ==========================================
# Check each run
# ==========================================

results = []

for file in files:

    name = os.path.basename(file)

    print("Checking:", name)

    try:
        df = pd.read_csv(file)

    except Exception as e:

        print("  ERROR: cannot read file")
        print(" ", e)
        continue


    # --------------------------------------
    # Column check
    # --------------------------------------

    missing_columns = [
        c
        for c in REQUIRED_COLUMNS
        if c not in df.columns
    ]

    if missing_columns:

        print(
            "  ERROR: missing columns:",
            missing_columns
        )

        continue


    if len(df) == 0:

        print("  ERROR: empty file")
        continue


    # --------------------------------------
    # Basic information
    # --------------------------------------

    samples = len(df)

    duration_s = (
        df["time_s"].max()
        - df["time_s"].min()
    )


    # --------------------------------------
    # Missing values
    # --------------------------------------

    missing_rtt = (
        df["rtt_ms"]
        .isna()
        .sum()
    )

    missing_overlimits = (
        df["overlimits"]
        .isna()
        .sum()
    )


    # --------------------------------------
    # Requested / active flows
    # --------------------------------------

    mismatch_samples = (
        df["requested_flows"]
        != df["active_flows"]
    ).sum()

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
    # Overlimits monotonicity
    # --------------------------------------

    counter_decreases = (
        df["overlimits"]
        .diff()
        .lt(0)
        .sum()
    )


    # --------------------------------------
    # Bottleneck rate
    # --------------------------------------

    rates = sorted(
        df["bottleneck_mbit"]
        .dropna()
        .unique()
        .tolist()
    )


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
    # RTT statistics
    # --------------------------------------

    valid_rtt = df["rtt_ms"].dropna()

    mean_rtt = (
        valid_rtt.mean()
        if len(valid_rtt) > 0
        else None
    )

    max_rtt = (
        valid_rtt.max()
        if len(valid_rtt) > 0
        else None
    )


    # --------------------------------------
    # Status
    # --------------------------------------

    problems = []

    if missing_rtt > 0:
        problems.append("missing RTT")

    if missing_overlimits > 0:
        problems.append("missing overlimits")

    if mismatch_samples > 0:
        problems.append("flow mismatch")

    if failed_flow_samples > 0:
        problems.append("failed flow")

    if counter_decreases > 0:
        problems.append("counter decrease")

    if len(rates) != 1:
        problems.append("invalid bottleneck rate")


    if len(problems) == 0:
        status = "PASS"
    else:
        status = (
            "CHECK: "
            + ", ".join(problems)
        )


    results.append({
        "file":
            name,

        "samples":
            samples,

        "duration_s":
            duration_s,

        "missing_rtt":
            missing_rtt,

        "missing_overlimits":
            missing_overlimits,

        "flow_mismatch_samples":
            mismatch_samples,

        "failed_flow_samples":
            failed_flow_samples,

        "counter_decreases":
            counter_decreases,

        "requested_flow_states":
            str(requested_states),

        "active_flow_states":
            str(active_states),

        "bottleneck_rates":
            str(rates),

        "mean_rtt_ms":
            mean_rtt,

        "max_rtt_ms":
            max_rtt,

        "status":
            status
    })


# ==========================================
# Results
# ==========================================

result_df = pd.DataFrame(results)


print()
print("=== Per-run Results ===")
print()

if len(result_df) > 0:

    print(
        result_df.to_string(
            index=False
        )
    )

else:

    print("No valid formal files found.")


# ==========================================
# Overall summary
# ==========================================

print()
print("=== Overall Summary ===")
print()

if len(result_df) > 0:

    print(
        "Valid formal runs =",
        len(result_df)
    )

    print(
        "Total samples =",
        result_df["samples"].sum()
    )

    print(
        "Total missing RTT =",
        result_df["missing_rtt"].sum()
    )

    print(
        "Total missing overlimits =",
        result_df["missing_overlimits"].sum()
    )

    print(
        "Total flow mismatch samples =",
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
        "Total counter decreases =",
        result_df[
            "counter_decreases"
        ].sum()
    )

    passed = (
        result_df["status"] == "PASS"
    ).sum()

    print(
        "Runs passed =",
        passed,
        "/",
        len(result_df)
    )


# ==========================================
# Per-rate summary
# ==========================================

if len(result_df) > 0:

    print()
    print("=== Bottleneck Summary ===")
    print()

    for rate in [5, 10, 20]:

        subset = result_df[
            result_df[
                "bottleneck_rates"
            ] == f"[{rate}]"
        ]

        print(
            f"{rate} Mbit/s:",
            len(subset),
            "runs"
        )


# ==========================================
# Save
# ==========================================

output = (
    "/home/yuxsun/phase2/data/"
    "formal_dataset_quality.csv"
)

result_df.to_csv(
    output,
    index=False
)

print()
print("Saved to:")
print(output)