import matplotlib.pyplot as plt

with open("/home/yuxsun/phase1/data/overlimits_before.txt", "r") as f:
    before = int(f.read().strip())

with open("/home/yuxsun/phase1/data/overlimits_after.txt", "r") as f:
    after = int(f.read().strip())

labels = ["Before", "After"]
values = [before, after]

plt.figure(figsize=(6, 5))
plt.bar(labels, values)
plt.ylabel("Overlimits")
plt.title("Queue Signal Comparison (TBF overlimits)")
plt.grid(True, axis="y")

plt.tight_layout()
plt.savefig("/home/yuxsun/phase1/plots/queue_signal_overlimits.png", dpi=200)
plt.show()
