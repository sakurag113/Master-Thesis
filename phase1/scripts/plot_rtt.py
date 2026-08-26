import matplotlib.pyplot as plt

def load_csv(path):
    x = []
    y = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            a, b = line.split(",")
            x.append(int(a))
            y.append(float(b))
    return x, y

xb, yb = load_csv("/home/yuxsun/phase1/data/ping_rtt_baseline.csv")
xs, ys = load_csv("/home/yuxsun/phase1/data/ping_rtt_singleflow.csv")
x1, y1 = load_csv("/home/yuxsun/phase1/data/ping_rtt_run1.csv")
x2, y2 = load_csv("/home/yuxsun/phase1/data/ping_rtt_run2.csv")
x3, y3 = load_csv("/home/yuxsun/phase1/data/ping_rtt_run3.csv")

plt.figure(figsize=(10, 6))
plt.plot(xb, yb, label="Baseline")
plt.plot(xs, ys, label="Singleflow")
plt.plot(x1, y1, label="Run 1")
plt.plot(x2, y2, label="Run 2")
plt.plot(x3, y3, label="Run 3")

plt.xlabel("Sample Index")
plt.ylabel("RTT (ms)")
plt.title("RTT Comparison: Baseline, Single-flow and  Contention Runs")
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig("/home/yuxsun/phase1/plots/rtt_comparison.png", dpi=200)
plt.show()
