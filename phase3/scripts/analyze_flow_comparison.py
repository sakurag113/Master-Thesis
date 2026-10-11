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
    / "flow_comparison_summary.csv"
)


def main():

    df = pd.read_csv(LOG_FILE)

    # Only rows where prediction was actually calculated
    pred_df = df.dropna(
        subset=[
            "future_high_probability",
            "prediction",
        ]
    ).copy()

    rows = []

    scenario_map = {
        0: "Idle / Recovery",
        1: "Single-flow",
        2: "Dual-flow",
    }

    for flows, scenario in scenario_map.items():

        subset = pred_df[
            pred_df["active_flows"] == flows
        ]

        if subset.empty:
            continue

        risk = subset[
            "future_high_probability"
        ]

        rtt = subset[
            "rtt_ms"
        ].dropna()

        queue = subset[
            "mean_overlimits_rate"
        ].dropna()

        warning_ratio = (
            subset["prediction"].mean()
        )

        rows.append({
            "scenario":
                scenario,

            "active_flows":
                flows,

            "n_predictions":
                len(subset),

            "mean_risk":
                risk.mean(),

            "median_risk":
                risk.median(),

            "max_risk":
                risk.max(),

            "std_risk":
                risk.std(),

            "mean_rtt_ms":
                rtt.mean()
                if not rtt.empty
                else np.nan,

            "max_rtt_ms":
                rtt.max()
                if not rtt.empty
                else np.nan,

            "mean_overlimits_rate":
                queue.mean()
                if not queue.empty
                else np.nan,

            "max_overlimits_rate":
                queue.max()
                if not queue.empty
                else np.nan,

            "warning_ratio":
                warning_ratio,
        })


    result = pd.DataFrame(rows)

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
        "============================================"
    )

    print(
        " Phase 3 Flow Comparison Summary"
    )

    print(
        "============================================"
    )

    print()

    print(
        result.to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}",
        )
    )

    print()

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()