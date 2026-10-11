#!/usr/bin/env python3

import subprocess
import sys
import time
from pathlib import Path


PHASE3_DIR = Path.home() / "phase3"

MEASURED_RUN_SCRIPT = (
    PHASE3_DIR
    / "scripts"
    / "run_phase3_measured.py"
)


def main():

    if len(sys.argv) != 2:
        print(
            "Usage: python3 run_phase3_batch.py "
            "<number_of_runs>"
        )
        sys.exit(1)

    try:
        number_of_runs = int(sys.argv[1])
    except ValueError:
        print("number_of_runs must be an integer")
        sys.exit(1)

    if number_of_runs <= 0:
        print("number_of_runs must be > 0")
        sys.exit(1)

    print()
    print("==========================================")
    print(" Phase 3 Batch Experiment")
    print("==========================================")
    print(f"Number of runs: {number_of_runs}")
    print()

    subprocess.run(
        ["sudo", "-v"],
        check=True,
    )

    successful_runs = 0
    failed_runs = 0

    for i in range(1, number_of_runs + 1):

        run_name = f"phase3_batch_run{i:02d}"

        print()
        print("==========================================")
        print(
            f" Starting {run_name} "
            f"({i}/{number_of_runs})"
        )
        print("==========================================")
        print()

        result = subprocess.run(
            [
                "python3",
                str(MEASURED_RUN_SCRIPT),
                run_name,
            ]
        )

        if result.returncode == 0:
            successful_runs += 1
            print()
            print(f"{run_name}: SUCCESS")
        else:
            failed_runs += 1
            print()
            print(f"{run_name}: FAILED")

        if i < number_of_runs:

            print()
            print(
                "Waiting 5 seconds before next run..."
            )

            time.sleep(5)

    print()
    print("==========================================")
    print(" Batch finished")
    print("==========================================")
    print(f"Successful runs: {successful_runs}")
    print(f"Failed runs    : {failed_runs}")
    print()


if __name__ == "__main__":
    main()