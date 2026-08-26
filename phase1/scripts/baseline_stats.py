import numpy as np

files = [
    "/home/yuxsun/phase1/data/evpn_rtt_baseline.txt",
    "/home/yuxsun/phase1/data/evpn_rtt_baseline_run2.txt",
    "/home/yuxsun/phase1/data/evpn_rtt_baseline_run3.txt"
]

all_data = []

for i, file in enumerate(files, start=1):
    x = np.loadtxt(file)
    all_data.append(x)

    print(f"\nBaseline Run {i}")
    print("samples =", len(x))
    print("mean =", x.mean(), "ms")
    print("std =", x.std(), "ms")
    print("p95 =", np.percentile(x, 95), "ms")
    print("p99 =", np.percentile(x, 99), "ms")
    print("max =", x.max(), "ms")
    print("mean + 3std =", x.mean() + 3 * x.std(), "ms")

combined = np.concatenate(all_data)

print("\nCombined Baseline")
print("samples =", len(combined))
print("mean =", combined.mean(), "ms")
print("std =", combined.std(), "ms")
print("p95 =", np.percentile(combined, 95), "ms")
print("p99 =", np.percentile(combined, 99), "ms")
print("max =", combined.max(), "ms")
print("mean + 3std =", combined.mean() + 3 * combined.std(), "ms")