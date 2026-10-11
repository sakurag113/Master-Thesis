#!/usr/bin/env python3

import pandas as pd
import numpy as np
from pathlib import Path


LOG_FILE = (
    Path.home()
    / "phase3"
    / "logs"
    / "flow_comparison_log.csv"
)

OUTPUT_FILE = (
    Path.home()
    / "phase3"
    / "data"
    / "risk_recovery_summary.csv"
)


WARNING_THRESHOLD = 0.50
BASELINE_RISK = 0.15


def main():

    df = pd.read_csv(LOG_FILE)

    df = df.sort_values(
        "time_s"
    ).reset_index(drop=True)

    # Only rows with actual predictions
    pred = df.dropna(
        subset=[
            "future_high_probability"
        ]
    ).copy()

    # --------------------------------------------------------
    # Detect transitions:
    # active flow > 0  -->  active flow = 0
    # --------------------------------------------------------

    transitions = []

    previous_flow = None

    for i, row in df.iterrows():

        current_flow = int(
            row["active_flows"]
        )

        if (
            previous_flow is not None
            and
            previous_flow > 0
            and
            current_flow == 0
        ):

            transitions.append({
                "index": i,
                "stop_time":
                    row["time_s"],
                "previous_flows":
                    previous_flow,
            })

        previous_flow = current_flow


    results = []

    for number, transition in enumerate(
        transitions,
        start=1,
    ):

        stop_time = transition[
            "stop_time"
        ]

        previous_flows = transition[
            "previous_flows"
        ]

        # Predictions immediately before stop
        before = pred[
            pred["time_s"] < stop_time
        ]

        if before.empty:
            continue

        risk_before_stop = (
            before.iloc[-1]
            ["future_high_probability"]
        )

        # Predictions after stop
        after = pred[
            pred["time_s"] >= stop_time
        ].copy()

        # Only consider recovery period until traffic restarts
        restart_rows = df[
            (df["time_s"] > stop_time)
            &
            (df["active_flows"] > 0)
        ]

        if not restart_rows.empty:

            restart_time = (
                restart_rows.iloc[0]
                ["time_s"]
            )

            after = after[
                after["time_s"]
                <
                restart_time
            ]

        else:

            restart_time = np.nan


        first_after_risk = np.nan

        if not after.empty:

            first_after_risk = (
                after.iloc[0]
                ["future_high_probability"]
            )


        # ----------------------------------------------------
        # Time until risk falls below warning threshold
        # ----------------------------------------------------

        below_warning = after[
            after[
                "future_high_probability"
            ]
            <
            WARNING_THRESHOLD
        ]

        if not below_warning.empty:

            below_warning_time = (
                below_warning.iloc[0]
                ["time_s"]
            )

            time_to_below_warning = (
                below_warning_time
                -
                stop_time
            )

        else:

            below_warning_time = np.nan
            time_to_below_warning = np.nan


        # ----------------------------------------------------
        # Time until approximately baseline
        # ----------------------------------------------------

        baseline_rows = after[
            after[
                "future_high_probability"
            ]
            <=
            BASELINE_RISK
        ]

        if not baseline_rows.empty:

            baseline_time = (
                baseline_rows.iloc[0]
                ["time_s"]
            )

            time_to_baseline = (
                baseline_time
                -
                stop_time
            )

        else:

            baseline_time = np.nan
            time_to_baseline = np.nan


        results.append({

            "transition":
                number,

            "flows_before_stop":
                previous_flows,

            "stop_time_s":
                stop_time,

            "risk_before_stop":
                risk_before_stop,

            "first_risk_after_stop":
                first_after_risk,

            "time_to_below_0.5_s":
                time_to_below_warning,

            "time_to_baseline_s":
                time_to_baseline,

            "restart_time_s":
                restart_time,
        })


    result = pd.DataFrame(
        results
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
    )


    print()
    print(
        "=============================================="
    )

    print(
        " Phase 3 Risk Recovery Analysis"
    )

    print(
        "=============================================="
    )

    print()

    print(
        result.to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}",
        )
    )


    print()

    if not result.empty:

        print(
            "Average time below warning threshold:"
        )

        print(
            f"{result['time_to_below_0.5_s'].mean():.3f} s"
        )

        print()

        print(
            "Average time back to baseline:"
        )

        print(
            f"{result['time_to_baseline_s'].mean():.3f} s"
        )


    print()

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()