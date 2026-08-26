import pandas as pd
import numpy as np

single_file = "/home/yuxsun/phase1/data/evpn_sync_singleflow.csv"
dual_file = "/home/yuxsun/phase1/data/evpn_sync_dualflow.csv"

baseline_p99 = 0.1293  # 之前 combined baseline 的 p99


def analyze(file, name):
    df = pd.read_csv(file)

    df["delta_overlimits"] = (
        df["overlimits"]
        .diff()
        .fillna(0)
    )

    df.loc[df["delta_overlimits"] < 0, "delta_overlimits"] = 0

    rtt = df["rtt_ms"].dropna()
    delta = df["delta_overlimits"].dropna()

    result = {
        "condition": name,
        "samples": len(rtt),
        "mean_rtt_ms": rtt.mean(),
        "p95_rtt_ms": np.percentile(rtt, 95),
        "p99_rtt_ms": np.percentile(rtt, 99),
        "max_rtt_ms": rtt.max(),
        "above_baseline_p99_count": (rtt > baseline_p99).sum(),
        "above_baseline_p99_ratio": (rtt > baseline_p99).mean(),
        "mean_delta_overlimits": delta.mean(),
        "max_delta_overlimits": delta.max()
    }

    return result


single = analyze(single_file, "Single-flow")
dual = analyze(dual_file, "Dual-flow")

results = pd.DataFrame([single, dual])

print("\n=== Single-flow vs Dual-flow Comparison ===\n")

print(results.to_string(index=False))

output = "/home/yuxsun/phase1/data/single_dual_comparison.csv"

results.to_csv(output, index=False)

print("\nSaved to:")
print(output)