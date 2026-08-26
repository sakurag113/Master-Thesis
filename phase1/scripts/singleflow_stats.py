import numpy as np

x = np.loadtxt('/home/yuxsun/phase1/data/evpn_rtt_singleflow_run1.txt')

threshold = 0.1293  # combined baseline p99，暂时作为候选阈值

print("samples =", len(x))
print("mean =", x.mean(), "ms")
print("std =", x.std(), "ms")
print("p95 =", np.percentile(x, 95), "ms")
print("p99 =", np.percentile(x, 99), "ms")
print("max =", x.max(), "ms")

above = x > threshold
print("samples above baseline p99 =", above.sum())
print("ratio above baseline p99 =", above.mean())