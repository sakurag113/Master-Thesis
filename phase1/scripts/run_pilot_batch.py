import subprocess
import time

EXPERIMENT_SCRIPT = (
    "/home/yuxsun/phase2/scripts/"
    "run_phase2_experiment.py"
)

experiments = [
    # 5 Mbit/s
    ("pilot_5m_run1", 5, 501),
    ("pilot_5m_run2", 5, 502),
    ("pilot_5m_run3", 5, 503),
    ("pilot_5m_run4", 5, 504),

    # 10 Mbit/s
    ("pilot_10m_run1", 10, 1001),
    ("pilot_10m_run2", 10, 1002),
    ("pilot_10m_run3", 10, 1003),
    ("pilot_10m_run4", 10, 1004),

    # 20 Mbit/s
    ("pilot_20m_run1", 20, 2001),
    ("pilot_20m_run2", 20, 2002),
    ("pilot_20m_run3", 20, 2003),
    ("pilot_20m_run4", 20, 2004),
]

for index, (run_name, rate, seed) in enumerate(
    experiments,
    start=1
):

    print()
    print("=" * 60)

    print(
        f"Experiment {index}/{len(experiments)}"
    )

    print(
        f"Run: {run_name}"
    )

    print(
        f"Bottleneck: {rate} Mbit/s"
    )

    print(
        f"Seed: {seed}"
    )

    print("=" * 60)
    print()

    cmd = [
        "python3",
        EXPERIMENT_SCRIPT,

        "--run-name",
        run_name,

        "--rate",
        str(rate),

        "--duration",
        "90",

        "--seed",
        str(seed)
    ]

    result = subprocess.run(cmd)

    if result.returncode != 0:

        print()
        print(
            f"ERROR: {run_name} failed."
        )

        print(
            "Batch stopped."
        )

        break

    print()
    print(
        f"{run_name} finished."
    )

    # Small cooldown between runs
    time.sleep(5)

else:

    print()
    print(
        "=== All pilot experiments finished ==="
    )