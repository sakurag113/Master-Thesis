import subprocess
import time
import os

# ==========================================
# Configuration
# ==========================================

EXPERIMENT_SCRIPT = (
    "/home/yuxsun/phase2/scripts/"
    "run_phase2_experiment_v4.py"
)

DURATION = 120
COOLDOWN = 5

# 16 runs per bottleneck
RATES = [5, 10, 20]

RUNS_PER_RATE = 16


# ==========================================
# Build experiment list
# ==========================================

experiments = []

for rate in RATES:

    for run_idx in range(1, RUNS_PER_RATE + 1):

        run_name = (
            f"formal_{rate}m_run{run_idx}"
        )

        # unique, reproducible seed
        seed = (
            rate * 10000
            + run_idx
        )

        experiments.append(
            (
                run_name,
                rate,
                seed
            )
        )


# ==========================================
# Print plan
# ==========================================

print()
print(
    "=== Phase 2 Formal Batch ==="
)
print()

print(
    "Total runs =",
    len(experiments)
)

print(
    "Duration per run =",
    DURATION,
    "s"
)

print(
    "Cooldown =",
    COOLDOWN,
    "s"
)

print()


# ==========================================
# Run experiments
# ==========================================

completed = 0

for index, (
    run_name,
    rate,
    seed
) in enumerate(
    experiments,
    start=1
):

    print()
    print("=" * 70)

    print(
        f"Experiment "
        f"{index}/{len(experiments)}"
    )

    print(
        "Run:",
        run_name
    )

    print(
        "Bottleneck:",
        rate,
        "Mbit/s"
    )

    print(
        "Seed:",
        seed
    )

    print("=" * 70)
    print()

    cmd = [
        "python3",
        EXPERIMENT_SCRIPT,

        "--run-name",
        run_name,

        "--rate",
        str(rate),

        "--duration",
        str(DURATION),

        "--seed",
        str(seed)
    ]

    result = subprocess.run(
        cmd
    )

    # --------------------------------------
    # Stop batch if one experiment fails
    # --------------------------------------

    if result.returncode != 0:

        print()
        print(
            "ERROR:"
        )

        print(
            run_name,
            "failed."
        )

        print(
            "Batch stopped."
        )

        break


    completed += 1

    print()
    print(
        run_name,
        "finished successfully."
    )

    print(
        f"Completed "
        f"{completed}/"
        f"{len(experiments)}"
    )


    # --------------------------------------
    # Cooldown
    # --------------------------------------

    if index < len(experiments):

        print()
        print(
            f"Cooldown for "
            f"{COOLDOWN} seconds..."
        )

        time.sleep(
            COOLDOWN
        )


# ==========================================
# Final summary
# ==========================================

print()
print(
    "========================================"
)

print(
    "=== Formal Batch Finished ==="
)

print(
    "========================================"
)

print()

print(
    "Completed runs =",
    completed
)

print(
    "Planned runs =",
    len(experiments)
)

if completed == len(experiments):

    print()
    print(
        "All formal experiments "
        "completed successfully."
    )

else:

    print()
    print(
        "Batch did not complete."
    )

    print(
        "Check the last failed run."
    )